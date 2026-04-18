[CmdletBinding()]
param(
    [string]$Target = "win-amd64-msvc2022-py310-release",
    [string]$PythonExe = "python",
    [string]$ConstraintsFile = "",
    [switch]$NoIndex
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..\..")

if (-not $ConstraintsFile) {
    $ConstraintsFile = Join-Path $RepoRoot "constraints\py310.txt"
}

$VenvDir = Join-Path $RepoRoot ".venvs\$Target"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$WheelhouseDir = Join-Path $RepoRoot "external\wheelhouse\vtk-9.3.1\$Target"
$AuditScript = Join-Path $RepoRoot "scripts\validate\audit-environment.py"

if (-not (Test-Path $VenvPython)) {
    & $PythonExe -m venv $VenvDir
}

& $VenvPython $AuditScript --mode strict --target-venv $VenvDir

$vtkArgs = @(
    "-m", "pip", "install",
    "--no-deps",
    "--no-index",
    "--find-links", $WheelhouseDir,
    "vtk==9.3.1"
)

& $VenvPython @vtkArgs

$pyvistaArgs = @(
    "-m", "pip", "install",
    "--constraint", $ConstraintsFile,
    "pyvista"
)

if ($NoIndex) {
    $pyvistaArgs = @(
        "-m", "pip", "install",
        "--no-index",
        "--find-links", $WheelhouseDir,
        "--constraint", $ConstraintsFile,
        "pyvista"
    )
}

& $VenvPython @pyvistaArgs
& $VenvPython -m pip install (Join-Path $RepoRoot "packages\codecpp")
& $VenvPython -m pip install -e (Join-Path $RepoRoot "packages\codepy")
& $VenvPython -m pip install -e (Join-Path $RepoRoot "packages\pmanager")
