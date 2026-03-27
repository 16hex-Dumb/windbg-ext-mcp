#!/usr/bin/env python3
"""
Bootstrap launcher for the WinDbg MCP server.

This script keeps client configuration stable while resolving the actual Python
runtime from the local project environment. It allows MCP clients to start the
server without shelling out through `poetry run`.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
SERVER_SCRIPT = REPO_ROOT / "mcp_server" / "server.py"
PROBE_SNIPPET = (
    "import runpy, sys; "
    f"sys.path.insert(0, {str(SERVER_SCRIPT.parent)!r}); "
    f"runpy.run_path({str(SERVER_SCRIPT)!r}, run_name='__windbg_probe__')"
)


def _is_usable_python(python_executable: str | None) -> bool:
    if not python_executable:
        return False

    candidate = Path(python_executable)
    if not candidate.exists():
        return False

    try:
        result = subprocess.run(
            [str(candidate), "-c", PROBE_SNIPPET],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False

    return result.returncode == 0


def _poetry_python() -> str | None:
    poetry_command = shutil.which("poetry")
    if not poetry_command:
        return None

    try:
        result = subprocess.run(
            [poetry_command, "env", "info", "--executable"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if result.returncode != 0:
        return None

    executable = result.stdout.strip()
    return executable or None


def resolve_python() -> str:
    candidates = []

    env_override = os.environ.get("WINDBG_MCP_PYTHON")
    if env_override:
        candidates.append(env_override)

    candidates.append(sys.executable)

    if os.name == "nt":
        candidates.append(str(REPO_ROOT / ".venv" / "Scripts" / "python.exe"))
    else:
        candidates.append(str(REPO_ROOT / ".venv" / "bin" / "python"))

    poetry_python = _poetry_python()
    if poetry_python:
        candidates.append(poetry_python)

    seen: set[str] = set()
    for candidate in candidates:
        if not candidate:
            continue
        normalized = str(Path(candidate))
        if normalized in seen:
            continue
        seen.add(normalized)
        if _is_usable_python(normalized):
            return normalized

    raise RuntimeError(
        "Could not find a Python environment that can import the WinDbg MCP server. "
        "Install dependencies with `poetry install` or create a local `.venv` first."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--check", action="store_true", help="Validate runtime resolution and exit")
    parser.add_argument("--resolve-python", action="store_true", help="Print the resolved runtime and exit")
    args, forwarded = parser.parse_known_args(argv)

    try:
        resolved_python = resolve_python()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.resolve_python:
        print(resolved_python)
        return 0

    if args.check:
        print(f"Resolved runtime: {resolved_python}")
        return 0

    os.chdir(REPO_ROOT)
    os.execv(resolved_python, [resolved_python, str(SERVER_SCRIPT), *forwarded])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
