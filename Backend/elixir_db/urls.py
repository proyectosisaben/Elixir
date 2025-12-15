from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.static import serve
import os

admin.site.site_header = "Elixir - Administración"
admin.site.site_title = "Elixir Admin"

def api_root(request):
    """API root endpoint"""
    return JsonResponse({
        'message': 'Bienvenido a la API de Elixir',
        'version': '1.0',
        'endpoints': {
            'home': '/api/home/',
            'productos': '/api/productos/',
            'catalogo': '/api/catalogo/',
            'producto_detalle': '/api/producto/<id>/',
            'registro': '/api/registro/',
            'checkout': '/api/checkout/',
            'admin': '/admin/',
        }
    })

# Vista para servir el frontend React
def serve_react(request, path=''):
    """Sirve el frontend React - index.html para SPA routing"""
    frontend_path = os.path.join(settings.BASE_DIR, 'frontend', 'build')
    
    # Si es un archivo estático del frontend (js, css, assets)
    file_path = os.path.join(frontend_path, path)
    if path and os.path.isfile(file_path):
        return serve(request, path, document_root=frontend_path)
    
    # Para cualquier otra ruta, servir index.html (SPA routing)
    index_path = os.path.join(frontend_path, 'index.html')
    if os.path.exists(index_path):
        from django.http import HttpResponse
        with open(index_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html')
    
    # Fallback a API root si no hay frontend
    return api_root(request)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('inventario.urls')),
    
    # API root info
    path('api-info/', api_root, name='api_root'),
]

# Archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Catch-all para servir el frontend React (debe ir al final)
urlpatterns += [
    re_path(r'^(?P<path>.*)$', serve_react, name='serve_react'),
]
