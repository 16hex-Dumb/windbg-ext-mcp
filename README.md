# WinDbg-ext-MCP

WinDbg extension plus Python MCP server.

It lets MCP clients drive WinDbg over stdio while the extension talks to WinDbg over `\\.\pipe\windbgmcp`.

Tested flow in this repo:
- load the extension into WinDbg / WinDbgX
- let the extension host the named pipe server
- let the Python MCP server expose tools to MCP clients

## Quick Start

Prereqs
- Windows 10/11
- WinDbg or WinDbgX
- Visual Studio Build Tools with C++
- Python 3.10+
- Poetry 2.x

Build the extension from the repo root:

```powershell
msbuild extension\windbgmcpExt.sln /p:Configuration=Release /p:Platform=x64
```

Recommended daily-use launch:

```powershell
powershell -ExecutionPolicy Bypass -File .\launch_windbg_with_mcp.ps1
```

This script prefers `WinDbgX.exe` and auto-loads the built DLL.

Manual fallback inside WinDbg:

```text
.load D:\path\to\windbgmcpExt.dll
```

After `.load`, the extension starts the pipe server automatically. `mcpstart` is only a fallback command if you need to restart it manually.

Install Python dependencies and write MCP client config:

```powershell
poetry install
python install_client_config.py --install
```

Sanity check:

```powershell
python install_client_config.py --test
poetry run selftest
```

## How It Works

```text
MCP Client (stdio) <-> Python MCP Server (stdio) <-> WinDbg Extension (named pipe) <-> WinDbg / target
```

- `extension/` contains the C++ WinDbg extension DLL.
- `mcp_server/` contains the FastMCP server and tool implementations.
- `install_client_config.py` writes client config for supported desktop clients.
- `launch_windbg_with_mcp.ps1` starts WinDbg / WinDbgX and preloads the extension.
- `mcp_server_launcher.py` resolves a usable Python runtime and is mainly for diagnostics.

## Daily Use

Typical workflow:

1. Build the DLL once after code changes.
2. Run `python install_client_config.py --install` once per machine or when the Python environment changes.
3. Start WinDbg with `launch_windbg_with_mcp.ps1`.
4. Restart your MCP client.
5. Call `debug_session(action="status")` or `connection_manager(action="status")`.

## Supported MCP Clients

`install_client_config.py` currently writes config for:
- Cursor
- Claude Desktop
- VS Code Cline
- VS Code Roo Code
- Windsurf

Commands:

```powershell
python install_client_config.py --install --dry-run
python install_client_config.py --install
python install_client_config.py --uninstall
python install_client_config.py --test
```

What the installer writes:
- the resolved Python interpreter from the project environment
- the direct server entrypoint `mcp_server/server.py`
- stdio transport settings

It does not write `poetry run mcp` into client config.

## Codex Manual Config

Codex uses `~/.codex/config.toml`. Add a `stdio` server entry that points directly to the resolved Python runtime and `mcp_server/server.py`.

First resolve the runtime:

```powershell
python .\mcp_server_launcher.py --resolve-python
```

Then add an entry like this:

```toml
[mcp_servers.windbg-mcp]
type = "stdio"
command = "C:\\path\\to\\python.exe"
args = [
    "D:\\path\\to\\windbg-ext-mcp\\mcp_server\\server.py",
]
```

Do not point Codex at `poetry run`.
Do not point Codex at `mcp_server_launcher.py` for production use.
Point it at the resolved interpreter plus `mcp_server/server.py`.

After editing `~/.codex/config.toml`, fully restart Codex so the MCP server is reloaded.

## Manual Server Runs

Useful commands while developing:

```powershell
python .\mcp_server_launcher.py --check
python .\mcp_server_launcher.py --resolve-python
poetry run mcp --list-tools
poetry run mcp
```

The launcher is useful for verifying environment resolution.
The actual client config should still point to `python.exe + mcp_server/server.py`.

## Available Tools

- `debug_session`
- `connection_manager`
- `session_manager`
- `run_command`
- `run_sequence`
- `breakpoint_and_continue`
- `analyze_process`
- `analyze_thread`
- `analyze_memory`
- `analyze_kernel`
- `performance_manager`
- `async_manager`
- `troubleshoot`
- `get_help`
- `test_windbg_communication`
- `network_debugging_troubleshoot`

## WinDbg Commands Exported By The DLL

- `help`
- `hello`
- `objecttypes`
- `mcpstart`
- `mcpstop`
- `mcpstatus`

## Troubleshooting

Extension does not load:
- make sure WinDbg and the DLL are both x64
- make sure the DLL path is correct
- if linking fails, install Debugging Tools for Windows from the Windows SDK

MCP client cannot connect:
- confirm the extension is loaded in WinDbg
- run `mcpstatus` in WinDbg
- confirm `\\.\pipe\windbgmcp` exists
- restart the MCP client after config changes

Codex still cannot see the server:
- verify `~/.codex/config.toml`
- make sure it points to the current Python environment and `mcp_server/server.py`
- fully restart Codex, not just the chat thread

`WinDbgX.exe` path issues:
- `launch_windbg_with_mcp.ps1` prefers `WinDbgX.exe`
- if WindowsApps argument forwarding breaks because your DLL path contains spaces, use `-WinDbgPath` to point at a classic `windbg.exe` install or move the repo to a path without spaces

## Tested Notes

Observed working behavior in this repo:
- loading the extension creates the named pipe without an extra `mcpstart`
- direct stdio config using resolved `python.exe` plus `mcp_server/server.py` works reliably
- using a shell wrapper such as `poetry run` in MCP client config is less reliable and not recommended

## Repository Layout

- `extension/`: C++ WinDbg extension project
- `mcp_server/`: FastMCP server and tool modules
- `install_client_config.py`: MCP desktop client config installer
- `launch_windbg_with_mcp.ps1`: WinDbg / WinDbgX launcher
- `mcp_server_launcher.py`: runtime resolver and diagnostics helper
- `mcp_server/tests/`: pytest coverage for server helpers

## License

See `LICENSE`.
