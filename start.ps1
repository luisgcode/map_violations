# MAP Violations - Script de inicio rapido
# Activa el entorno virtual e inicia la aplicacion Flask

Write-Host "Iniciando MAP Violations Email Generator..." -ForegroundColor Green
Write-Host ""

# Verificar si existe el entorno virtual
if (!(Test-Path ".\.venv")) {
    Write-Host "No se encontro el entorno virtual. Ejecuta setup.ps1 primero." -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Activar entorno virtual
Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Verificar que Flask esté instalado
try {
    & .\.venv\Scripts\python.exe -c "import flask; print('Flask version:', flask.__version__)"
    Write-Host "Flask esta instalado correctamente" -ForegroundColor Green
} catch {
    Write-Host "Error: Flask no esta instalado. Instalando dependencias..." -ForegroundColor Red
    & .\.venv\Scripts\pip.exe install -r requirements.txt
}

Write-Host ""
Write-Host "Iniciando aplicacion web..." -ForegroundColor Cyan
Write-Host "URL: http://localhost:5000" -ForegroundColor White
Write-Host "Para detener: Ctrl+C" -ForegroundColor White
Write-Host ""

# Iniciar la aplicacion Flask
& .\.venv\Scripts\python.exe app_flask.py