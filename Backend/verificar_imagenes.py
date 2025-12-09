import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elixir_db.settings')
django.setup()

from inventario.models import Producto

# Verificar estado de imagen_url
productos = Producto.objects.all()
print(f"\n=== VERIFICACIÓN DE IMAGEN_URL ===\n")
print(f"Total de productos: {productos.count()}\n")

sin_imagen_url = 0
con_imagen_url = 0
sin_imagen = 0

for p in productos:
    if p.imagen_url:
        con_imagen_url += 1
        print(f"✓ {p.nombre}: imagen_url = {p.imagen_url}")
    elif p.imagen:
        sin_imagen_url += 1
        print(f"✗ {p.nombre}: imagen_url vacío, pero tiene imagen = {p.imagen}")
    else:
        sin_imagen += 1
        print(f"✗✗ {p.nombre}: SIN imagen_url ni imagen")

print(f"\n=== RESUMEN ===")
print(f"Con imagen_url: {con_imagen_url}")
print(f"Sin imagen_url (pero con imagen): {sin_imagen_url}")
print(f"Sin ninguna imagen: {sin_imagen}")
