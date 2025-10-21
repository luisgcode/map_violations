<#
PowerShell setup wrapper for bootstrap.py
Usage:
  .\setup.ps1    # interactive
  .\setup.ps1 -Yes  # non-interactive
#>
param(
    [switch]$Yes
)

function Try-Install-Python {
    Write-Host "Attempting to install Python automatically (requires admin)." -ForegroundColor Yellow
    # Try winget first
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Using winget to install Python..."
        winget install --silent --accept-package-agreements --accept-source-agreements --id Python.Python.3 -e
        return $?
    }

    # Try choco
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Host "Using choco to install Python..."
        choco install -y python
        return $?
    }

    return $false
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "Python not found in PATH." -ForegroundColor Yellow
    $proceed = Read-Host "Attempt automatic install of Python? (requires admin) [y/N]"
    if ($proceed -match '^[yY]') {
        $ok = Try-Install-Python
        if (-not $ok) {
            Write-Host "Automatic install failed or not available. Please install Python 3.8+ manually and re-run." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Please install Python 3.8+ and ensure 'python' is on PATH, then re-run this script." -ForegroundColor Red
        exit 1
    }
}

$script = Join-Path $PSScriptRoot 'bootstrap.py'
if (-not (Test-Path $script)) {
    Write-Host "bootstrap.py not found in repository root." -ForegroundColor Red
    exit 1
}

$yesArg = if ($Yes) { '--yes' } else { '' }
# Run bootstrap and auto-run the app after setup
python $script --venv .venv $yesArg --run
