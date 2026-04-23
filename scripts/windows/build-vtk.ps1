[CmdletBinding()]
param(
    [string]$Target = "win-amd64-msvc2022-py310-release",
    [string]$PythonExe = "",
    [string]$Generator = "",
    [ValidateSet("auto", "ninja", "vs")]
    [string]$BuildBackend = "auto",
    [string]$Architecture = "x64",
    [int]$Parallel = 0
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

function Invoke-External {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$Arguments = @()
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        $renderedArgs = $Arguments -join " "
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $renderedArgs"
    }
}

function Get-CMakeCacheGenerator {
    param([string]$BuildDirPath)

    $cachePath = Join-Path $BuildDirPath "CMakeCache.txt"
    if (-not (Test-Path $cachePath)) {
        return $null
    }

    $line = Select-String -Path $cachePath -Pattern "^CMAKE_GENERATOR:INTERNAL=(.+)$" | Select-Object -First 1
    if (-not $line) {
        return $null
    }

    return $line.Matches[0].Groups[1].Value
}

function Resolve-VsDevCmd {
    if ($env:VS2022INSTALLDIR) {
        $candidate = Join-Path $env:VS2022INSTALLDIR "Common7\Tools\VsDevCmd.bat"
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    $programFilesX86 = [Environment]::GetFolderPath("ProgramFilesX86")
    $vswhere = Join-Path $programFilesX86 "Microsoft Visual Studio\Installer\vswhere.exe"
    if (-not (Test-Path $vswhere)) {
        throw "Unable to locate vswhere.exe. Cannot prepare a Ninja MSVC environment."
    }

    $installPath = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    if (-not $installPath) {
        throw "Unable to locate a Visual Studio installation with C++ tools."
    }

    $candidate = Join-Path $installPath.Trim() "Common7\Tools\VsDevCmd.bat"
    if (-not (Test-Path $candidate)) {
        throw "Unable to locate VsDevCmd.bat under $installPath."
    }

    return $candidate
}

function Import-VsDevEnvironment {
    param(
        [string]$TargetArchitecture
    )

    $vsDevCmd = Resolve-VsDevCmd
    $command = """$vsDevCmd"" -no_logo -arch=$TargetArchitecture -host_arch=$TargetArchitecture >nul && set"
    $output = & cmd.exe /s /c $command
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to initialize Visual Studio build environment through VsDevCmd.bat."
    }

    foreach ($line in $output) {
        if ($line -match "^(.*?)=(.*)$") {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

function Resolve-BuildChoice {
    param(
        [string]$RequestedGenerator,
        [string]$RequestedBackend,
        [string]$ExistingGeneratorName
    )

    if ($RequestedGenerator) {
        if ($RequestedGenerator -match "^Ninja") {
            return @{
                Backend = "ninja"
                Generator = $RequestedGenerator
                NinjaPath = $null
            }
        }

        return @{
            Backend = "vs"
            Generator = $RequestedGenerator
            NinjaPath = $null
        }
    }

    if ($ExistingGeneratorName) {
        if ($ExistingGeneratorName -match "^Ninja") {
            if ($RequestedBackend -eq "vs") {
                throw "Build directory $BuildDir is already configured for $ExistingGeneratorName. Remove it or choose a different target before switching backends."
            }
            return @{
                Backend = "ninja"
                Generator = $ExistingGeneratorName
                NinjaPath = $null
            }
        }

        if ($RequestedBackend -eq "ninja") {
            throw "Build directory $BuildDir is already configured for $ExistingGeneratorName. Remove it or choose a different target before switching backends."
        }

        return @{
            Backend = "vs"
            Generator = $ExistingGeneratorName
            NinjaPath = $null
        }
    }

    if ($RequestedBackend -eq "vs") {
        return @{
            Backend = "vs"
            Generator = "Visual Studio 17 2022"
            NinjaPath = $null
        }
    }

    $ninjaCommand = Get-Command ninja -ErrorAction SilentlyContinue
    if ($RequestedBackend -eq "ninja" -and -not $ninjaCommand) {
        throw "BuildBackend=ninja was requested but 'ninja' was not found in PATH."
    }

    if ($ninjaCommand) {
        return @{
            Backend = "ninja"
            Generator = "Ninja"
            NinjaPath = $ninjaCommand.Source
        }
    }

    return @{
        Backend = "vs"
        Generator = "Visual Studio 17 2022"
        NinjaPath = $null
    }
}

function Ensure-WheelSupport {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonPath
    )

    $probeScript = @"
import sys
import warnings

try:
    from setuptools.command.bdist_wheel import bdist_wheel  # noqa: F401
except Exception:
    try:
        warnings.simplefilter("ignore", FutureWarning)
        import wheel.bdist_wheel  # noqa: F401
    except Exception:
        sys.exit(1)

sys.exit(0)
"@

    try {
        & $PythonPath "-c" $probeScript
        $wheelAvailable = ($LASTEXITCODE -eq 0)
    }
    catch {
        $wheelAvailable = $false
    }

    if ($wheelAvailable) {
        return
    }

    Write-Host "Installing missing 'wheel' package into the target venv..."
    Invoke-External -FilePath $PythonPath -Arguments @("-m", "pip", "install", "wheel")
    Invoke-External -FilePath $PythonPath -Arguments @("-c", $probeScript)
}

$ResolvedVenvDir = Resolve-Path $VenvDir -ErrorAction SilentlyContinue
if (-not $ResolvedVenvDir) {
    throw "Target venv does not exist yet: $VenvDir. Run sync-venv first."
}

$ResolvedPython = (Get-Command $PythonExe).Source
if (-not $ResolvedPython.StartsWith($ResolvedVenvDir.Path, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "PythonExe must resolve inside the target venv. Expected under $VenvDir but got $ResolvedPython."
}

New-Item -ItemType Directory -Force -Path $BuildDir, $InstallDir, $WheelhouseDir | Out-Null

Invoke-External -FilePath $ResolvedPython -Arguments @($AuditScript, "--mode", "strict", "--target-venv", $VenvDir, "--target-sdk-root", $InstallDir)

$ExistingGenerator = Get-CMakeCacheGenerator -BuildDirPath $BuildDir
$BuildChoice = Resolve-BuildChoice -RequestedGenerator $Generator -RequestedBackend $BuildBackend -ExistingGeneratorName $ExistingGenerator
$ResolvedBackend = $BuildChoice.Backend
$ResolvedGenerator = $BuildChoice.Generator
$NinjaPath = $BuildChoice.NinjaPath

if ($ResolvedBackend -eq "ninja") {
    Import-VsDevEnvironment -TargetArchitecture $Architecture
    $clCommand = Get-Command cl -ErrorAction SilentlyContinue
    if (-not $clCommand) {
        throw "Ninja was selected, but 'cl.exe' is still unavailable after VsDevCmd initialization."
    }
}

$Parallelism = $Parallel
if ($Parallelism -le 0) {
    $Parallelism = [Environment]::ProcessorCount
}

$env:CMAKE_BUILD_PARALLEL_LEVEL = "$Parallelism"

$cmakeArgs = @(
    "-S", $VtkSourceDir,
    "-B", $BuildDir,
    "-G", $ResolvedGenerator,
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

if ($ResolvedBackend -eq "vs") {
    $cmakeArgs += @("-A", $Architecture)
}

if ($ResolvedBackend -eq "ninja" -and $NinjaPath) {
    $cmakeArgs += "-DCMAKE_MAKE_PROGRAM=$NinjaPath"
}

Write-Host "Using backend:   $ResolvedBackend"
Write-Host "Using generator: $ResolvedGenerator"
Write-Host "Parallel jobs:   $Parallelism"
if ($ExistingGenerator) {
    Write-Host "Existing build tree generator: $ExistingGenerator"
}

Invoke-External -FilePath "cmake" -Arguments $cmakeArgs

$buildArgs = @("--build", $BuildDir, "--parallel", $Parallelism)
if ($ResolvedBackend -eq "vs") {
    $buildArgs += @("--config", "Release")
}
Invoke-External -FilePath "cmake" -Arguments $buildArgs

$installArgs = @("--install", $BuildDir)
if ($ResolvedBackend -eq "vs") {
    $installArgs += @("--config", "Release")
}
Invoke-External -FilePath "cmake" -Arguments $installArgs

$setupPy = Join-Path $BuildDir "setup.py"
if (Test-Path $setupPy) {
    Ensure-WheelSupport -PythonPath $ResolvedPython
    Push-Location $BuildDir
    try {
        Invoke-External -FilePath $ResolvedPython -Arguments @("setup.py", "bdist_wheel", "--dist-dir", $WheelhouseDir)
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
    generator = $ResolvedGenerator
    backend = $ResolvedBackend
    architecture = $Architecture
    parallel = $Parallelism
    ninja_path = $NinjaPath
    vtk_version = "9.3.1"
}

$manifest | ConvertTo-Json -Depth 4 | Set-Content -Path $ManifestPath -Encoding UTF8
Write-Host "Wrote manifest to $ManifestPath"
