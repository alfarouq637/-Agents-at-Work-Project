"""Create or restore encrypted local SQLite snapshots without exposing keys."""

import argparse
import base64
import hashlib
import json
import os
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


FORMAT = "autocorp-encrypted-sqlite-backup-v1"
AAD = FORMAT.encode("ascii")


def decode_backup_key(value: str) -> bytes:
    """Accept a URL-safe base64-encoded, 32-byte AES-256 key."""
    try:
        padded = value.strip() + "=" * (-len(value.strip()) % 4)
        key = base64.urlsafe_b64decode(padded.encode("ascii"))
    except Exception as exc:
        raise ValueError("BACKUP_ENCRYPTION_KEY must be URL-safe base64") from exc
    if len(key) != 32:
        raise ValueError("BACKUP_ENCRYPTION_KEY must decode to exactly 32 bytes")
    return key


def _sqlite_snapshot(source: Path) -> bytes:
    if not source.is_file():
        raise ValueError("The SQLite source database does not exist")
    source_uri = source.resolve().as_uri() + "?mode=ro"
    source_connection = sqlite3.connect(source_uri, uri=True)
    snapshot_connection = sqlite3.connect(":memory:")
    try:
        source_connection.backup(snapshot_connection)
        integrity = snapshot_connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError("The SQLite source database failed integrity_check")
        return snapshot_connection.serialize()
    finally:
        snapshot_connection.close()
        source_connection.close()


def create_encrypted_backup(
    source: Path,
    destination: Path,
    key: bytes,
    *,
    owner: str,
    retention_until: str,
    key_id: str,
) -> dict:
    """Snapshot a SQLite database and save an AES-256-GCM encrypted envelope."""
    if not owner.strip() or not key_id.strip():
        raise ValueError("owner and key_id are required for accountable backup records")
    retention_date = date.fromisoformat(retention_until)
    if retention_date < date.today():
        raise ValueError("retention_until cannot be in the past")
    if destination.exists():
        raise FileExistsError("Refusing to overwrite an existing backup")
    if not destination.parent.is_dir():
        raise ValueError("The backup destination directory must already exist")

    snapshot = _sqlite_snapshot(source)
    nonce = os.urandom(12)
    encrypted = AESGCM(key).encrypt(nonce, snapshot, AAD)
    metadata = {
        "format": FORMAT,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "owner": owner.strip(),
        "retention_until": retention_date.isoformat(),
        "key_id": key_id.strip(),
        "algorithm": "AES-256-GCM",
        "plaintext_sha256": hashlib.sha256(snapshot).hexdigest(),
        "plaintext_bytes": len(snapshot),
        "nonce": base64.urlsafe_b64encode(nonce).decode("ascii"),
        "ciphertext": base64.urlsafe_b64encode(encrypted).decode("ascii"),
    }
    destination.write_text(json.dumps(metadata, sort_keys=True), encoding="utf-8")
    try:
        os.chmod(destination, 0o600)
    except OSError:
        pass
    return {key: metadata[key] for key in metadata if key not in {"nonce", "ciphertext"}}


def restore_encrypted_backup(source: Path, destination: Path, key: bytes) -> dict:
    """Restore a verified encrypted envelope without overwriting a database."""
    if destination.exists():
        raise FileExistsError("Refusing to overwrite an existing restore destination")
    try:
        envelope = json.loads(source.read_text(encoding="utf-8"))
        if envelope.get("format") != FORMAT or envelope.get("algorithm") != "AES-256-GCM":
            raise ValueError("Unsupported backup envelope")
        nonce = base64.urlsafe_b64decode(envelope["nonce"].encode("ascii"))
        ciphertext = base64.urlsafe_b64decode(envelope["ciphertext"].encode("ascii"))
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, AAD)
    except (KeyError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("Backup could not be authenticated or decoded") from exc
    if hashlib.sha256(plaintext).hexdigest() != envelope.get("plaintext_sha256"):
        raise ValueError("Backup integrity hash does not match")

    try:
        destination.write_bytes(plaintext)
        connection = sqlite3.connect(destination)
        try:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            connection.close()
        if integrity != "ok":
            raise ValueError("Restored database failed integrity_check")
    except Exception:
        if destination.exists():
            destination.unlink()
        raise
    try:
        os.chmod(destination, 0o600)
    except OSError:
        pass
    return {
        "format": envelope["format"],
        "owner": envelope["owner"],
        "retention_until": envelope["retention_until"],
        "key_id": envelope["key_id"],
        "plaintext_sha256": envelope["plaintext_sha256"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Encrypted local SQLite backup utility")
    actions = parser.add_subparsers(dest="action", required=True)
    backup = actions.add_parser("backup")
    backup.add_argument("source", type=Path)
    backup.add_argument("destination", type=Path)
    backup.add_argument("--owner", required=True)
    backup.add_argument("--retention-until", required=True, metavar="YYYY-MM-DD")
    backup.add_argument("--key-id", required=True, help="Secret-manager/KMS key reference, not key material")
    restore = actions.add_parser("restore")
    restore.add_argument("source", type=Path)
    restore.add_argument("destination", type=Path)
    args = parser.parse_args()

    key = decode_backup_key(os.environ.get("BACKUP_ENCRYPTION_KEY", ""))
    if args.action == "backup":
        result = create_encrypted_backup(
            args.source, args.destination, key, owner=args.owner,
            retention_until=args.retention_until, key_id=args.key_id,
        )
    else:
        result = restore_encrypted_backup(args.source, args.destination, key)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
