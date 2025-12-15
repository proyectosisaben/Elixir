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

## 🚀 Despliegue en Render

### Opción 1: Blueprint (Automático)
1. Ir a [Render Dashboard](https://dashboard.render.com)
2. Click en "New" → "Blueprint"
3. Conectar el repositorio de GitHub
4. Render detectará el archivo `render.yaml` y creará todos los servicios

### Opción 2: Manual

#### Backend (Web Service)
- **Root Directory:** `Backend`
- **Build Command:** `./build.sh`
- **Start Command:** `gunicorn elixir_db.wsgi:application`

**Variables de Entorno:**
```
SECRET_KEY=k8$mN2xP9qL5vR7wT3yU6zA1bC4dE0fG8hJ2kM5nQ7sW9xY1zB3cD6eF
DEBUG=False
ALLOWED_HOSTS=.onrender.com
FRONTEND_URL=https://tu-frontend.onrender.com
CSRF_TRUSTED_ORIGINS=https://*.onrender.com
```

#### Frontend (Static Site)
- **Root Directory:** `Frontend/PaginaWeb`
- **Build Command:** `npm install && npm run build`
- **Publish Directory:** `dist`

**Variables de Entorno:**
```
VITE_API_URL=https://tu-backend.onrender.com/api
```

### Configurar Rewrite Rule en Frontend
En Settings → Redirects/Rewrites:
- Source: `/*`
- Destination: `/index.html`
- Action: Rewrite
