import os
from pathlib import Path

import importlib


def test_install_uninstall_dry_run(tmp_path: Path, monkeypatch):
    # Import the script as a module
    ic = importlib.import_module("install_client_config")

    cfg_path = tmp_path / "mcp.json"

    # Ensure nothing exists
    if cfg_path.exists():
        cfg_path.unlink()

    # Dry-run install should return True and not create the file
    ok = ic.install_windbg_mcp(str(cfg_path), quiet=False, dry_run=True)
    assert ok is True
    assert not cfg_path.exists()

    # Dry-run uninstall should also return True and not fail
    ok = ic.uninstall_windbg_mcp(str(cfg_path), quiet=False, dry_run=True)
    assert ok is True


def test_installed_config_uses_resolved_runtime(tmp_path: Path):
    ic = importlib.import_module("install_client_config")

    cfg_path = tmp_path / "mcp.json"
    ok = ic.install_windbg_mcp(str(cfg_path), quiet=True, dry_run=False)
    assert ok is True

    payload = ic.read_json_config(str(cfg_path))
    server_cfg = payload["mcpServers"]["windbg-mcp"]

    assert server_cfg["command"].endswith("python.exe") or server_cfg["command"].endswith("python")
    assert server_cfg["args"][0].endswith("mcp_server\\server.py") or server_cfg["args"][0].endswith("mcp_server/server.py")

