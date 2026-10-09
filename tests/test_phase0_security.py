"""Regression checks for the Phase 0 containment controls.

These tests use an isolated SQLite file and test-only secrets. They must never
depend on a developer's `.env` file or the production database.
"""
import asyncio
import base64
import hashlib
import io
import importlib.util
import json
import sqlite3
import subprocess
import sys
import types
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from PIL import Image, PngImagePlugin

from app import artifacts, auth, builder, corp, db, main as main_module, runtime, security, tools
from app.body_limits import MAX_REQUEST_BODY_BYTES
from app.enterprise_generator import generate_enterprise_project
from app.main import app, handle_telegram_update


def load_encrypted_backup_module():
    spec = importlib.util.spec_from_file_location(
        "encrypted_sqlite_backup", Path("scripts/encrypted_sqlite_backup.py")
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def configure_test_database(monkeypatch, tmp_path):
    """Point the lightweight data layer at a fresh, local test database."""
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-auth-secret-not-for-production")
    monkeypatch.setenv("ADMIN_PASSWORD", "test-admin-password-123")
    monkeypatch.setattr(db, "USE_TURSO", False)
    monkeypatch.setattr(db, "LOCAL_DB", str(tmp_path / "autocorp-test.db"))
    db.init()


def test_database_initialization_creates_tenant_query_indexes(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    indexes = {row["name"] for row in db.q("PRAGMA index_list('site_files')")}
    assert "idx_site_files_job_filename" in indexes
    indexes = {row["name"] for row in db.q("PRAGMA index_list('idempotency_records')")}
    assert {"idx_idempotency_job", "idx_idempotency_order"}.issubset(indexes)
    order_indexes = {row["name"]: row for row in db.q("PRAGMA index_list('site_orders')")}
    assert order_indexes["idx_site_orders_idempotency"]["unique"] == 1
    job_indexes = {row["name"]: row for row in db.q("PRAGMA index_list('jobs')")}
    assert job_indexes["idx_jobs_user_idempotency"]["unique"] == 1


def test_database_transaction_commits_all_writes_or_rolls_them_back(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    db.x("INSERT INTO agents(name, balance, uses) VALUES (?, ?, ?)", ("agent-a", 0, 0))
    db.x("INSERT INTO jobs(client, status, cost) VALUES (?, ?, ?)", ("client-a", "running", 0))

    ids = db.transaction([
        ("INSERT INTO ledger(ts, account, delta, memo, job_id) VALUES (?, ?, ?, ?, ?)",
         (1, "payroll:agent-a", -2, "test", 1)),
        ("UPDATE agents SET balance=balance+?, uses=uses+1 WHERE name=?", (2, "agent-a")),
        ("UPDATE jobs SET cost=cost+? WHERE id=?", (2, 1)),
    ])
    assert len(ids) == 3
    assert db.one("SELECT balance, uses FROM agents WHERE name=?", ("agent-a",)) == {"balance": 2, "uses": 1}
    assert db.one("SELECT cost FROM jobs WHERE id=1") == {"cost": 2}
    assert db.one("SELECT count(*) AS count FROM ledger WHERE job_id=1")["count"] == 1

    with pytest.raises(sqlite3.OperationalError):
        db.transaction([
            ("INSERT INTO ledger(ts, account, delta, memo, job_id) VALUES (?, ?, ?, ?, ?)",
             (2, "payroll:agent-a", -3, "rollback test", 1)),
            ("INSERT INTO missing_table(value) VALUES (?)", ("fail",)),
        ])
    assert db.one("SELECT count(*) AS count FROM ledger WHERE job_id=1")["count"] == 1


def test_turso_transaction_uses_single_non_retried_conditional_batch(monkeypatch):
    captured = {}

    def fake_request(requests, *, retry=True):
        captured["requests"] = requests
        captured["retry"] = retry
        batch_steps = requests[0]["batch"]["steps"]
        return [{
            "type": "ok",
            "response": {"result": {
                "step_errors": [None] * len(batch_steps),
                "step_results": [None, {"last_insert_rowid": 42}, {"last_insert_rowid": 0},
                                 {"last_insert_rowid": 0}],
            }},
        }]

    monkeypatch.setattr(db, "USE_TURSO", True)
    monkeypatch.setattr(db, "_turso_request", fake_request)
    assert db.transaction([("INSERT INTO records(value) VALUES (?)", ("value",))]) == [42]
    assert captured["retry"] is False
    assert len(captured["requests"]) == 1
    assert captured["requests"][0]["type"] == "batch"
    steps = captured["requests"][0]["batch"]["steps"]
    assert steps[1]["condition"] == {"type": "ok", "step": 0}
    assert steps[2]["condition"] == {"type": "and", "conds": [{"type": "ok", "step": 1}]}
    assert steps[3]["condition"] == {"type": "or", "conds": [{"type": "error", "step": 1}]}

def test_idempotency_columns_migrate_from_existing_sqlite_schema(monkeypatch, tmp_path):
    legacy_path = tmp_path / "legacy-autocorp.db"
    connection = sqlite3.connect(legacy_path)
    connection.executescript(
        """
        CREATE TABLE jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, request TEXT,
            status TEXT, plan TEXT, result TEXT, site_url TEXT,
            price REAL DEFAULT 0, cost REAL DEFAULT 0, created_at REAL
        );
        CREATE TABLE site_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER,
            customer_name TEXT, customer_phone TEXT, customer_address TEXT,
            items_json TEXT, total_egp REAL, payment_method TEXT,
            payment_ref TEXT, status TEXT, created_at REAL
        );
        INSERT INTO jobs(client, request, status, created_at)
        VALUES ('Legacy store', 'Keep this job', 'created', 1);
        INSERT INTO site_orders(job_id, customer_name, created_at)
        VALUES (1, 'Legacy customer', 1);
        """
    )
    connection.commit()
    connection.close()
    monkeypatch.setattr(db, "USE_TURSO", False)
    monkeypatch.setattr(db, "LOCAL_DB", str(legacy_path))

    db.init()

    job_columns = {row["name"] for row in db.q("PRAGMA table_info('jobs')")}
    order_columns = {row["name"] for row in db.q("PRAGMA table_info('site_orders')")}
    assert {"user_id", "idempotency_key", "request_hash"} <= job_columns
    assert {"idempotency_key", "request_hash"} <= order_columns
    assert db.one("SELECT request FROM jobs WHERE id=1")["request"] == "Keep this job"
    assert db.one("SELECT customer_name FROM site_orders WHERE id=1")["customer_name"] == "Legacy customer"


def test_runtime_and_test_dependency_locks_are_hash_verified_and_consumed():
    runtime_lock = Path("requirements.lock").read_text(encoding="utf-8")
    test_lock = Path("requirements-dev.lock").read_text(encoding="utf-8")
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    assert "autogenerated by pip-compile" in runtime_lock
    assert "fastapi==" in runtime_lock and "--hash=sha256:" in runtime_lock
    assert "pytest==" in test_lock and "--hash=sha256:" in test_lock
    assert "--require-hashes -r requirements-dev.lock" in workflow
    assert "COPY requirements.lock" in dockerfile
    assert "--require-hashes -r requirements.lock" in dockerfile


def test_runtime_sbom_matches_the_locked_runtime_dependency_inventory():
    sbom = json.loads(Path("docs/sbom.cdx.json").read_text(encoding="utf-8"))
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    components = {(component["name"], component["version"]) for component in sbom["components"]}
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.7"
    assert {"fastapi", "uvicorn", "argon2-cffi", "cryptography", "pillow"} <= {
        name for name, _version in components
    }
    assert "cyclonedx-bom==7.5.0" in workflow
    assert "--output-reproducible" in workflow
    assert "git diff --exit-code -- docs/sbom.cdx.json" in workflow


def test_encrypted_sqlite_backup_round_trip_and_refuses_overwrite(tmp_path):
    backup_module = load_encrypted_backup_module()
    source = tmp_path / "source.sqlite"
    connection = sqlite3.connect(source)
    connection.execute("CREATE TABLE records (value TEXT)")
    connection.execute("INSERT INTO records(value) VALUES ('private record')")
    connection.commit()
    connection.close()
    key = backup_module.decode_backup_key(base64.urlsafe_b64encode(b"k" * 32).decode("ascii"))
    encrypted = tmp_path / "encrypted-backup.json"
    details = backup_module.create_encrypted_backup(
        source, encrypted, key, owner="security-team", retention_until="2099-01-01", key_id="kms://backup-key-v1"
    )
    assert details["algorithm"] == "AES-256-GCM"
    assert "private record" not in encrypted.read_text(encoding="utf-8")
    with pytest.raises(FileExistsError):
        backup_module.create_encrypted_backup(
            source, encrypted, key, owner="security-team", retention_until="2099-01-01", key_id="kms://backup-key-v1"
        )
    restored = tmp_path / "restored.sqlite"
    backup_module.restore_encrypted_backup(encrypted, restored, key)
    connection = sqlite3.connect(restored)
    assert connection.execute("SELECT value FROM records").fetchone()[0] == "private record"
    connection.close()


def register(client, username, password):
    response = client.post(
        "/api/auth/register", json={"username": username, "password": password}
    )
    assert response.status_code == 200, response.text
    return response


def test_browser_session_is_httponly_and_not_in_response(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        response = register(client, "alpha", "long-password-123")

        assert "token" not in response.json()["user"]
        cookie = response.headers["set-cookie"].lower()
        assert "autocorp_session=" in cookie
        assert "httponly" in cookie
        assert response.headers["x-request-id"]
        assert client.get("/api/jobs").status_code == 200
        copied_token = client.cookies.get("autocorp_session")
        assert copied_token
        # The old dashboard sends this empty header during the cookie migration.
        assert client.get("/api/jobs", headers={"x-user-token": ""}).status_code == 200
        assert client.post(
            "/api/auth/logout", headers={"origin": "https://attacker.example"}
        ).status_code == 403
        assert client.post(
            "/api/auth/logout", headers={"sec-fetch-site": "cross-site"}
        ).status_code == 403
        assert client.post("/api/auth/logout").status_code == 200
        # A stolen copy of the signed token cannot survive a server-side logout.
        assert auth.get_active_user(copied_token) is None
        assert client.get("/api/jobs", headers={"x-user-token": copied_token}).status_code == 401
        event = db.one(
            "SELECT actor_id, action, outcome FROM audit_events WHERE action = ? ORDER BY id DESC LIMIT 1",
            ("identity.logout_succeeded",),
        )
        assert event == {"actor_id": 1, "action": "identity.logout_succeeded", "outcome": "success"}


def test_api_errors_have_stable_envelopes_without_breaking_detail(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        unauthorized = client.get("/api/jobs")
        assert unauthorized.status_code == 401
        assert unauthorized.json()["error"]["code"] == "http_401"
        assert unauthorized.json()["detail"] == "Authentication is required"
        assert unauthorized.json()["error"]["request_id"] == unauthorized.headers["x-request-id"]

        invalid = client.post(
            "/api/auth/register", json={"username": "x", "password": "short"}
        )
        assert invalid.status_code == 422
        assert invalid.json()["error"]["code"] == "validation_error"
        assert invalid.json()["detail"][0]["location"] == ["body", "username"]


def test_unexpected_api_errors_do_not_expose_exception_text(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "runtime_security_status", lambda: (_ for _ in ()).throw(RuntimeError("private failure")))
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/api/healthz")
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "internal_error"
        assert "private failure" not in response.text


def test_production_write_origin_does_not_trust_client_host_header(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    monkeypatch.setenv("PUBLIC_URL", "https://app.example.test")
    with TestClient(app) as client:
        register(client, "alpha", "long-password-123")
        spoofed = client.post(
            "/api/auth/logout",
            headers={"origin": "https://attacker.example", "host": "attacker.example"},
        )
        assert spoofed.status_code == 403
        trusted = client.post(
            "/api/auth/logout",
            headers={"origin": "https://app.example.test", "host": "attacker.example"},
        )
        assert trusted.status_code == 200


def test_authentication_fails_closed_without_the_signing_secret(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    monkeypatch.delenv("AUTH_SECRET_KEY")
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/register", json={"username": "alpha", "password": "long-password-123"}
        )
        assert response.status_code == 503
        health = client.get("/api/healthz")
        assert health.status_code == 503
        assert health.json()["missing_required_settings"] == ["AUTH_SECRET_KEY"]


def test_maintenance_mode_allows_reads_but_rejects_all_writes(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    monkeypatch.setenv("MAINTENANCE_MODE", "1")
    with TestClient(app) as client:
        blocked = client.post(
            "/api/auth/register", json={"username": "alpha", "password": "long-password-123"}
        )
        assert blocked.status_code == 503
        assert blocked.json()["error"]["code"] == "maintenance_mode"
        assert blocked.headers["cache-control"] == "no-store"
        assert blocked.headers["retry-after"] == "3600"
        assert db.one("SELECT id FROM users WHERE username=?", ("alpha",)) is None
        assert client.get("/api/healthz").status_code == 200


def test_health_fails_closed_without_argon2id_dependency(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "_argon2_available", lambda: False)
    with TestClient(app) as client:
        health = client.get("/api/healthz")
        assert health.status_code == 503
        assert health.json()["missing_required_dependencies"] == ["argon2-cffi"]
        assert health.json()["database_ready"] is True


def test_vercel_readiness_requires_durable_turso_storage(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
    with TestClient(app) as client:
        health = client.get("/api/healthz")
        assert health.status_code == 503
        assert health.json()["missing_serverless_storage_settings"] == [
            "TURSO_DATABASE_URL", "TURSO_AUTH_TOKEN"
        ]


def test_readiness_fails_for_incomplete_opt_in_automation(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    monkeypatch.setenv("ENABLE_OUTBOUND_WEBHOOKS", "1")
    monkeypatch.delenv("OUTBOUND_WEBHOOK_SECRET", raising=False)
    monkeypatch.delenv("OUTBOUND_WEBHOOKS", raising=False)
    with TestClient(app) as client:
        health = client.get("/api/healthz")
        assert health.status_code == 503
        assert health.json()["automation_configuration_errors"] == [
            "ENABLE_OUTBOUND_WEBHOOKS requires OUTBOUND_WEBHOOK_SECRET",
            "ENABLE_OUTBOUND_WEBHOOKS requires OUTBOUND_WEBHOOKS",
        ]


def test_passwords_use_argon2id_and_upgrade_legacy_scrypt(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        register(client, "alpha", "long-password-123")
        current = db.one("SELECT password_hash FROM users WHERE username = ?", ("alpha",))
        assert current["password_hash"].startswith("$argon2id$")

        salt = b"legacy-test-salt"
        digest = hashlib.scrypt(b"long-password-123", salt=salt, n=2**14, r=8, p=1, dklen=32)
        legacy_hash = f"scrypt$16384$8$1${salt.hex()}${digest.hex()}"
        db.x("UPDATE users SET password_hash = ? WHERE username = ?", (legacy_hash, "alpha"))
        assert client.post(
            "/api/auth/login", json={"username": "alpha", "password": "long-password-123"}
        ).status_code == 200
        upgraded = db.one("SELECT password_hash FROM users WHERE username = ?", ("alpha",))
        assert upgraded["password_hash"].startswith("$argon2id$")


def test_request_correlation_id_is_validated_or_generated(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        trusted = "trusted-request-123"
        assert client.get("/api/healthz", headers={"x-request-id": trusted}).headers["x-request-id"] == trusted
        generated = client.get("/api/healthz", headers={"x-request-id": "not valid"}).headers["x-request-id"]
        assert generated != "not valid"
        assert len(generated) == 32


def test_audit_event_keeps_validated_request_correlation_id(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        request_id = "audit-trace-0001"
        response = client.post(
            "/api/auth/register",
            headers={"x-request-id": request_id},
            json={"username": "alpha", "password": "long-password-123"},
        )
        assert response.status_code == 200
        event = db.one(
            "SELECT request_id FROM audit_events WHERE action = ? ORDER BY id DESC LIMIT 1",
            ("identity.user_registered",),
        )
        assert event == {"request_id": request_id}


def test_production_https_origin_enables_transport_security_headers(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    monkeypatch.setenv("PUBLIC_URL", "https://app.example.test")
    with TestClient(app) as client:
        response = client.get("/api/healthz")
        assert response.headers["strict-transport-security"] == "max-age=63072000; includeSubDomains"
        assert response.headers["cross-origin-opener-policy"] == "same-origin"
        assert response.headers["x-permitted-cross-domain-policies"] == "none"
        assert response.headers["content-security-policy"] == (
            "base-uri 'self'; frame-ancestors 'none'; form-action 'self'; object-src 'none'"
        )


def test_https_canonical_origin_issues_secure_session_cookie(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    monkeypatch.setenv("PUBLIC_URL", "https://app.example.test")
    monkeypatch.delenv("COOKIE_SECURE", raising=False)
    with TestClient(app) as client:
        response = register(client, "alpha", "long-password-123")
        assert "secure" in response.headers["set-cookie"].lower()


def test_local_development_does_not_emit_hsts(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    monkeypatch.delenv("PUBLIC_URL", raising=False)
    with TestClient(app) as client:
        assert "strict-transport-security" not in client.get("/api/healthz").headers


def test_internal_operations_endpoints_require_an_admin_session(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        assert client.get("/api/summary").status_code == 401
        assert client.get("/api/providers").status_code == 401
        response = client.post("/api/admin/login", json={"password": "test-admin-password-123"})
        assert response.status_code == 200
        assert "token" not in response.json()
        assert client.get("/api/summary").status_code == 200
        assert client.get("/api/providers").status_code == 200
        audit_events = client.get("/api/audit-events")
        assert audit_events.status_code == 200
        assert any(event["action"] == "identity.admin_login_succeeded" for event in audit_events.json())


def test_telegram_never_accepts_password_commands(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    sent_messages = []

    async def fake_send(chat_id, message, *args, **kwargs):
        sent_messages.append((chat_id, message))

    monkeypatch.setattr("app.main.corp.tg_send", fake_send)
    update = {"message": {"chat": {"id": 42}, "message_id": 7, "text": "/login user password"}}
    asyncio.run(handle_telegram_update(update))
    asyncio.run(handle_telegram_update(update))

    assert len(sent_messages) == 1
    assert "disabled" in sent_messages[0][1].lower()
    assert db.one("SELECT id FROM users WHERE username = ?", ("user",)) is None


def test_telegram_pdf_ingestion_is_bounded_and_not_public(monkeypatch, tmp_path):
    """Keep the Telegram and web paths on one bounded PDF extractor."""
    configure_test_database(monkeypatch, tmp_path)

    class FakePage:
        def get_text(self):
            return "x" * 2_000

    class FakeDocument:
        def __iter__(self):
            return iter([FakePage() for _ in range(60)])

        def close(self):
            return None

    monkeypatch.setitem(sys.modules, "fitz", types.SimpleNamespace(open=lambda **_kwargs: FakeDocument()))
    extracted = main_module.extract_pdf_text(b"%PDF-test")
    assert len(extracted) == main_module.MAX_EXTRACTED_TEXT_CHARS


def test_telegram_webhook_fails_closed_without_a_secret(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    monkeypatch.delenv("TELEGRAM_SECRET", raising=False)
    with TestClient(app) as client:
        assert client.post("/telegram", json={"update_id": 1}).status_code == 401


def test_telegram_webhook_requires_the_configured_secret(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    monkeypatch.setenv("TELEGRAM_SECRET", "test-telegram-webhook-secret")
    with TestClient(app) as client:
        assert client.post("/telegram", json={"update_id": 2}).status_code == 401
        accepted = client.post(
            "/telegram",
            headers={"x-telegram-bot-api-secret-token": "test-telegram-webhook-secret"},
            json={"update_id": 3},
        )
        assert accepted.status_code == 200
        # Simulate a retry reaching a different worker without this process's
        # short-lived cache; the durable unique record must still win.
        main_module.PROCESSED_TG_UPDATES.clear()
        duplicate = client.post(
            "/telegram",
            headers={"x-telegram-bot-api-secret-token": "test-telegram-webhook-secret"},
            json={"update_id": 3},
        )
        assert duplicate.status_code == 200
        assert duplicate.json()["duplicate"] is True


def test_vercel_guide_requires_telegram_webhook_secret_token():
    guide = Path("DEPLOY_VERCEL.md").read_text(encoding="utf-8")
    assert "secret_token=${TELEGRAM_SECRET}" in guide
    assert "setWebhook?url=" not in guide
    assert "ليس إقراراً بأن" in guide


def test_tracked_secret_scanner_reports_only_rule_and_line_metadata():
    scanner_path = Path("scripts/scan_tracked_secrets.py")
    spec = importlib.util.spec_from_file_location("tracked_secret_scanner", scanner_path)
    scanner = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(scanner)

    fake_token = "ghp_" + "a" * 24
    assert scanner.scan_text(f"token = '{fake_token}'") == [(1, "github-token")]
    assert scanner.scan_text("AUTH_SECRET_KEY=\n") == []


def test_secret_scanner_includes_untracked_but_respects_gitignore(tmp_path):
    repo = tmp_path / "scanner-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / ".gitignore").write_text(".env\n", encoding="utf-8")
    (repo / "tracked.txt").write_text("tracked", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore", "tracked.txt"], cwd=repo, check=True)
    (repo / "untracked.txt").write_text("local draft", encoding="utf-8")
    (repo / ".env").write_text("LOCAL_SECRET=ignored", encoding="utf-8")

    scanner_path = Path("scripts/scan_tracked_secrets.py")
    spec = importlib.util.spec_from_file_location("tracked_secret_scanner", scanner_path)
    scanner = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(scanner)
    discovered = {path.relative_to(repo).as_posix() for path in scanner.repository_files(repo)}

    assert discovered == {".gitignore", "tracked.txt", "untracked.txt"}


def test_ci_has_dependency_audit_and_automated_patch_update_policy():
    ci_workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    dependabot = Path(".github/dependabot.yml").read_text(encoding="utf-8")
    assert "pypa/gh-action-pip-audit@v1.1.0" in ci_workflow
    assert "inputs: requirements.lock" in ci_workflow
    assert "package-ecosystem: pip" in dependabot
    assert "interval: weekly" in dependabot
    assert "- patch" in dependabot


def test_example_environment_has_unique_and_safe_automation_settings():
    assignments = [
        line.split("=", 1)[0]
        for line in Path(".env.example").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#") and "=" in line
    ]
    assert len(assignments) == len(set(assignments))
    values = {
        line.split("=", 1)[0]: line.split("=", 1)[1].split("#", 1)[0].strip()
        for line in Path(".env.example").read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#") and "=" in line
    }
    assert values["ENABLE_AUTOMATED_DEPLOYMENT"] == "0"
    assert values["ENABLE_OUTBOUND_WEBHOOKS"] == "0"
    assert values["AUTO_DELIVER"] == "0"


def test_container_runs_as_non_root_and_excludes_sensitive_build_context():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
    dockerignore = Path(".dockerignore").read_text(encoding="utf-8")
    assert "USER autocorp" in dockerfile
    assert "COPY --chown=autocorp:autocorp . ." in dockerfile
    assert ".env" in dockerignore
    assert ".git" in dockerignore
    assert "*.db" in dockerignore
    assert "sites" in dockerignore


def test_automation_defaults_to_owner_approval_and_never_publishes_from_a_token(monkeypatch):
    monkeypatch.setenv("NETLIFY_TOKEN", "configured-but-not-approval")
    monkeypatch.delenv("ENABLE_AUTOMATED_DEPLOYMENT", raising=False)
    assert asyncio.run(corp.deploy_netlify("<html></html>", 1)) is None

    example = Path(".env.example").read_text(encoding="utf-8")
    assert "ENABLE_AUTOMATED_DEPLOYMENT=0" in example
    assert "AUTO_APPROVE=0" in example
    assert "AUTO_DELIVER=0" in example
    source = Path("app/corp.py").read_text(encoding="utf-8")
    assert 'os.getenv("AUTO_APPROVE", "0") == "1"' in source
    assert 'os.getenv("AUTO_DELIVER", "0") == "1"' in source


def test_project_delivery_does_not_create_a_simulated_payment(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    monkeypatch.setattr(corp, "spawn", lambda task: task.close())

    async def no_external_event(*_args, **_kwargs):
        return None

    monkeypatch.setattr(corp, "emit", no_external_event)
    job_id = db.x(
        "INSERT INTO jobs(client, request, status, plan, result, site_url, price, cost, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "Alpha Store",
            "brief",
            "awaiting_delivery",
            json.dumps({"summary": "Storefront delivery"}),
            "{}",
            "/sites/1/",
            2500,
            100,
            0,
        ),
    )

    asyncio.run(corp.deliver(job_id))

    delivered = db.one("SELECT status, result FROM jobs WHERE id=?", (job_id,))
    result = json.loads(delivered["result"])
    assert delivered["status"] == "delivered"
    assert result["payment_status"] == "not_processed"
    assert "Status: paid" not in result["invoice"]
    assert db.one("SELECT id FROM ledger WHERE job_id=?", (job_id,)) is None


def test_outbound_webhooks_are_opt_in_signed_and_reject_unsafe_destinations(monkeypatch):
    monkeypatch.setenv("OUTBOUND_WEBHOOKS", "job_delivered=https://example.test/hooks/delivery")
    monkeypatch.delenv("ENABLE_OUTBOUND_WEBHOOKS", raising=False)
    assert asyncio.run(tools.webhook("job_delivered", {"job_id": 1})) == "Outbound webhooks are disabled."

    monkeypatch.setenv("ENABLE_OUTBOUND_WEBHOOKS", "1")
    monkeypatch.delenv("OUTBOUND_WEBHOOK_SECRET", raising=False)
    monkeypatch.setattr(tools, "_public", lambda _url: True)
    assert "signing secret" in asyncio.run(tools.webhook("job_delivered", {"job_id": 1}))

    monkeypatch.setenv("OUTBOUND_WEBHOOK_SECRET", "test-signing-secret")
    monkeypatch.setenv("OUTBOUND_WEBHOOKS", "job_delivered=http://127.0.0.1/private")
    monkeypatch.setattr(tools, "_public", lambda _url: False)
    assert "public HTTPS" in asyncio.run(tools.webhook("job_delivered", {"job_id": 1}))


def test_vercel_header_policies_cover_static_and_generated_sites():
    config = json.loads(Path("vercel.json").read_text(encoding="utf-8"))
    all_routes = next(rule for rule in config["headers"] if rule["source"] == "/(.*)")
    values = {entry["key"]: entry["value"] for entry in all_routes["headers"]}
    assert values["X-Content-Type-Options"] == "nosniff"
    assert "frame-ancestors 'none'" in values["Content-Security-Policy"]
    assert {"key": "Cache-Control", "value": "no-store"} in next(
        rule for rule in config["headers"] if rule["source"] == "/api/(.*)"
    )["headers"]

    generated = generate_enterprise_project(4, "Safe Store", "general", "", "", "", [], {})
    generated_config = json.loads(generated["vercel.json"])
    generated_headers = generated_config["headers"][0]["headers"]
    assert {"key": "X-Frame-Options", "value": "DENY"} in generated_headers
    assert any(
        header["key"] == "Content-Security-Policy"
        and "object-src 'none'" in header["value"]
        for header in generated_headers
    )
    generated_api_headers = next(
        rule for rule in generated_config["headers"] if rule["source"] == "/api/(.*)"
    )["headers"]
    assert {"key": "Cache-Control", "value": "no-store"} in generated_api_headers
    assert "USER app" in generated["Dockerfile"]
    assert "JWT_SECRET=replace-with" not in generated[".env.example"]
    assert "result, 201" not in generated["src/modules/auth/auth.controller.js"]
    assert "{ user: result.user }" in generated["src/modules/auth/auth.controller.js"]
    assert "sameSite: process.env.NODE_ENV === 'production' ? 'strict' : 'lax'" in generated["src/modules/auth/auth.controller.js"]
    assert "res.clearCookie('jwt_token', {" in generated["src/modules/auth/auth.controller.js"]
    assert "const env = require('./config/env');" in generated["src/app.js"]
    assert "express.json({ limit: '256kb', strict: true })" in generated["src/app.js"]
    assert "express.urlencoded({ extended: false, limit: '64kb', parameterLimit: 100 })" in generated["src/app.js"]
    assert "const allowedOrigins = env.CORS_ORIGIN" in generated["src/app.js"]
    assert "TRUST_PROXY_HOPS: trustProxyHops" in generated["src/config/env.js"]
    assert "app.set('trust proxy', env.TRUST_PROXY_HOPS)" in generated["src/app.js"]
    assert "TRUST_PROXY_HOPS=0" in generated[".env.example"]
    auth_routes = generated["src/modules/auth/auth.routes.js"]
    assert "rateLimiter(8, 15 * 60 * 1000, 'auth-login')" in auth_routes
    assert "rateLimiter(5, 60 * 60 * 1000, 'auth-register')" in auth_routes
    assert "validate(authValidation.validateRegister)" in auth_routes
    assert "validate(authValidation.validateLogin)" in auth_routes
    auth_validation = generated["src/modules/auth/auth.validation.js"]
    assert "Buffer.byteLength(password, 'utf8') > 72" in auth_validation
    assert "name.length < 2 || name.length > 100" in auth_validation
    assert "email.trim().toLowerCase()" in generated["src/modules/auth/auth.service.js"]
    assert "Rejects malformed registration and login input" in generated["tests/security.test.js"]
    for email_helper in ("src/utils/sendVerificationEmail.js", "src/utils/sendResetPasswordEmail.js"):
        helper = generated[email_helper]
        assert "new ApiError(503" in helper
        assert "console.log" not in helper
        assert "${token}" not in helper
    assert "Fails closed for email delivery without logging recovery tokens" in generated[
        "tests/security.test.js"
    ]
    assert "Rejects JSON request bodies larger than the API limit" in generated[
        "tests/security.test.js"
    ]
    limiter = generated["src/middlewares/rateLimiter.middleware.js"]
    assert "cleanup.unref()" in limiter
    assert "Retry-After" in limiter
    assert "router.get('/', auth, admin, orderController.getOrders);" in generated[
        "src/modules/orders/order.routes.js"
    ]
    assert "router.get('/summary', auth, admin," in generated[
        "src/modules/dashboard/dashboard.routes.js"
    ]
    order_service = generated["src/modules/orders/order.service.js"]
    assert "exports.isAllowedStatusTransition" in order_service
    assert "Order status transition is not allowed" in order_service
    assert "Payment state is deliberately untouched" in order_service
    assert "body.items.length > 50" in order_service
    assert "Number.isSafeInteger(productId)" in order_service
    assert "line.quantity" in order_service and "Number.parseInt" not in order_service
    assert "Total order quantity cannot exceed 100" in order_service
    assert "idempotencyKeyHash" in order_service and "idempotencyFingerprint" in order_service
    assert "requestedItems" in order_service
    assert "findByIdempotencyKey(idempotencyKeyHash)" in order_service
    assert "findByIdempotencyKey" in generated["src/models/order.model.js"]
    assert "req.get('Idempotency-Key')" in generated["src/modules/orders/order.controller.js"]
    assert "result.duplicate ? 200 : 201" in generated["src/modules/orders/order.controller.js"]
    assert "Idempotency-Key" in generated["README.md"]
    assert "changed payload" in generated["README.md"]
    assert "duplicate).toBe(true)" in generated["tests/api.test.js"]
    assert "conflict.status).toBe(409)" in generated["tests/api.test.js"]
    assert "checkoutIdempotencyKey = checkoutIdempotencyKey || crypto.randomUUID()" in generated[
        "public/index.html"
    ]
    product_service = generated["src/modules/products/product.service.js"]
    assert "exports.normalizeProductInput" in product_service
    assert "Object.keys(data).some((key) => !allowed.has(key))" in product_service
    assert "image.protocol !== 'https:'" in product_service
    product_model = generated["src/models/product.model.js"]
    assert "id: s.products.length + 1" in product_model
    assert "...data" not in product_model
    assert "Accepts only bounded catalog fields" in generated["tests/security.test.js"]
    assert "items: cart.map(x => ({ id: x.id, quantity: x.qty }))" in generated[
        "public/index.html"
    ]
    assert "itemCount >= 100" in generated["public/index.html"]
    assert "exist.qty >= 50" in generated["public/index.html"]
    assert "never payment-state promotion" in generated["tests/security.test.js"]
    assert "Rejects malformed checkout data" in generated["tests/security.test.js"]
    admin_page = generated["public/admin.html"]
    assert 'id="admin-login-panel"' in admin_page
    assert "identity.data.role !== 'admin'" in admin_page
    assert "credentials: 'same-origin'" in admin_page
    assert "localStorage" not in admin_page and "sessionStorage" not in admin_page


def test_readme_does_not_overstate_security_or_tenant_isolation():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "Grade A+ | 100/100" not in readme
    assert "Database-Per-Tenant Isolation" not in readme
    assert "not a penetration test, dependency audit, OWASP certification" in readme
    assert "This is not physical isolation or database-enforced RLS" in readme


def test_login_throttle_blocks_password_spraying(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        for _ in range(5):
            response = client.post(
                "/api/auth/login", json={"username": "target", "password": "incorrect-password"}
            )
            assert response.status_code == 401
        assert client.post(
            "/api/auth/login", json={"username": "target", "password": "incorrect-password"}
        ).status_code == 429
        failed = db.one(
            "SELECT action, actor_type, outcome FROM audit_events WHERE action = ? ORDER BY id DESC LIMIT 1",
            ("identity.login_failed",),
        )
        assert failed == {"action": "identity.login_failed", "actor_type": "anonymous", "outcome": "denied"}


def test_admin_login_throttle_blocks_brute_force(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        for _ in range(5):
            assert client.post("/api/admin/login", json={"password": "incorrect-password"}).status_code == 401
        assert client.post(
            "/api/admin/login", json={"password": "incorrect-password"}
        ).status_code == 429
        failed = db.one(
            "SELECT action, actor_type, outcome FROM audit_events WHERE action = ? ORDER BY id DESC LIMIT 1",
            ("identity.admin_login_failed",),
        )
        assert failed == {"action": "identity.admin_login_failed", "actor_type": "anonymous", "outcome": "denied"}


def test_job_decision_requires_explicit_allowlisted_admin_choice(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    # The process-local throttle is shared across test cases in this module.
    main_module.rate_limit.admin_login_limiter.reset("testclient:admin")
    with TestClient(app) as client:
        assert client.post(
            "/api/admin/login", json={"password": "test-admin-password-123"}
        ).status_code == 200
        job_id = db.x(
            "INSERT INTO jobs(client, request, status, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
            ("Alpha Store", "brief", "awaiting_plan", 0, 0),
        )

        missing = client.post(f"/api/jobs/{job_id}/decision", json={})
        unsupported = client.post(
            f"/api/jobs/{job_id}/decision", json={"decision": "execute"}
        )
        extra_field = client.post(
            f"/api/jobs/{job_id}/decision",
            json={"decision": "reject", "force_delivery": True},
        )

        assert missing.status_code == 422
        assert unsupported.status_code == 422
        assert extra_field.status_code == 422
        assert db.one("SELECT status FROM jobs WHERE id=?", (job_id,))["status"] == "awaiting_plan"


def test_campaign_decision_requires_pending_owned_draft_and_audits_action(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        register(client, "alpha", "long-password-123")
        job_id = db.x(
            "INSERT INTO jobs(client, request, status, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
            ("Alpha Store", "brief", "created", 1, 0),
        )
        automation_id = db.x(
            "INSERT INTO site_automations(job_id, type, title, content, target_platform, status, created_at) "
            "VALUES (?, 'email', 'Draft', 'Campaign', 'email', 'pending_approval', 0)",
            (job_id,),
        )

        endpoint = f"/api/sites/{job_id}/automations/approve-email"
        assert client.post(endpoint, json={"automation_id": automation_id}).status_code == 422
        assert client.post(
            endpoint, json={"automation_id": automation_id, "decision": "ship"}
        ).status_code == 422
        assert client.post(
            endpoint,
            json={"automation_id": automation_id, "decision": "approve", "send_now": True},
        ).status_code == 422
        assert db.one("SELECT status FROM site_automations WHERE id=?", (automation_id,))["status"] == "pending_approval"

        approved = client.post(
            endpoint, json={"automation_id": automation_id, "decision": "approve"}
        )
        assert approved.status_code == 200
        assert approved.json()["status"] == "approved"
        assert client.post(
            endpoint, json={"automation_id": automation_id, "decision": "approve"}
        ).status_code == 409
        event = db.one(
            "SELECT actor_id, action, target_id, outcome FROM audit_events "
            "WHERE action='marketing.email_decision' ORDER BY id DESC LIMIT 1"
        )
        assert event == {
            "actor_id": 1,
            "action": "marketing.email_decision",
            "target_id": str(automation_id),
            "outcome": "success",
        }


def test_admin_post_and_proposal_decisions_require_explicit_valid_transitions(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    main_module.rate_limit.admin_login_limiter.reset("testclient:admin")
    with TestClient(app) as client:
        assert client.post(
            "/api/admin/login", json={"password": "test-admin-password-123"}
        ).status_code == 200
        post_id = db.x(
            "INSERT INTO posts(job_id, text, status, ts) VALUES (0, 'Draft', 'pending', 0)"
        )
        proposal_id = db.x(
            "INSERT INTO proposals(kind, target, content, old, reason, status, ts) "
            "VALUES ('prompt', 'Test Agent', 'New prompt', 'Old prompt', 'Test', 'pending', 0)"
        )

        post_endpoint = f"/api/posts/{post_id}/decision"
        proposal_endpoint = f"/api/proposals/{proposal_id}/decision"
        for endpoint, payload in (
            (post_endpoint, {}),
            (post_endpoint, {"decision": "publish"}),
            (proposal_endpoint, {}),
            (proposal_endpoint, {"decision": "apply"}),
            (proposal_endpoint, {"decision": "approve", "execute": True}),
        ):
            assert client.post(endpoint, json=payload).status_code == 422
        assert db.one("SELECT status FROM posts WHERE id=?", (post_id,))["status"] == "pending"
        assert db.one("SELECT status FROM proposals WHERE id=?", (proposal_id,))["status"] == "pending"

        assert client.post(proposal_endpoint, json={"decision": "rollback"}).status_code == 409
        rejected = client.post(proposal_endpoint, json={"decision": "reject"})
        assert rejected.status_code == 200
        assert db.one("SELECT status FROM proposals WHERE id=?", (proposal_id,))["status"] == "dropped"
        assert client.post(proposal_endpoint, json={"decision": "approve"}).status_code == 409

        rejected_post = client.post(post_endpoint, json={"decision": "reject"})
        assert rejected_post.status_code == 200
        assert db.one("SELECT status FROM posts WHERE id=?", (post_id,))["status"] == "dropped"


def test_generated_artifacts_require_responsive_safe_html():
    safe_document = (
        '<!doctype html><html lang="ar" dir="rtl"><head>'
        '<meta name="viewport" content="width=device-width, initial-scale=1"></head><body>Safe</body></html>'
    )
    assert artifacts.validate_site_html(safe_document) == []
    unsafe_document = (
        '<!doctype html><html lang="en"><head><meta name="viewport" content="width=device-width">'
        '</head><body><iframe src="https://attacker.example"></iframe></body></html>'
    )
    assert "embedded active content is not allowed" in artifacts.validate_site_html(unsafe_document)
    assert artifacts.validate_site_html(
        builder.build_site_html(1, "Safe Store", "متجر إلكتروني", settings={}, items=[])
    ) == []
    escaped_catalog = builder.build_site_html(
        2,
        "Safe Store",
        "متجر إلكتروني",
        settings={},
        items=[{"title": "</script><script>alert(1)</script>", "price": 10}],
    )
    assert "</script><script>alert(1)</script>" not in escaped_catalog
    assert "\\u003c/script\\u003e" in escaped_catalog
    escaped_service = builder.build_site_html(
        3,
        "Safe Portfolio",
        "cybersecurity portfolio",
        settings={},
        items=[{"title": "x');alert(1);//", "price": "not-a-price", "description": "safe"}],
    )
    assert "requestService('x');alert" not in escaped_service
    assert "requestService(&quot;x&#x27;);alert(1);//&quot;, 0.0)" in escaped_service
    exported = generate_enterprise_project(
        3,
        "Safe Store",
        "general",
        "",
        "",
        "",
        [{"title": "</script><script>alert(1)</script>", "price": 10}],
        {},
    )
    assert "</script><script>alert(1)</script>" not in exported["public/index.html"]
    exported_order_service = exported["src/modules/orders/order.service.js"]
    assert "totalEgp: body.total_egp" not in exported_order_service
    assert "ProductModel.findById" in exported_order_service
    assert "pending_confirmation" in exported_order_service
    assert "merchant confirmation" in exported_order_service
    assert ".env" not in exported
    assert "JWT_SECRET=replace-with-a-strong-random-secret" not in exported[".env.example"]
    assert "JWT_SECRET=  # set a unique 32+-character secret" in exported[".env.example"]
    assert "autocorp_enterprise_secret" not in exported["src/config/env.js"]
    assert "CORS_ORIGIN: process.env.CORS_ORIGIN || '*'" not in exported["src/config/env.js"]
    assert "allowedOrigins.includes('*')" not in exported["src/app.js"]
    assert "credentialed HttpOnly session cookies" in exported["src/app.js"]
    assert '"users": []' in exported["database.json"]
    assert "INSERT OR IGNORE INTO users" not in exported["schema.sql"]
    assert "password === 'admin123'" not in exported["src/modules/auth/auth.service.js"]


def test_exported_project_escapes_brand_and_omits_payment_destinations():
    exported = generate_enterprise_project(
        6,
        '<img src=x onerror="alert(1)">',
        "general",
        "<script>alert(1)</script>",
        '#fff" onmouseover="alert(1)',
        "javascript:alert(1)",
        [],
        {
            "phone": '0100" onclick="alert(1)',
            "vodafone_cash": "private-wallet",
            "instapay": "private@instapay",
            "fawry_code": "private-code",
        },
    )
    assert '<img src=x onerror="alert(1)">' not in exported["public/index.html"]
    assert "<script>alert(1)</script>" not in exported["public/index.html"]
    assert "onmouseover=\"alert(1)" not in exported["public/index.html"]
    assert "private-wallet" not in "\n".join(exported.values())
    assert "private@instapay" not in "\n".join(exported.values())
    assert "private-code" not in "\n".join(exported.values())


def test_generated_storefront_does_not_publish_manual_payment_destinations():
    storefront = builder.build_site_html(
        4,
        "Safe Store",
        "electronic store",
        settings={
            "vodafone_cash": "private-wallet-0100",
            "instapay": "private@instapay",
            "fawry_code": "private-fawry-code",
        },
        items=[{"title": "Safe item", "price": 10, "category": "General", "description": "safe"}],
    )
    assert "private-wallet-0100" not in storefront
    assert "private@instapay" not in storefront
    assert "private-fawry-code" not in storefront
    assert 'value="cash_on_delivery" checked' in storefront


def test_generated_site_normalizes_attribute_bound_settings():
    generated = builder.build_site_html(
        5,
        "Safe Store",
        "electronic store",
        settings={
            "color_primary": '#fff" onmouseover="alert(1)',
            "color_secondary": "javascript:alert(1)",
            "phone": '0100" onclick="alert(1)',
            "whatsapp": "0111<script>alert(1)</script>",
        },
        items=[],
    )
    assert 'onmouseover="alert(1)' not in generated
    assert 'onclick="alert(1)' not in generated
    assert "javascript:alert(1)" not in generated
    assert "<script>alert(1)</script>" not in generated
    assert 'href="tel:01001"' in generated


def test_generated_site_does_not_invent_merchant_contact_details():
    storefront = builder.build_site_html(8, "New Store", "general", settings={}, items=[])
    assert "01000000000" not in storefront
    assert "wa.me/?" not in storefront
    assert "بيانات التواصل قيد الإعداد" in storefront
    portfolio = builder.build_site_html(9, "New Agency", "cybersecurity portfolio", settings={}, items=[])
    assert "wa.me/?" not in portfolio
    assert "بيانات التواصل قيد الإعداد" in portfolio
    exported = generate_enterprise_project(8, "New Store", "general", "", "", "", [], {})
    assert "01000000000" not in exported["database.json"]


def test_static_review_does_not_claim_owasp_certification():
    report = security.run_sast_security_scan({"public/index.html": "<!doctype html><html></html>"})
    assert report["assessment_type"] == "automated static review; not OWASP certification"
    assert report["grade"] == "STATIC_REVIEW"
    assert "not an OWASP compliance certification" in report["summary"]
    assert report["owasp_compliance"]["A10"]["status"] == "STATIC_CHECK_PASSED"
    dashboard = Path("static/index.html").read_text(encoding="utf-8")
    assert "Static review pending" in dashboard
    assert "not a certification" in dashboard
    assert "تحديث شهادة OWASP" not in dashboard
    assert "مطابق لمعايير OWASP Top 10 بدون أي ثغرات" not in dashboard


def test_dashboard_serializes_inline_handler_arguments_and_syncs_static_copies():
    dashboard = Path("static/index.html").read_text(encoding="utf-8")
    mirrored_dashboard = Path("api/static/index.html").read_text(encoding="utf-8")
    assert dashboard == mirrored_dashboard
    assert "const jsArg = value => JSON.stringify(String(value ?? ''));" in dashboard
    assert "openDeleteConfirmModal(${j.id}, ${esc(jsArg(j.client))})" in dashboard
    assert "loadTenantTableData(${esc(jsArg(t.table_name))})" in dashboard
    assert "safeSiteUrl(j.frontend_url" in dashboard
    assert 'rel="noopener noreferrer"' in dashboard


def test_jobs_are_private_to_the_authenticated_owner(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as alpha, TestClient(app) as bravo:
        register(alpha, "alpha", "long-password-123")
        job_id = db.x(
            "INSERT INTO jobs(client, request, status, user_id, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Alpha Store", "brief", "created", 1, 0),
        )
        register(bravo, "bravo", "long-password-456")

        assert len(alpha.get("/api/jobs").json()) == 1
        assert bravo.get("/api/jobs").json() == []
        assert bravo.get(f"/api/jobs/{job_id}").status_code == 403
        assert TestClient(app).get("/api/jobs").status_code == 401


def test_deleted_user_session_is_revoked_immediately(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        register(client, "alpha", "long-password-123")
        assert client.get("/api/jobs").status_code == 200
        db.x("DELETE FROM users WHERE username = ?", ("alpha",))
        assert client.get("/api/jobs").status_code == 401


def test_tenant_file_viewer_rejects_path_traversal(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        register(client, "alpha", "long-password-123")
        job_id = db.x(
            "INSERT INTO jobs(client, request, status, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
            ("Alpha Store", "brief", "created", 1, 0),
        )
        # HTTP clients normalize literal ../ segments before routing, so cover
        # that boundary at the filename validator itself as well.
        with pytest.raises(HTTPException) as exc_info:
            main_module.safe_site_filename("../.env")
        assert exc_info.value.status_code == 400
        for alias in ("./.env", "src/./config.js", "src//config.js"):
            with pytest.raises(HTTPException) as alias_error:
                main_module.safe_site_filename(alias)
            assert alias_error.value.status_code == 400
        assert main_module.safe_site_filename(".env.example") == ".env.example"
        assert client.get(f"/api/sites/{job_id}/files/C:%5CWindows%5Cwin.ini").status_code == 400


def test_tenant_file_editor_rejects_unbounded_or_unknown_fields(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    monkeypatch.setenv("ENABLE_TENANT_FILE_EDITOR", "1")
    with TestClient(app) as client:
        register(client, "alpha", "long-password-123")
        job_id = db.x(
            "INSERT INTO jobs(client, request, status, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
            ("Alpha Store", "brief", "created", 1, 0),
        )
        oversized = client.put(
            f"/api/sites/{job_id}/files/index.html",
            json={"content": "x" * 1_000_001},
        )
        assert oversized.status_code == 422
        unexpected = client.put(
            f"/api/sites/{job_id}/files/index.html",
            json={"content": "<h1>ok</h1>", "publish": True},
        )
        assert unexpected.status_code == 422
        assert db.one("SELECT html FROM site_pages WHERE job_id=?", (job_id,)) is None


def test_job_creation_idempotency_prevents_duplicate_projects(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        register(client, "alpha", "long-password-123")
        headers = {"idempotency-key": "job-create-unique-0001"}
        payload = {"client": "Alpha Store", "request": "Build a small store"}
        first = client.post("/api/jobs", json=payload, headers=headers)
        second = client.post("/api/jobs", json=payload, headers=headers)
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["id"] == second.json()["id"]
        assert second.json()["duplicate"] is True
        assert db.one("SELECT count(*) AS count FROM jobs")["count"] == 1
        stored_key = db.one(
            "SELECT idempotency_key, request_hash FROM jobs WHERE id=?",
            (first.json()["id"],),
        )
        assert stored_key["idempotency_key"] == "job-create-unique-0001"
        assert len(stored_key["request_hash"]) == 64
        changed = client.post(
            "/api/jobs",
            json={"client": "Alpha Store", "request": "Build a different store"},
            headers=headers,
        )
        assert changed.status_code == 409
        assert db.one("SELECT count(*) AS count FROM jobs")["count"] == 1


def test_project_create_contract_bounds_wizard_arrays_and_server_controls_execution(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    observed_at_start = []

    def capture_start(task):
        job = db.one("SELECT id FROM jobs ORDER BY id DESC LIMIT 1")
        observed_at_start.append({
            "job_id": job["id"],
            "settings": db.one("SELECT brand_name FROM site_settings WHERE job_id=?", (job["id"],)),
            "item": db.one("SELECT title FROM site_items WHERE job_id=?", (job["id"],)),
        })
        task.close()

    monkeypatch.setattr(corp, "spawn", capture_start)
    with TestClient(app) as client:
        register(client, "alpha", "long-password-123")
        invalid_payloads = [
            {"client": "Store", "request": "Build a store", "items": [{"title": "Item"}] * 51},
            {"client": "Store", "request": "Build a store", "ai_answers": [{"a": "Answer"}] * 21},
            {"client": "Store", "request": "Build a store", "sync": True},
            {"client": {"unexpected": "object"}, "request": "Build a store"},
        ]
        for payload in invalid_payloads:
            response = client.post("/api/jobs", json=payload)
            assert response.status_code == 422
        assert db.one("SELECT count(*) AS count FROM jobs")["count"] == 0

        # This mirrors the current dashboard's successful wizard payload shape.
        dashboard_payload = {
            "brand_name": "Alpha Store",
            "category": "retail",
            "slogan": "A sample shop",
            "logo_url": "",
            "palette": "ocean",
            "vodafone_cash": "",
            "instapay": "",
            "fawry_code": "",
            "cod_enabled": True,
            "phone": "01000000000",
            "whatsapp": "01000000000",
            "address": "Cairo",
            "items": [{"title": "Lamp", "price": 25.5, "category": "Lighting", "badge": "New"}],
            "ai_answers": [{"label": "Audience", "a": "Local families"}],
            "extracted_text": "Brief text",
            "features": {
                "auth": True, "bilingual": True, "darklight": True, "reviews": True,
                "promos": True, "admin": True, "docker": True, "hostinger": True,
            },
        }
        created = client.post("/api/jobs", json=dashboard_payload)
        assert created.status_code == 200, created.text
        assert db.one("SELECT title, price FROM site_items WHERE job_id=?", (created.json()["id"],)) == {
            "title": "Lamp", "price": 25.5,
        }
        assert observed_at_start[-1] == {
            "job_id": created.json()["id"],
            "settings": {"brand_name": "Alpha Store"},
            "item": {"title": "Lamp"},
        }


def test_uploads_require_authentication_and_validate_file_signature(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    asset_root = tmp_path / "asset-root"
    monkeypatch.setattr(main_module, "BASE", str(asset_root))
    with TestClient(app) as anonymous, TestClient(app) as client:
        assert anonymous.post(
            "/api/upload", files={"file": ("logo.png", b"\x89PNG\r\n\x1a\n", "image/png")}
        ).status_code == 401

        register(client, "alpha", "long-password-123")
        assert client.post(
            "/api/upload", files={"file": ("note.txt", b"not allowed", "text/plain")}
        ).status_code == 415
        assert client.post(
            "/api/upload", files={"file": ("fake.png", b"not a PNG", "image/png")}
        ).status_code == 415
        image_bytes = io.BytesIO()
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text("Sensitive", "remove this metadata")
        Image.new("RGB", (2, 2), "red").save(image_bytes, format="PNG", pnginfo=metadata)
        image = client.post(
            "/api/upload", files={"file": ("logo.png", image_bytes.getvalue(), "image/png")}
        )
        assert image.status_code == 200
        with Image.open(asset_root / "static" / "uploads" / image.json()["filename"]) as saved:
            assert "Sensitive" not in saved.info
        pdf = client.post(
            "/api/upload",
            files={"file": ("brief.pdf", b"%PDF-1.4\n", "application/pdf")},
        )
        assert pdf.status_code == 200
        assert pdf.json()["url"] == ""


def test_high_risk_prototype_surfaces_are_disabled_and_bot_tokens_redacted(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        register(client, "alpha", "long-password-123")
        job_id = db.x(
            "INSERT INTO jobs(client, request, status, user_id, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Alpha Store", "brief", "created", 1, 0),
        )
        db.x(
            "INSERT INTO site_bot_configs "
            "(job_id, bot_platform, bot_token, bot_name, is_active, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, "telegram", "must-never-be-returned", "Alpha Bot", 1, 0),
        )

        integrations = client.get(f"/api/sites/{job_id}/integrations")
        assert integrations.status_code == 200
        config = integrations.json()["config"]
        assert "bot_token" not in config
        assert config["has_bot_token"] is True

        assert client.post(
            f"/api/sites/{job_id}/integrations/bot", json={"bot_token": "new-token"}
        ).status_code == 503
        assert client.post(
            f"/api/sites/{job_id}/database/query", json={"query": "SELECT 1"}
        ).status_code == 503
        assert client.put(
            f"/api/sites/{job_id}/files/index.html", json={"content": "<h1>changed</h1>"}
        ).status_code == 503
        assert client.post(
            f"/api/sites/{job_id}/deploy-github", json={"github_token": "not-used"}
        ).status_code == 503
        oversized_provider_token = client.post(
            f"/api/sites/{job_id}/deploy-github",
            json={"github_token": "x" * 257},
        )
        assert oversized_provider_token.status_code == 422
        unsafe_hook = client.post(
            f"/api/sites/{job_id}/deploy-vercel",
            json={"deploy_hook": "http://127.0.0.1/latest/meta-data"},
        )
        assert unsafe_hook.status_code == 422
        valid_hook = client.post(
            f"/api/sites/{job_id}/deploy-vercel",
            json={
                "deploy_hook": "https://api.vercel.com/v1/integrations/deploy/prj_example/secret-hook",
            },
        )
        assert valid_hook.status_code == 503

        monkeypatch.setenv("ENABLE_DIRECT_DEPLOYMENT", "1")
        query_token = client.get(
            f"/api/sites/{job_id}/deploy-status?deployment_id=deploy_123&vercel_token=must-not-leak"
        )
        assert query_token.status_code == 400
        assert "must-not-leak" not in query_token.text
        status_without_provider = client.get(
            f"/api/sites/{job_id}/deploy-status?deployment_id=deploy_123"
        )
        assert status_without_provider.status_code == 503
        assert client.post(
            f"/api/sites/{job_id}/activate-payment",
            json={"payment_method": "demo", "payment_ref": "not-a-payment"},
        ).status_code == 503


def test_enabled_tenant_reporting_console_still_allows_only_read_only_tables(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    monkeypatch.setenv("ENABLE_TENANT_SQL_CONSOLE", "1")
    site_root = tmp_path / "sites"
    monkeypatch.setattr(main_module.corp, "SITES", str(site_root))
    with TestClient(app) as client:
        register(client, "alpha", "long-password-123")
        job_id = db.x(
            "INSERT INTO jobs(client, request, status, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
            ("Alpha Store", "brief", "created", 1, 0),
        )
        tenant_dir = site_root / str(job_id)
        tenant_dir.mkdir(parents=True)
        with sqlite3.connect(tenant_dir / "database.sqlite") as connection:
            connection.executescript(
                "CREATE TABLE products (id INTEGER, name TEXT);"
                "INSERT INTO products VALUES (1, 'Public item');"
                "CREATE TABLE users (id INTEGER, email TEXT);"
                "INSERT INTO users VALUES (1, 'private@example.test');"
            )
        assert client.post(
            f"/api/sites/{job_id}/database/query", json={"query": "DELETE FROM products"}
        ).status_code == 400
        assert client.post(
            f"/api/sites/{job_id}/database/query", json={"query": "SELECT * FROM users"}
        ).status_code == 400
        allowed = client.post(
            f"/api/sites/{job_id}/database/query", json={"query": "SELECT * FROM products"}
        )
        assert allowed.status_code == 200
        joined = client.post(
            f"/api/sites/{job_id}/database/query",
            json={"query": "SELECT products.name, users.email FROM products JOIN users ON users.id = products.id"},
        )
        assert joined.status_code == 400
        assert "private@example.test" not in joined.text


def test_site_deletion_keeps_audit_evidence_and_removes_site_security_artifact(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        register(client, "alpha", "long-password-123")
        job_id = db.x(
            "INSERT INTO jobs(client, request, status, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
            ("Alpha Store", "brief", "created", 1, 0),
        )
        db.x(
            "INSERT INTO site_security_audits(job_id, score, grade, audited_at) VALUES (?, ?, ?, ?)",
            (job_id, 50, "STATIC_REVIEW", 0),
        )
        db.x("INSERT INTO posts(job_id, text, status, ts) VALUES (?, ?, ?, ?)", (job_id, "draft", "pending", 0))
        order_id = db.x("INSERT INTO site_orders(job_id, created_at) VALUES (?, ?)", (job_id, 0))
        db.x(
            "INSERT INTO idempotency_records(scope, idempotency_key, request_hash, job_id, order_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("order", "delete-test-order", "test-request-hash", 0, order_id, 0),
        )
        deleted = client.delete(f"/api/sites/{job_id}")
        assert deleted.status_code == 200
        assert db.one("SELECT id FROM jobs WHERE id=?", (job_id,)) is None
        assert db.one("SELECT job_id FROM site_security_audits WHERE job_id=?", (job_id,)) is None
        assert db.one("SELECT id FROM posts WHERE job_id=?", (job_id,)) is None
        assert db.one("SELECT idempotency_key FROM idempotency_records WHERE order_id=?", (order_id,)) is None
        event = db.one(
            "SELECT action, target_id FROM audit_events WHERE action='site.deletion_requested' ORDER BY id DESC LIMIT 1"
        )
        assert event == {"action": "site.deletion_requested", "target_id": str(job_id)}


def test_site_deletion_removes_only_unshared_tenant_uploads(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    asset_root = tmp_path / "asset-root"
    monkeypatch.setattr(main_module, "BASE", str(asset_root))
    monkeypatch.setattr(corp, "SITES", str(tmp_path / "sites"))
    upload_dirs = [
        asset_root / "static" / "uploads",
        asset_root / "api" / "static" / "uploads",
    ]
    for upload_dir in upload_dirs:
        upload_dir.mkdir(parents=True)

    with TestClient(app) as client:
        register(client, "alpha", "long-password-123")
        lone_job = db.x(
            "INSERT INTO jobs(client, request, status, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
            ("Lone Store", "brief", "created", 1, 0),
        )
        lone_filename = "tenant-only-logo.png"
        lone_url = f"/static/uploads/{lone_filename}"
        for upload_dir in upload_dirs:
            (upload_dir / lone_filename).write_bytes(b"image")
        db.x(
            "INSERT INTO site_files(job_id, filename, file_type, content, file_url, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (lone_job, lone_filename, "image", "", lone_url, 0),
        )

        assert client.delete(f"/api/sites/{lone_job}").status_code == 200
        assert all(not (upload_dir / lone_filename).exists() for upload_dir in upload_dirs)

        first_job = db.x(
            "INSERT INTO jobs(client, request, status, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
            ("First Store", "brief", "created", 1, 0),
        )
        second_job = db.x(
            "INSERT INTO jobs(client, request, status, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
            ("Second Store", "brief", "created", 1, 0),
        )
        shared_filename = "shared-logo.png"
        shared_url = f"/static/uploads/{shared_filename}"
        for upload_dir in upload_dirs:
            (upload_dir / shared_filename).write_bytes(b"image")
        for job_id in (first_job, second_job):
            db.x(
                "INSERT INTO site_files(job_id, filename, file_type, content, file_url, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (job_id, shared_filename, "image", "", shared_url, 0),
            )

        assert client.delete(f"/api/sites/{first_job}").status_code == 200
        assert all((upload_dir / shared_filename).exists() for upload_dir in upload_dirs)
        assert db.one("SELECT id FROM site_files WHERE job_id=?", (second_job,)) is not None


def test_site_settings_patch_preserves_omitted_values_and_rejects_unsafe_fields(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        register(client, "alpha", "long-password-123")
        job_id = db.x(
            "INSERT INTO jobs(client, request, status, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
            ("Alpha Store", "brief", "created", 1, 0),
        )
        db.x(
            "INSERT INTO site_settings(job_id, brand_name, category, phone, whatsapp, color_primary, "
            "color_secondary, cod_enabled, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (job_id, "Alpha Store", "retail", "201000000000", "201000000000", "#123456", "#abcdef", 1, 0),
        )
        db.x("INSERT INTO site_pages(job_id, html) VALUES (?, ?)", (job_id, "old html"))

        saved = client.post(
            f"/api/sites/{job_id}/settings",
            json={"custom_domain": "SHOP.Example.com.", "instapay": "merchant@bank"},
        )
        assert saved.status_code == 200, saved.text
        settings = db.one("SELECT * FROM site_settings WHERE job_id=?", (job_id,))
        assert settings["brand_name"] == "Alpha Store"
        assert settings["phone"] == "201000000000"
        assert settings["color_primary"] == "#123456"
        assert settings["cod_enabled"] == 1
        assert settings["custom_domain"] == "shop.example.com"
        assert settings["instapay"] == "merchant@bank"
        arabic_domain = client.post(
            f"/api/sites/{job_id}/settings", json={"custom_domain": "متجر.مصر"}
        )
        assert arabic_domain.status_code == 200
        assert db.one("SELECT custom_domain FROM site_settings WHERE job_id=?", (job_id,))["custom_domain"].startswith("xn--")

        for invalid in (
            {"logo_url": "javascript:alert(1)"},
            {"color_primary": "red; background:url(https://attacker.test)"},
            {"custom_domain": "https://shop.example.com/path"},
            {"unexpected": "value"},
            {},
        ):
            response = client.post(f"/api/sites/{job_id}/settings", json=invalid)
            assert response.status_code in {400, 422}


def test_refine_request_bounds_untrusted_llm_context(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        register(client, "alpha", "long-password-123")
        job_id = db.x(
            "INSERT INTO jobs(client, request, status, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
            ("Alpha Store", "brief", "created", 1, 0),
        )

        for payload in (
            {"prompt": "x" * 4001},
            {"prompt": "Refine", "extracted_text": "x" * 50_001},
            {"prompt": "Refine", "file_url": "javascript:alert(1)"},
            {"prompt": "Refine", "execute": True},
        ):
            response = client.post(f"/api/sites/{job_id}/refine", json=payload)
            assert response.status_code == 422


def test_marketing_draft_requests_bound_prompt_inputs(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        register(client, "alpha", "long-password-123")
        job_id = db.x(
            "INSERT INTO jobs(client, request, status, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
            ("Alpha Store", "brief", "created", 1, 0),
        )
        email_endpoint = f"/api/sites/{job_id}/automations/generate-email"
        social_endpoint = f"/api/sites/{job_id}/automations/generate-social"
        for endpoint, payload in (
            (email_endpoint, {"goal": "x" * 501}),
            (email_endpoint, {"target_audience": "x" * 301}),
            (email_endpoint, {"goal": "offer", "send_now": True}),
            (social_endpoint, {"platform": "arbitrary prompt text"}),
            (social_endpoint, {"theme": "x" * 501}),
            (social_endpoint, {"theme": "Offer", "publish": True}),
        ):
            response = client.post(endpoint, json=payload)
            assert response.status_code == 422


def test_visual_editor_rejects_unbounded_or_active_markup_inputs(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        register(client, "alpha", "long-password-123")
        job_id = db.x(
            "INSERT INTO jobs(client, request, status, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
            ("Alpha Store", "brief", "created", 1, 0),
        )
        endpoint = f"/api/sites/{job_id}/visual-edit"
        valid = client.post(
            endpoint,
            json={
                "brand_name": "متجر ألفا",
                "color_primary": "#123abc",
                "enable_faq": True,
                "enable_reviews": False,
            },
        )
        assert valid.status_code == 200, valid.text
        assert db.one("SELECT brand_name FROM site_settings WHERE job_id=?", (job_id,))["brand_name"] == "متجر ألفا"
        for payload in (
            {"brand_name": "x" * 121},
            {"color_primary": "red; background:url(https://attacker.test)"},
            {"logo_url": "javascript:alert(1)"},
            {"enable_reviews": "true"},
            {"inject_html": "<script>alert(1)</script>"},
        ):
            response = client.post(endpoint, json=payload)
            assert response.status_code == 422


def test_public_order_uses_server_catalog_price_and_waits_for_confirmation(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        job_id = db.x(
            "INSERT INTO jobs(client, request, status, created_at) VALUES (?, ?, ?, ?)",
            ("Alpha Store", "brief", "created", 0),
        )
        item_id = db.x(
            "INSERT INTO site_items(job_id, title, price, created_at) VALUES (?, ?, ?, ?)",
            (job_id, "Trusted item", 49.95, 0),
        )
        response = client.post(
            f"/api/sites/{job_id}/orders",
            headers={"idempotency-key": "public-order-unique-0001"},
            json={
                "customer_name": "Test Customer",
                "customer_phone": "01000000000",
                "customer_address": "Cairo",
                "payment_method": "fawry",
                "total_egp": 0.01,
                "items": [{"id": item_id, "title": "forged", "price": 0.01, "quantity": 2}],
            },
        )
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["total_egp"] == 99.9
        assert payload["status"] == "pending_confirmation"
        assert payload["payment_processed"] is False
        stored = db.one("SELECT items_json, total_egp, status FROM site_orders WHERE id=?", (payload["order_id"],))
        assert stored["total_egp"] == 99.9
        assert stored["status"] == "pending_confirmation"
        assert json.loads(stored["items_json"])[0]["unit_price"] == 49.95
        repeated = client.post(
            f"/api/sites/{job_id}/orders",
            headers={"idempotency-key": "public-order-unique-0001"},
            json={
                "customer_name": "Test Customer",
                "customer_phone": "01000000000",
                "customer_address": "Cairo",
                "payment_method": "fawry",
                "total_egp": 0.01,
                "items": [{"id": item_id, "title": "forged", "price": 0.01, "quantity": 2}],
            },
        )
        assert repeated.status_code == 200, repeated.text
        assert repeated.json()["duplicate"] is True
        assert db.one("SELECT count(*) AS count FROM site_orders")["count"] == 1
        stored_key = db.one(
            "SELECT idempotency_key, request_hash FROM site_orders WHERE id=?",
            (payload["order_id"],),
        )
        assert stored_key["idempotency_key"] == "public-order-unique-0001"
        assert len(stored_key["request_hash"]) == 64
        assert db.one(
            "SELECT count(*) AS count FROM idempotency_records WHERE scope=?",
            (f"public-order:{job_id}",),
        )["count"] == 0
        changed_payload = client.post(
            f"/api/sites/{job_id}/orders",
            headers={"idempotency-key": "public-order-unique-0001"},
            json={
                "customer_name": "Different Customer",
                "customer_phone": "01000000000",
                "customer_address": "Cairo",
                "payment_method": "fawry",
                "total_egp": 0.01,
                "items": [{"id": item_id, "title": "forged", "price": 0.01, "quantity": 2}],
            },
        )
        assert changed_payload.status_code == 409
        assert db.one("SELECT count(*) AS count FROM site_orders")["count"] == 1


def test_service_quote_request_has_no_untrusted_price(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        job_id = db.x(
            "INSERT INTO jobs(client, request, status, created_at) VALUES (?, ?, ?, ?)",
            ("Alpha Studio", "brief", "created", 0),
        )
        response = client.post(
            f"/api/sites/{job_id}/orders",
            headers={"idempotency-key": "service-quote-unique-0001"},
            json={
                "customer_name": "Test Customer",
                "customer_phone": "01000000000",
                "customer_address": "Cairo",
                "payment_method": "contract_invoice",
                "total_egp": 999999,
                "items": [{"title": "Website consultation", "price": 999999, "quantity": 5}],
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["quote_required"] is True
        assert response.json()["total_egp"] == 0.0
        stored = db.one("SELECT total_egp, status FROM site_orders WHERE id=?", (response.json()["order_id"],))
        assert stored == {"total_egp": 0.0, "status": "pending_confirmation"}


def test_public_order_schema_rejects_unbounded_or_malformed_fields(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    job_id = db.x(
        "INSERT INTO jobs(client, request, status, created_at) VALUES (?, ?, ?, ?)",
        ("Alpha Store", "brief", "created", 0),
    )
    invalid_requests = [
        {"customer_name": {}, "customer_phone": "01000000000", "items": [{"id": 1, "quantity": 1}]},
        {"customer_name": "Valid name", "customer_phone": "01000000000", "items": [{"id": 1, "quantity": 0}]},
        {"customer_name": "Valid name", "customer_phone": "01000000000", "items": [{"id": 1, "quantity": 1, "unexpected": True}]},
        {"customer_name": "Valid name", "customer_phone": "01000000000", "items": [{"id": 1, "quantity": 1}], "unexpected": True},
        {"customer_name": "Valid name", "customer_phone": "01000000000", "items": [{"id": True, "quantity": 1}]},
        {"customer_name": "Valid name", "customer_phone": "01000000000", "items": [{"id": 1, "quantity": True}]},
    ]

    with TestClient(app) as client:
        for index, payload in enumerate(invalid_requests):
            response = client.post(
                f"/api/sites/{job_id}/orders",
                headers={"idempotency-key": f"bad-order-schema-{index:02d}"},
                json=payload,
            )
            assert response.status_code == 422

    assert db.one("SELECT count(*) AS count FROM site_orders") == {"count": 0}


def test_streamed_request_body_limit_rejects_chunked_payloads_before_order_creation(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    job_id = db.x(
        "INSERT INTO jobs(client, request, status, created_at) VALUES (?, ?, ?, ?)",
        ("Alpha Store", "brief", "created", 0),
    )

    def oversized_chunks():
        yield b"{" + b" " * (MAX_REQUEST_BODY_BYTES - 1)
        yield b" "

    with TestClient(app) as client:
        response = client.post(
            f"/api/sites/{job_id}/orders",
            headers={
                "idempotency-key": "oversized-streamed-order-0001",
                "content-type": "application/json",
            },
            content=oversized_chunks(),
        )

    assert response.status_code == 413, response.text
    assert response.json()["error"]["code"] == "request_body_too_large"
    assert db.one("SELECT count(*) AS count FROM site_orders") == {"count": 0}


def test_public_site_info_never_exposes_payment_configuration(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    monkeypatch.setenv("VODAFONE_CASH_WALLET", "sensitive-wallet")
    monkeypatch.setenv("FAWRY_MERCHANT_CODE", "sensitive-merchant-code")
    monkeypatch.setenv("INSTAPAY_ADDRESS", "sensitive-instapay")
    job_id = db.x(
        "INSERT INTO jobs(client, request, status, created_at) VALUES (?, ?, ?, ?)",
        ("Alpha Store", "brief", "created", 0),
    )
    with TestClient(app) as client:
        response = client.get(f"/api/sites/{job_id}/info")
    assert response.status_code == 200
    payload = response.json()
    assert payload["payment_processing"] == {
        "enabled": False,
        "status": "pending_verified_gateway_integration",
    }
    assert "payment_gateways" not in payload
    assert "sensitive-wallet" not in response.text
    assert "sensitive-merchant-code" not in response.text
    assert "sensitive-instapay" not in response.text


def test_auth_me_resolves_session_from_cookie_header_or_request_cookies(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        response = register(client, "cookieuser", "long-password-1234")
        assert response.status_code == 200
        # Call /api/auth/me without any x-user-token or authorization header, relying solely on cookie
        me_resp = client.get("/api/auth/me")
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["authenticated"] is True
        assert me_data["user"]["username"] == "cookieuser"

        # Also verify jobs listing endpoint resolves user via cookie
        jobs_resp = client.get("/api/jobs")
        assert jobs_resp.status_code == 200
        assert isinstance(jobs_resp.json(), list)

        # Logout with cookie clears session
        logout_resp = client.post("/api/auth/logout")
        assert logout_resp.status_code == 200
        assert logout_resp.json()["ok"] is True

        # After logout, /api/auth/me returns unauthenticated
        me_after = client.get("/api/auth/me")
        assert me_after.status_code == 200
        assert me_after.json()["authenticated"] is False


def test_enterprise_website_builder_skill_and_dashboard_parity():
    import filecmp
    from app import skills

    # Verify static/index.html and api/static/index.html are byte-for-byte identical
    assert filecmp.cmp("static/index.html", "api/static/index.html", shallow=False)

    # Verify enterprise-website-builder skill is loaded
    all_skills = skills.load()
    builder_skill = next((s for s in all_skills if s["file"] == "enterprise-website-builder.md"), None)
    assert builder_skill is not None, "enterprise-website-builder.md must be present in skills directory"
    assert "*" in builder_skill["meta"].get("roles", [])

    # Verify text is injected for engineering and security agents
    sec_txt, sec_tools = skills.for_agent("Cybersecurity Reviewer", "security")
    assert "enterprise-website-builder" in sec_txt
    assert "calc" in sec_tools

    dev_txt, dev_tools = skills.for_agent("Full-Stack Developer", "engineering")
    assert "enterprise-website-builder" in dev_txt


def test_deep_learning_security_audit_and_remediation_loop(monkeypatch, tmp_path):
    import asyncio
    from app import security

    # 1. Vulnerable HTML snippet
    vulnerable_html = """<!doctype html><html lang="ar" dir="rtl"><head><title>Test</title></head>
    <body>
      <div id="out"></div>
      <a href="https://example.com" target="_blank">External</a>
      <script>
        const data = location.hash;
        document.getElementById('out').innerHTML = data + '<p>' + user_input + '</p>';
        eval("console.log('insecure')");
      </script>
    </body></html>"""

    # Run deep learning security audit
    report = asyncio.run(security.deep_learning_security_audit(vulnerable_html))
    assert report["status"] == "REMEDIATION_REQUIRED"
    assert report["score"] < 90
    assert any(v["type"] == "DOM_XSS" for v in report["vulnerabilities"])
    assert any(v["type"] == "ARBITRARY_CODE_EXECUTION" for v in report["vulnerabilities"])
    assert "DOM_XSS" in report["actionable_feedback"]

    # 2. Hardened HTML snippet
    hardened_html = """<!doctype html><html lang="ar" dir="rtl"><head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Safe Site</title></head>
    <body>
      <div id="out"></div>
      <a href="https://example.com" target="_blank" rel="noopener noreferrer">External</a>
      <script>
        function esc(s) { return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
        document.getElementById('out').textContent = 'Safe Content';
      </script>
    </body></html>"""

    safe_report = asyncio.run(security.deep_learning_security_audit(hardened_html))
    assert safe_report["status"] == "APPROVED"
    assert safe_report["score"] >= 90
    assert len(safe_report["vulnerabilities"]) == 0


def test_security_filter_middleware_blocks_malicious_query_and_injects_headers(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    with TestClient(app) as client:
        # Normal call passes and receives security headers
        resp = client.get("/api/healthz")
        assert resp.status_code == 200
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "DENY"
        assert resp.headers.get("X-XSS-Protection") == "1; mode=block"

        # SQL Injection attempt in query param is blocked with 400
        sqli_resp = client.get("/api/healthz?probe=1'%20UNION%20SELECT%20*%20FROM%20users--")
        assert sqli_resp.status_code == 400
        assert sqli_resp.json()["code"] == "security_filter_violation"

        # XSS script injection in query param is blocked with 400
        xss_resp = client.get("/api/healthz?search=<script>alert(1)</script>")
        assert xss_resp.status_code == 400
        assert xss_resp.json()["code"] == "security_filter_violation"


def test_builder_calm_neon_palettes():
    from app.builder import PALETTES

    for key, pal in PALETTES.items():
        assert "neon_accent" in pal, f"Palette {key} must define neon_accent"
        assert "neon_glow" in pal, f"Palette {key} must define neon_glow"
        assert pal["bg_light"].startswith("#"), f"Palette {key} bg_light must be a valid hex color"
        # Ensure base colors are calm and eye-friendly
        assert pal["primary"].startswith("#")


def test_cookie_session_store_creation_without_bearer_header(monkeypatch, tmp_path):
    configure_test_database(monkeypatch, tmp_path)
    monkeypatch.setattr(corp, "spawn", lambda task: task.close())
    with TestClient(app) as client:
        # 1. Register a user
        reg_resp = client.post(
            "/api/auth/register",
            json={"username": "store_owner", "password": "StrongPassword123!", "phone": "01000000000"},
        )
        assert reg_resp.status_code == 200
        assert "autocorp_session" in client.cookies

        # 2. Check /api/auth/me relying purely on cookie
        me_resp = client.get("/api/auth/me")
        assert me_resp.status_code == 200
        assert me_resp.json()["authenticated"] is True
        assert me_resp.json()["user"]["username"] == "store_owner"

        # 3. Create a store using POST /api/jobs with cookie session, explicitly with empty x-user-token header
        job_resp = client.post(
            "/api/jobs",
            headers={"x-user-token": "", "Idempotency-Key": "test-idem-key-12345678"},
            json={
                "brand_name": "متجر الخضار الطازج",
                "category": "خضار وفواكه طازجة",
                "slogan": "من الغيط للبيت",
                "request": "متجر لبيع الخضار والفواكه الطازجة مع توصيل سريع",
            },
        )
        assert job_resp.status_code == 200
        jid = job_resp.json()["id"]
        assert jid > 0

        # 4. Verify in DB that job was created with correct user_id
        job = db.one("SELECT * FROM jobs WHERE id = ?", (jid,))
        assert job is not None
        assert job["user_id"] == reg_resp.json()["user"]["id"]

        # 5. Verify GET /api/jobs with cookie returns the user's store
        jobs_resp = client.get("/api/jobs", headers={"x-user-token": ""})
        assert jobs_resp.status_code == 200
        user_jobs = jobs_resp.json()
        assert len(user_jobs) == 1
        assert user_jobs[0]["id"] == jid


def test_portfolio_multi_track_specialization_and_prepositions():
    from app.main import extract_smart_brand

    # AI Engineer track with Arabic preposition "للفاروق"
    ai_prompt = "عايز اعمل بورتفوليو للفاروق ابراهيم مهندس AI"
    ai_niche = builder.detect_niche(ai_prompt)
    ai_brand = extract_smart_brand(ai_prompt, ai_niche)
    assert ai_brand == "الفاروق ابراهيم | مهندس ذكاء اصطناعي | AI Engineer"
    ai_track = builder.detect_portfolio_track(ai_prompt + " " + ai_brand)
    assert ai_track == "ai"
    ai_catalog = builder.get_default_catalog(ai_niche, ai_prompt + " " + ai_brand)
    assert len(ai_catalog) >= 4
    ai_html = builder.build_site_html(901, ai_brand, ai_prompt, settings={"brand_name": ai_brand}, items=[])
    assert "AI & DEEP LEARNING ENGINEER" in ai_html
    assert "TensorFlow Certified Developer" in ai_html
    assert "Autonomous Agents & LLMs" in ai_html
    assert "togglePortfolioLang" in ai_html

    # Software Engineer track with preposition "لأحمد"
    dev_prompt = "عايز بورتفوليو لأحمد محمود مهندس برمجيات"
    dev_niche = builder.detect_niche(dev_prompt)
    dev_brand = extract_smart_brand(dev_prompt, dev_niche)
    assert "أحمد محمود" in dev_brand and "Software Engineer" in dev_brand
    dev_track = builder.detect_portfolio_track(dev_prompt + " " + dev_brand)
    assert dev_track == "dev"
    dev_html = builder.build_site_html(902, dev_brand, dev_prompt, settings={"brand_name": dev_brand}, items=[])
    assert "Full-Stack Web Development" in dev_html
    assert "AWS Certified Solutions Architect" in dev_html

    # Cybersecurity track with preposition "لياسين"
    cyber_prompt = "عايز بورتفوليو لياسين احمد في السايبر سيكيورتي"
    cyber_niche = builder.detect_niche(cyber_prompt)
    cyber_brand = extract_smart_brand(cyber_prompt, cyber_niche)
    assert "ياسين احمد" in cyber_brand and "Cybersecurity" in cyber_brand
    cyber_track = builder.detect_portfolio_track(cyber_prompt + " " + cyber_brand)
    assert cyber_track == "cyber"
    cyber_html = builder.build_site_html(903, cyber_brand, cyber_prompt, settings={"brand_name": cyber_brand}, items=[])
    assert "Penetration Testing" in cyber_html
    assert "OSCP Certified" in cyber_html



