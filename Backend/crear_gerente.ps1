#!/usr/bin/env powershell
# Script para crear un usuario gerente rápidamente

Write-Host "🔧 Crear Usuario Gerente - ELIXIR" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

# Verificar si estamos en la carpeta Backend
if (-not (Test-Path ".\manage.py")) {
    Write-Host "❌ Error: Este script debe ejecutarse desde la carpeta Backend" -ForegroundColor Red
    Write-Host "📁 Navega a: Elixir\Backend" -ForegroundColor Yellow
    exit 1
}

# Verificar si el entorno virtual está activado
if ($env:VIRTUAL_ENV -eq $null) {
    Write-Host "⚠️ El entorno virtual no está activado." -ForegroundColor Yellow
    Write-Host "🔄 Activando entorno virtual..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
}

# Solicitar datos
$email = Read-Host "📧 Email del gerente"
$password = Read-Host "🔐 Contraseña" -AsSecureString
$passwordText = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($password))
$nombre = Read-Host "👤 Nombre del gerente (opcional, presiona Enter para 'Gerente')"

if ([string]::IsNullOrWhiteSpace($nombre)) {
    $nombre = "Gerente"
}

Write-Host ""
Write-Host "🔄 Creando usuario gerente..." -ForegroundColor Cyan
Write-Host ""

# Ejecutar comando
python manage.py crear_usuario_gerente $email $passwordText --nombre $nombre

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ ¡Usuario gerente creado exitosamente!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Credenciales:" -ForegroundColor Cyan
    Write-Host "  📧 Email: $email" -ForegroundColor White
    Write-Host "  🔐 Contraseña: $passwordText" -ForegroundColor White
    Write-Host "  👤 Nombre: $nombre" -ForegroundColor White
    Write-Host "  🎭 Rol: gerente" -ForegroundColor White
    Write-Host ""
    Write-Host "🌐 Ahora puedes iniciar sesión en: http://localhost:5173" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Error al crear el usuario" -ForegroundColor Red
}
