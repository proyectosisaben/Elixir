#!/usr/bin/env bash
# Script de build para Render - Backend + Frontend

set -o errexit

echo "=== Instalando dependencias de Python ==="
pip install -r requirements.txt

echo "=== Instalando Node.js y dependencias del Frontend ==="
# Instalar Node.js si no está disponible
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
fi

echo "=== Buildeando Frontend React ==="
cd ../Frontend/PaginaWeb
npm install
npm run build

echo "=== Copiando Frontend al Backend ==="
cd ../../Backend
mkdir -p frontend/build
cp -r ../Frontend/PaginaWeb/dist/* frontend/build/

echo "=== Collectstatic ==="
python manage.py collectstatic --no-input

echo "=== Migraciones ==="
python manage.py migrate

echo "=== Build completado ==="


