import struct
import time
from pathlib import Path

from app import create_app
from app.config.testing import TestingConfig


def test_cleanup_removes_only_expired_sessions(tmp_path, monkeypatch):
    monkeypatch.setattr(TestingConfig, "SESSION_FILE_DIR", str(tmp_path))
    app = create_app("testing")
    cache = app.session_interface.cache
    cache.set("expired", {"user_id": 1}, timeout=60)
    cache.set("active", {"user_id": 2}, timeout=60)
    cache.set("no-expiration", {"user_id": 3}, timeout=0)
    expired_path = Path(cache._get_filename("expired"))
    with expired_path.open("r+b") as session_file:
        session_file.write(struct.pack("I", int(time.time()) - 1))
    unrelated = tmp_path / "notes.txt"
    unrelated.write_text("keep")

    runner = app.test_cli_runner()
    missing_confirmation = runner.invoke(args=["cleanup-expired-sessions"])
    assert missing_confirmation.exit_code != 0
    assert expired_path.exists()

    result = runner.invoke(args=["cleanup-expired-sessions", "--confirm-stopped"])
    assert result.exit_code == 0, result.output
    assert "Removed 1 expired session file(s)." in result.output
    assert not expired_path.exists()
    assert cache.get("active") == {"user_id": 2}
    assert cache.get("no-expiration") == {"user_id": 3}
    assert unrelated.exists()


def test_cleanup_reports_invalid_session_file(tmp_path, monkeypatch):
    monkeypatch.setattr(TestingConfig, "SESSION_FILE_DIR", str(tmp_path))
    app = create_app("testing")
    invalid = tmp_path / ("a" * 32)
    invalid.write_bytes(b"x")

    result = app.test_cli_runner().invoke(
        args=["cleanup-expired-sessions", "--confirm-stopped"]
    )

    assert result.exit_code != 0
    assert "Invalid session file header" in result.output
    assert invalid.exists()


def test_active_sessions_are_not_evicted_at_old_threshold(tmp_path, monkeypatch):
    monkeypatch.setattr(TestingConfig, "SESSION_FILE_DIR", str(tmp_path))
    app = create_app("testing")
    cache = app.session_interface.cache
    for index in range(502):
        assert cache.set(f"session-{index}", {"user_id": index}, timeout=60)

    assert cache.get("session-0") == {"user_id": 0}
    assert cache.get("session-501") == {"user_id": 501}
