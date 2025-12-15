from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

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

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('inventario.urls')),
    
    # API root
    path('', api_root, name='api_root'),
]

# Archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
