# Elixir - E-commerce Botillería

Plataforma de e-commerce desarrollada con Django (Backend) + React (Frontend).

## 🚀 Inicio Rápido

### Backend (Django)
```bash
cd Backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend (React + Vite)
```bash
cd Frontend/PaginaWeb
npm install
npm run dev
```

## 📁 Estructura del Proyecto

- **Backend/** - API REST con Django
- **Frontend/PaginaWeb/** - Aplicación React con Vite

## ⚙️ Requisitos

- Python 3.11+
- Node.js 18+
- MySQL 8.0

## 🚂 Despliegue en Railway

### Variables de Entorno - Backend
```
SECRET_KEY=tu-clave-secreta-segura
DEBUG=False
ALLOWED_HOSTS=.railway.app
FRONTEND_URL=https://tu-frontend.railway.app
CSRF_TRUSTED_ORIGINS=https://*.railway.app
```

### Variables de Entorno - Frontend
```
VITE_API_URL=https://tu-backend.railway.app/api
```

### Pasos para Desplegar
1. Crear proyecto en Railway
2. Agregar servicio de MySQL
3. Crear servicio para Backend (desde carpeta Backend/)
4. Crear servicio para Frontend (desde carpeta Frontend/PaginaWeb/)
5. Configurar variables de entorno
6. Railway detectará automáticamente los archivos de configuración
