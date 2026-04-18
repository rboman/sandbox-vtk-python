[CmdletBinding()]
param(
    [string]$Version = "9.3.1",
    [string]$Url = "https://gitlab.kitware.com/vtk/vtk/-/archive/v9.3.1/vtk-v9.3.1.zip?ref_type=tags",
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..\..")

$ExternalSrcDir = Join-Path $RepoRoot "external\src"
$TargetDir = Join-Path $ExternalSrcDir "vtk-$Version"
$TempRoot = Join-Path $RepoRoot ".tmp\downloads"
$ZipPath = Join-Path $TempRoot "vtk-v$Version.zip"
$ExtractRoot = Join-Path $TempRoot "extract-vtk-$Version"

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

function Get-ArchiveExtractor {
    $tarCommand = Get-Command tar.exe -ErrorAction SilentlyContinue
    if ($tarCommand) {
        return @{
            Name = "tar.exe"
            FilePath = $tarCommand.Source
        }
    }

    return @{
        Name = "Expand-Archive"
        FilePath = $null
    }
}

function Expand-ArchiveFast {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ArchivePath,
        [Parameter(Mandatory = $true)]
        [string]$DestinationPath
    )

    $extractor = Get-ArchiveExtractor
    if ($extractor.Name -eq "tar.exe") {
        Write-Host "Extracting archive with tar.exe..."
        New-Item -ItemType Directory -Force -Path $DestinationPath | Out-Null
        Invoke-External -FilePath $extractor.FilePath -Arguments @("-xf", $ArchivePath, "-C", $DestinationPath)
        return
    }

    Write-Host "Extracting archive with Expand-Archive..."
    Expand-Archive -Path $ArchivePath -DestinationPath $DestinationPath -Force
}

if ((Test-Path $TargetDir) -and -not $Force) {
    throw "Target directory already exists: $TargetDir. Use -Force to replace it."
}

New-Item -ItemType Directory -Force -Path $ExternalSrcDir, $TempRoot | Out-Null

if (Test-Path $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
}

if (Test-Path $ExtractRoot) {
    Remove-Item -LiteralPath $ExtractRoot -Recurse -Force
}

Write-Host "Downloading VTK $Version source archive..."
Invoke-WebRequest -Uri $Url -OutFile $ZipPath

Expand-ArchiveFast -ArchivePath $ZipPath -DestinationPath $ExtractRoot

$ExtractedDir = Get-ChildItem -LiteralPath $ExtractRoot -Directory | Select-Object -First 1
if (-not $ExtractedDir) {
    throw "Archive extraction did not produce a source directory under $ExtractRoot."
}

if (Test-Path $TargetDir) {
    Remove-Item -LiteralPath $TargetDir -Recurse -Force
}

Move-Item -LiteralPath $ExtractedDir.FullName -Destination $TargetDir

Write-Host "VTK source is ready at $TargetDir"
Write-Host "Tip: if Windows Defender slows extraction badly, exclude this repo's .tmp and external/src directories from real-time scanning."
