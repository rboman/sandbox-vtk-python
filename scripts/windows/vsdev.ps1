[CmdletBinding()]
param(
    [string]$Arch = "x64",
    [string]$HostArch = "x64"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$vswhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path $vswhere)) {
    throw "[vsdev] vswhere.exe not found at '$vswhere'. Install Visual Studio 2022 with C++ tools."
}

$vsInstall = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $vsInstall) {
    throw "[vsdev] No Visual Studio installation with MSVC tools was found."
}

$devShellModule = Join-Path $vsInstall "Common7\Tools\Microsoft.VisualStudio.DevShell.dll"
if (-not (Test-Path $devShellModule)) {
    throw "[vsdev] DevShell module not found at '$devShellModule'."
}

Import-Module $devShellModule -ErrorAction Stop
$devCmdArgs = "-arch=$Arch -host_arch=$HostArch"
Enter-VsDevShell -VsInstallPath $vsInstall -DevCmdArguments $devCmdArgs | Out-Null

Write-Host "[vsdev] Activated MSVC developer environment from: $vsInstall"
Write-Host "[vsdev] Arguments: $devCmdArgs"
