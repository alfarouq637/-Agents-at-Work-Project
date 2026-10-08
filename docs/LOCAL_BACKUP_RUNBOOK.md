# Local SQLite Backup Runbook

This runbook applies only to the local SQLite fallback. It does not back up
Turso, Vercel, or a future PostgreSQL deployment.

1. Store a random 32-byte AES key, encoded with URL-safe base64, in the secret
   manager as `BACKUP_ENCRYPTION_KEY`. Store a non-secret key reference such as
   `kms://backup-key-v1` separately from the key material.
2. Export the key only into the operator's process environment. Do not put it
   in a command line, tracked `.env` file, ticket, or chat message.
3. Create a new encrypted backup file. The tool refuses to overwrite one.

```powershell
python scripts/encrypted_sqlite_backup.py backup corp.db backups/corp-2026-10-08.enc.json `
  --owner security-team --retention-until 2027-10-08 --key-id kms://backup-key-v1
```

4. Record the output metadata, access grant, owner, retention date, and backup
   location in the approved operations register. The output deliberately omits
   encryption key material and ciphertext.
5. Test a restore at least quarterly into a new non-production location:

```powershell
python scripts/encrypted_sqlite_backup.py restore backups/corp-2026-10-08.enc.json restored-corp.db
```

The utility takes a consistent SQLite snapshot, checks source and restored
integrity, encrypts using AES-256-GCM, and verifies the plaintext SHA-256 hash
after decryption. It does not replace malware scanning, a managed backup
service, off-site retention, or the planned disaster-recovery program.
