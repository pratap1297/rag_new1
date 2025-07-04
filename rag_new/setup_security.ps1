# Setup Security Script for Windows
# This script sets up pre-commit with detect-secrets and configures .gitignore
# Run this script from your project root directory

# Stop on first error
$ErrorActionPreference = "Stop"

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges. Please run as administrator." -ForegroundColor Red
    exit 1
}

# Function to check if a command exists
function Command-Exists {
    param($command)
    $exists = $null -ne (Get-Command $command -ErrorAction SilentlyContinue)
    return $exists
}

# Check if Python is installed
if (-not (Command-Exists "python")) {
    Write-Host "Python is not installed. Please install Python 3.7+ first." -ForegroundColor Red
    exit 1
}

# Check if pip is installed
if (-not (Command-Exists "pip")) {
    Write-Host "pip is not installed. Please install pip first." -ForegroundColor Red
    exit 1
}

# Install required packages
Write-Host "Installing required packages..." -ForegroundColor Cyan
pip install pre-commit detect-secrets

# Create .pre-commit-config.yaml if it doesn't exist
$preCommitConfig = @"
repos:
-   repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
    -   id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: .*/tests?/.*  # exclude test files
"@

$preCommitConfigPath = ".pre-commit-config.yaml"
if (-not (Test-Path $preCommitConfigPath)) {
    $preCommitConfig | Out-File -FilePath $preCommitConfigPath -Encoding utf8
    Write-Host "Created .pre-commit-config.yaml" -ForegroundColor Green
} else {
    Write-Host ".pre-commit-config.yaml already exists, skipping..." -ForegroundColor Yellow
}

# Update .gitignore
$gitignorePath = ".gitignore"
$gitignoreEntries = @(
    "",
    "# Environment variables",
    ".env",
    "*.env",
    "",
    "# Secrets",
    ".secrets.baseline",
    "*.pem",
    "*.key",
    "*.p12",
    "*.crt",
    "*.cert",
    "id_rsa",
    "*.gpg",
    "secrets.*",
    "",
    "# Python",
    "__pycache__/",
    "*.py[cod]",
    "*$py.class",
    ".python-version",
    "",
    "# Virtual Environment",
    "venv/",
    "env/",
    ".venv/"
)

if (-not (Test-Path $gitignorePath)) {
    $gitignoreEntries | Out-File -FilePath $gitignorePath -Encoding utf8
    Write-Host "Created .gitignore" -ForegroundColor Green
} else {
    $currentContent = Get-Content $gitignorePath -Raw
    foreach ($entry in $gitignoreEntries) {
        if (-not $currentContent.Contains($entry.Trim())) {
            Add-Content -Path $gitignorePath -Value $entry
            Write-Host "Added entry to .gitignore: $entry" -ForegroundColor Yellow
        }
    }
}

# Initialize pre-commit
Write-Host "Setting up pre-commit hook..." -ForegroundColor Cyan
pre-commit install

# Create initial secrets baseline
Write-Host "Creating initial secrets baseline..." -ForegroundColor Cyan
pre-commit run --all-files detect-secrets > .secrets.baseline

Write-Host "`nSetup completed successfully!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Review the .secrets.baseline file for any false positives"
Write-Host "2. Commit the .pre-commit-config.yaml, .gitignore, and .secrets.baseline files"
Write-Host "3. The pre-commit hook will now run automatically on each commit"
Write-Host "`nTo run manually: pre-commit run --all-files" -ForegroundColor Cyan
