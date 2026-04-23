[CmdletBinding()]
param(
    [string]$Version = "9.3.1",
    [string]$Url = "",
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..\..")

$ExternalSrcDir = Join-Path $RepoRoot "external\src"
$TargetDir = Join-Path $ExternalSrcDir "vtk-$Version"
$TempRoot = Join-Path $RepoRoot ".tmp\downloads"
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

function Get-Downloader {
    $curlCommand = Get-Command curl.exe -ErrorAction SilentlyContinue
    if ($curlCommand) {
        return @{
            Name = "curl.exe"
            FilePath = $curlCommand.Source
        }
    }

    return @{
        Name = "Invoke-WebRequest"
        FilePath = $null
    }
}

function Get-ArchivePlan {
    param(
        [Parameter(Mandatory = $true)]
        [string]$VtkVersion,
        [string]$ExplicitUrl = ""
    )

    $extractor = Get-ArchiveExtractor
    $preferredExtension = if ($extractor.Name -eq "tar.exe") { "tar.gz" } else { "zip" }
    $downloadUrl = $ExplicitUrl
    if (-not $downloadUrl) {
        $downloadUrl = "https://gitlab.kitware.com/vtk/vtk/-/archive/v$VtkVersion/vtk-v$VtkVersion.$preferredExtension" +
            "?ref_type=tags"
    }

    $archiveFileName = [System.IO.Path]::GetFileName(([System.Uri]$downloadUrl).AbsolutePath)
    if (-not $archiveFileName) {
        $archiveFileName = "vtk-v$VtkVersion.$preferredExtension"
    }

    return @{
        Url = $downloadUrl
        ArchivePath = Join-Path $TempRoot $archiveFileName
        Extractor = $extractor
    }
}

function Download-FileFast {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourceUrl,
        [Parameter(Mandatory = $true)]
        [string]$DestinationPath
    )

    $downloader = Get-Downloader
    if ($downloader.Name -eq "curl.exe") {
        Write-Host "Downloading with curl.exe..."
        Invoke-External -FilePath $downloader.FilePath -Arguments @(
            "--fail",
            "--location",
            "--retry", "5",
            "--retry-delay", "2",
            "--output", $DestinationPath,
            $SourceUrl
        )
        return
    }

    Write-Host "Downloading with Invoke-WebRequest..."
    Invoke-WebRequest -Uri $SourceUrl -OutFile $DestinationPath
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

$ArchivePlan = Get-ArchivePlan -VtkVersion $Version -ExplicitUrl $Url
$ArchivePath = $ArchivePlan.ArchivePath
$DownloadUrl = $ArchivePlan.Url

if (Test-Path $ArchivePath) {
    Remove-Item -LiteralPath $ArchivePath -Force
}

if (Test-Path $ExtractRoot) {
    Remove-Item -LiteralPath $ExtractRoot -Recurse -Force
}

Write-Host "Downloading VTK $Version source archive..."
Write-Host "URL: $DownloadUrl"
Download-FileFast -SourceUrl $DownloadUrl -DestinationPath $ArchivePath

Expand-ArchiveFast -ArchivePath $ArchivePath -DestinationPath $ExtractRoot

$ExtractedDir = Get-ChildItem -LiteralPath $ExtractRoot -Directory | Select-Object -First 1
if (-not $ExtractedDir) {
    throw "Archive extraction did not produce a source directory under $ExtractRoot."
}

if (Test-Path $TargetDir) {
    Remove-Item -LiteralPath $TargetDir -Recurse -Force
}

Move-Item -LiteralPath $ExtractedDir.FullName -Destination $TargetDir

Write-Host "VTK source is ready at $TargetDir"
Write-Host "Tip: if download or extraction still feels capped, Windows Defender or HTTPS inspection may be throttling access to .tmp/downloads and external/src."
