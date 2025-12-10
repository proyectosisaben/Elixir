from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventario.models import Cliente
from datetime import date

class Command(BaseCommand):
    help = 'Crear un usuario admin_sistema para acceder al dashboard administrativo'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email del usuario admin')
        parser.add_argument('password', type=str, help='Contraseña del usuario')
        parser.add_argument('--nombre', type=str, default='Admin', help='Nombre del usuario')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        nombre = options['nombre']

        try:
            # Crear o actualizar usuario
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'first_name': nombre,
                }
            )

            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Usuario creado: {email}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Usuario ya existe: {email}')
                )

            # Crear o actualizar Cliente con rol admin_sistema
            cliente, created = Cliente.objects.get_or_create(
                user=user,
                defaults={
                    'fecha_nacimiento': date(2000, 1, 1),
                    'email_confirmado': True,
                    'rol': 'admin_sistema'
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Cliente admin_sistema creado con rol: admin_sistema')
                )
            else:
                # Actualizar rol si no es admin_sistema
                if cliente.rol != 'admin_sistema':
                    cliente.rol = 'admin_sistema'
                    cliente.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Rol actualizado a: admin_sistema')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Cliente ya tiene rol admin_sistema')
                    )

            self.stdout.write(
                self.style.SUCCESS('\n✅ ¡Admin Sistema creado exitosamente!')
            )
            self.stdout.write(f'📧 Email: {email}')
            self.stdout.write(f'🔐 Contraseña: {password}')
            self.stdout.write(f'👤 Nombre: {nombre}')
            self.stdout.write(f'🎭 Rol: admin_sistema')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )
