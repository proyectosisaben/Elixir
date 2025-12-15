import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Base directory del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Seguridad - usar variable de entorno en producción
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-elixir-botilleria-2025-super-secreto')

# DEBUG = False en producción
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,.onrender.com,.railway.app').split(',')

# Aplicaciones instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'inventario',   # Cambia aquí el nombre de la app si la renombras, por ejemplo a 'clientes', 'producto', etc.
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Whitenoise para archivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Rutas principales
ROOT_URLCONF = 'elixir_db.urls'    # Cambiado de 'todocarro.urls' a 'elixir_db.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'frontend', 'build'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI
WSGI_APPLICATION = 'elixir_db.wsgi.application'    # Cambiado de 'todocarro.wsgi.application'

# Configuración de base de datos
# Usa DATABASE_URL de Render/Railway si está disponible
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
    }
else:
    # Base de datos local PostgreSQL para desarrollo
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'elixir_db'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
# Validadores de contraseña
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# Email para pruebas y confirmación de usuarios
# Para desarrollo (los emails se muestran en la consola):
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Para producción con SMTP real (Gmail):
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = ''  # Tu email de Gmail
EMAIL_HOST_PASSWORD = ''  # Contraseña de aplicación de Gmail (NO tu contraseña normal)

DEFAULT_FROM_EMAIL = 'Elixir Botillería <no-reply@elixir.com>'
FRONTEND_URL = 'http://localhost:3000'  # URL del frontend React

# Localización y zona horaria de Chile
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# Archivos estáticos (CSS, JS)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Directorios de archivos estáticos
STATICFILES_DIRS = []
_static_dir = os.path.join(BASE_DIR, 'static')
_frontend_assets = os.path.join(BASE_DIR, 'frontend', 'build', 'assets')

if os.path.exists(_static_dir):
    STATICFILES_DIRS.append(_static_dir)
if os.path.exists(_frontend_assets):
    STATICFILES_DIRS.append(_frontend_assets)

# Whitenoise para servir archivos estáticos en producción
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Ruta del frontend buildeado
FRONTEND_BUILD_DIR = os.path.join(BASE_DIR, 'frontend', 'build')

# Archivos media (subida de imágenes, documentos)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Auto field por defecto para modelos
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS authorization (agrega dominios del frontend React si corresponde)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",
    "http://localhost:5177",
    "http://localhost:5178",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://127.0.0.1:5176",
    "http://127.0.0.1:5177",
    "http://127.0.0.1:5178",
    # Frontend en Render
    "https://elixir-frontend-web.onrender.com",
    "https://elixir-frontend-67hb.onrender.com",
]

# Agregar URLs de Railway desde variable de entorno
FRONTEND_URL_ENV = os.environ.get('FRONTEND_URL')
if FRONTEND_URL_ENV:
    CORS_ALLOWED_ORIGINS.append(FRONTEND_URL_ENV)

# Permitir todos los orígenes de Render y Railway en producción
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.onrender\.com$",
    r"^https://.*\.railway\.app$",
    r"^https://.*\.up\.railway\.app$",
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Configuración de seguridad para producción
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = False  # Railway maneja SSL
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', 'https://*.onrender.com,https://*.railway.app').split(',')