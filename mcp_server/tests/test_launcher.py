from pathlib import Path

import mcp_server_launcher as launcher


def test_resolve_python_prefers_env_override(monkeypatch):
    monkeypatch.setenv("WINDBG_MCP_PYTHON", "C:\\custom\\python.exe")
    monkeypatch.setattr(launcher.sys, "executable", "C:\\current\\python.exe")
    monkeypatch.setattr(launcher, "_poetry_python", lambda: None)
    monkeypatch.setattr(launcher, "_is_usable_python", lambda candidate: candidate == "C:\\custom\\python.exe")

    assert launcher.resolve_python() == "C:\\custom\\python.exe"


def test_main_resolve_python_prints_value(monkeypatch, capsys):
    monkeypatch.setattr(launcher, "resolve_python", lambda: "C:\\resolved\\python.exe")

    exit_code = launcher.main(["--resolve-python"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == "C:\\resolved\\python.exe"


def test_main_check_prints_runtime(monkeypatch, capsys):
    monkeypatch.setattr(launcher, "resolve_python", lambda: "C:\\resolved\\python.exe")

    exit_code = launcher.main(["--check"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "C:\\resolved\\python.exe" in captured.out


def test_main_execs_server(monkeypatch):
    monkeypatch.setattr(launcher, "resolve_python", lambda: "C:\\resolved\\python.exe")

    observed = {}

    def fake_chdir(path):
        observed["cwd"] = path

    def fake_execv(executable, argv):
        observed["executable"] = executable
        observed["argv"] = argv
        raise SystemExit(0)

    monkeypatch.setattr(launcher.os, "chdir", fake_chdir)
    monkeypatch.setattr(launcher.os, "execv", fake_execv)

    try:
        launcher.main(["--list-tools"])
    except SystemExit as exc:
        assert exc.code == 0

    assert observed["executable"] == "C:\\resolved\\python.exe"
    assert observed["argv"][1].endswith("mcp_server\\server.py")
    assert observed["argv"][2:] == ["--list-tools"]


def test_server_script_exists():
    assert Path(launcher.SERVER_SCRIPT).exists()
