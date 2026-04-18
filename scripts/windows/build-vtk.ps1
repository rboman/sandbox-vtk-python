[CmdletBinding()]
param(
    [string]$Target = "win-amd64-msvc2022-py310-release",
    [string]$PythonExe = "",
    [string]$Generator = "Visual Studio 17 2022",
    [string]$Architecture = "x64"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..\..")

if (-not $PythonExe) {
    $PythonExe = "python"
}

$VenvDir = Join-Path $RepoRoot ".venvs\$Target"
$VtkSourceDir = Join-Path $RepoRoot "external\src\vtk-9.3.1"
$BuildDir = Join-Path $RepoRoot "external\build\vtk-9.3.1\$Target"
$InstallDir = Join-Path $RepoRoot "external\install\vtk-9.3.1\$Target\sdk"
$WheelhouseDir = Join-Path $RepoRoot "external\wheelhouse\vtk-9.3.1\$Target"
$AuditScript = Join-Path $RepoRoot "scripts\validate\audit-environment.py"
$ManifestPath = Join-Path $BuildDir "build-manifest.json"

$ResolvedVenvDir = Resolve-Path $VenvDir -ErrorAction SilentlyContinue
if (-not $ResolvedVenvDir) {
    throw "Target venv does not exist yet: $VenvDir. Run sync-venv first."
}

$ResolvedPython = (Get-Command $PythonExe).Source
if (-not $ResolvedPython.StartsWith($ResolvedVenvDir.Path, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "PythonExe must resolve inside the target venv. Expected under $VenvDir but got $ResolvedPython."
}

New-Item -ItemType Directory -Force -Path $BuildDir, $InstallDir, $WheelhouseDir | Out-Null

& $ResolvedPython $AuditScript --mode strict --target-venv $VenvDir --target-sdk-root $InstallDir

$cmakeArgs = @(
    "-S", $VtkSourceDir,
    "-B", $BuildDir,
    "-G", $Generator,
    "-A", $Architecture,
    "-DCMAKE_BUILD_TYPE=Release",
    "-DCMAKE_INSTALL_PREFIX=$InstallDir",
    "-DVTK_WRAP_PYTHON=ON",
    "-DVTK_WHEEL_BUILD=ON",
    "-DPython3_EXECUTABLE=$ResolvedPython",
    "-DVTK_GROUP_ENABLE_Qt=WANT",
    "-DVTK_MODULE_ENABLE_VTK_GUISupportQtQuick=DONT_WANT",
    "-DVTK_GROUP_ENABLE_Rendering=WANT",
    "-DVTK_GROUP_ENABLE_Views=WANT",
    "-DVTK_GROUP_ENABLE_StandAlone=WANT",
    "-DVTK_MODULE_ENABLE_VTK_RenderingOpenGL2=WANT",
    "-DVTK_MODULE_ENABLE_VTK_InteractionStyle=WANT",
    "-DVTK_MODULE_ENABLE_VTK_RenderingMatplotlib=WANT"
)

& cmake @cmakeArgs
& cmake --build $BuildDir --config Release
& cmake --install $BuildDir --config Release

$setupPy = Join-Path $BuildDir "setup.py"
if (Test-Path $setupPy) {
    Push-Location $BuildDir
    try {
        & $ResolvedPython "setup.py" "bdist_wheel" "--dist-dir" $WheelhouseDir
    }
    finally {
        Pop-Location
    }
}

$manifest = [ordered]@{
    target = $Target
    python_executable = $ResolvedPython
    vtk_source_dir = $VtkSourceDir
    build_dir = $BuildDir
    install_dir = $InstallDir
    wheelhouse_dir = $WheelhouseDir
    generator = $Generator
    architecture = $Architecture
    vtk_version = "9.3.1"
}

$manifest | ConvertTo-Json -Depth 4 | Set-Content -Path $ManifestPath -Encoding UTF8
Write-Host "Wrote manifest to $ManifestPath"
