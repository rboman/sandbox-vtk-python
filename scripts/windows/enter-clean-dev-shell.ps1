[CmdletBinding()]
param(
    [string]$Target = "",
    [string]$Command = "",
    [switch]$NoSpawn
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..\..")

$UnsafeVars = @(
    "PYTHONPATH",
    "PYTHONHOME",
    "PYTHONSTARTUP",
    "VIRTUAL_ENV",
    "PIP_INDEX_URL",
    "PIP_EXTRA_INDEX_URL",
    "PIP_FIND_LINKS",
    "PIP_CONSTRAINT",
    "PIP_REQUIRE_VIRTUALENV",
    "CMAKE_PREFIX_PATH",
    "VTK_DIR",
    "CMAKE_TOOLCHAIN_FILE",
    "INCLUDE",
    "LIB",
    "LIBRARY_PATH",
    "CPATH",
    "LD_LIBRARY_PATH",
    "DYLD_LIBRARY_PATH",
    "CONDA_PREFIX",
    "CONDA_DEFAULT_ENV"
)

function Get-SanitizedPath {
    $entries = @()
    $systemRoots = @(
        (Join-Path $env:SystemRoot "System32"),
        (Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0"),
        $env:SystemRoot
    )

    foreach ($entry in $systemRoots + ($env:PATH -split ';')) {
        if ([string]::IsNullOrWhiteSpace($entry)) {
            continue
        }

        $trimmed = $entry.Trim()
        $lower = $trimmed.ToLowerInvariant()

        if ($lower -match "vtk" -or
            $lower -match "site-packages" -or
            $lower -match "\\.venv" -or
            $lower -match "\\.venvs" -or
            $lower -match "conda") {
            continue
        }

        if (-not ($entries -contains $trimmed)) {
            $entries += $trimmed
        }
    }

    return ($entries -join ';')
}

foreach ($name in $UnsafeVars) {
    Remove-Item "Env:$name" -ErrorAction SilentlyContinue
}

$env:PYTHONNOUSERSITE = "1"
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
$env:SANDBOX_VTK_PYTHON_REPO_ROOT = $RepoRoot.Path
$env:PATH = Get-SanitizedPath

if ($Target) {
    $env:SANDBOX_VTK_PYTHON_TARGET = $Target
}

Write-Host "Prepared sanitized environment for sandbox-vtk-python"
Write-Host "Repo root: $($RepoRoot.Path)"
if ($Target) {
    Write-Host "Target: $Target"
}
Write-Host "PYTHONNOUSERSITE=1"

if ($NoSpawn) {
    return
}

if ($Command) {
    & powershell.exe -NoLogo -NoProfile -Command $Command
    exit $LASTEXITCODE
}

& powershell.exe -NoLogo -NoProfile
exit $LASTEXITCODE
