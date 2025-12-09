from django.core.management.base import BaseCommand
from inventario.models import Producto

class Command(BaseCommand):
    help = 'Popula el campo imagen_url con las URLs de imagen existentes'

    def handle(self, *args, **options):
        productos = Producto.objects.filter(imagen__isnull=False, imagen_url__exact='')
        
        actualizado = 0
        for producto in productos:
            if producto.imagen:
                # Construir la URL correcta
                producto.imagen_url = f'/media/{producto.imagen}'
                producto.save()
                actualizado += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Actualizado: {producto.nombre} - {producto.imagen_url}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Total productos actualizados: {actualizado}')
        )
