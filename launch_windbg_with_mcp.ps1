param(
    [string]$WinDbgPath,
    [string]$ExtensionPath,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$WinDbgArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Resolve-CandidatePath {
    param([string[]]$Candidates)

    foreach ($candidate in $Candidates) {
        if (-not [string]::IsNullOrWhiteSpace($candidate) -and (Test-Path -LiteralPath $candidate)) {
            return (Resolve-Path -LiteralPath $candidate).Path
        }
    }

    return $null
}

function Find-WinDbg {
    param([string]$PreferredPath)

    if ($PreferredPath) {
        return (Resolve-Path -LiteralPath $PreferredPath).Path
    }

    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps\WinDbgX.exe"),
        (Join-Path $env:ProgramFiles "Windows Kits\10\Debuggers\x64\WinDbgX.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Windows Kits\10\Debuggers\x64\WinDbgX.exe"),
        (Join-Path $env:ProgramFiles "Windows Kits\10\Debuggers\x64\windbg.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Windows Kits\10\Debuggers\x64\windbg.exe")
    )

    $resolved = Resolve-CandidatePath -Candidates $candidates
    if ($resolved) {
        return $resolved
    }

    $windbgXOnPath = Get-Command WinDbgX.exe -ErrorAction SilentlyContinue
    if ($windbgXOnPath) {
        return $windbgXOnPath.Source
    }

    $windbgOnPath = Get-Command windbg.exe -ErrorAction SilentlyContinue
    if ($windbgOnPath) {
        return $windbgOnPath.Source
    }

    return $null
}

function Find-ExtensionDll {
    param([string]$PreferredPath)

    if ($PreferredPath) {
        return (Resolve-Path -LiteralPath $PreferredPath).Path
    }

    $candidates = @(
        (Join-Path $repoRoot "extension\build\x64\Release\windbgmcpExt.dll"),
        (Join-Path $repoRoot "extension\build\x64\Debug\windbgmcpExt.dll"),
        (Join-Path $repoRoot "extension\Release\windbgmcpExt.dll"),
        (Join-Path $repoRoot "extension\Debug\windbgmcpExt.dll")
    )

    return Resolve-CandidatePath -Candidates $candidates
}

$resolvedWinDbg = Find-WinDbg -PreferredPath $WinDbgPath
if (-not $resolvedWinDbg) {
    throw "Could not find WinDbg. Pass -WinDbgPath explicitly or install Debugging Tools for Windows."
}

$resolvedDll = Find-ExtensionDll -PreferredPath $ExtensionPath
if (-not $resolvedDll) {
    throw "Could not find windbgmcpExt.dll. Build the extension first or pass -ExtensionPath explicitly."
}

$usesWinDbgAppAlias = $resolvedWinDbg -like "*\WindowsApps\WinDbgX.exe"
if ($usesWinDbgAppAlias -and $resolvedDll.Contains(' ')) {
    throw "WinDbgX.exe from WindowsApps may split quoted -c arguments incorrectly when the DLL path contains spaces. Move the repo to a path without spaces or pass -WinDbgPath to a classic windbg.exe installation."
}

# WinDbgX.exe launched through the WindowsApps alias can mis-handle nested quotes
# inside the `-c` command. Use a plain path here when possible.
$startupCommand = ".load $resolvedDll"

Write-Host "Starting WinDbg:" $resolvedWinDbg
Write-Host "Auto-loading extension:" $resolvedDll
Write-Host "Startup command:" $startupCommand

& $resolvedWinDbg -c $startupCommand @WinDbgArgs
