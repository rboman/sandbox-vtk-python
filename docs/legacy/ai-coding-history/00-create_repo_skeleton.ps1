param(
    [string]$RepoName = "sandbox-vtk-python"
)

$ErrorActionPreference = "Stop"

Write-Host "Création du dépôt initial : $RepoName"

# Répertoire racine
New-Item -ItemType Directory -Path $RepoName -Force | Out-Null

# Dossiers à créer
$directories = @(
    "$RepoName/docs",
    "$RepoName/scripts/reference/ubuntu",
    "$RepoName/external/src",
    "$RepoName/external/build",
    "$RepoName/external/install",
    "$RepoName/external/wheelhouse",
    "$RepoName/packages/codecpp",
    "$RepoName/packages/codepy",
    "$RepoName/packages/pmanager",
    "$RepoName/examples",
    "$RepoName/tests"
)

foreach ($dir in $directories) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

# Fichiers vides à créer
$files = @(
    "$RepoName/.gitignore",
    "$RepoName/README.md",
    "$RepoName/AGENTS.md",
    "$RepoName/pyproject.toml",

    "$RepoName/docs/problem-statement.md",
    "$RepoName/docs/objectives-and-non-goals.md",
    "$RepoName/docs/platform-matrix.md",
    "$RepoName/docs/existing-linux-workflow.md",
    "$RepoName/docs/desired-repository-layout.md",
    "$RepoName/docs/open-questions.md",

    "$RepoName/scripts/reference/ubuntu/build_vtk_wheel.sh",
    "$RepoName/scripts/reference/ubuntu/install_vtk_wheel.sh",

    "$RepoName/external/src/.gitkeep",
    "$RepoName/external/build/.gitkeep",
    "$RepoName/external/install/.gitkeep",
    "$RepoName/external/wheelhouse/.gitkeep",

    "$RepoName/packages/codecpp/README.md",
    "$RepoName/packages/codepy/README.md",
    "$RepoName/packages/pmanager/README.md",

    "$RepoName/examples/README.md",
    "$RepoName/tests/README.md"
)

foreach ($file in $files) {
    New-Item -ItemType File -Path $file -Force | Out-Null
}

Write-Host "Structure créée avec succès."
Write-Host ""
Write-Host "Arborescence principale :"
Get-ChildItem -Path $RepoName -Recurse | Select-Object FullName