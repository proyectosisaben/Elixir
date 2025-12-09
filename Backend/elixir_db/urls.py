from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from inventario import views as inventario_views

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
    
    # Inventario URLs - API endpoints at root level
    path('api/', include('inventario.urls')),
    
    # Redirect root to API
    path('', api_root, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
