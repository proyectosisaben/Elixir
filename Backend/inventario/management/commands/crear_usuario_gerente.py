from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventario.models import Cliente
from datetime import date

class Command(BaseCommand):
    help = 'Crear un usuario gerente para acceder al dashboard'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email del usuario gerente')
        parser.add_argument('password', type=str, help='Contraseña del usuario')
        parser.add_argument('--nombre', type=str, default='Gerente', help='Nombre del usuario')

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

            # Crear o actualizar Cliente con rol gerente
            cliente, created = Cliente.objects.get_or_create(
                user=user,
                defaults={
                    'fecha_nacimiento': date(2000, 1, 1),
                    'email_confirmado': True,
                    'rol': 'gerente'
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Cliente gerente creado con rol: gerente')
                )
            else:
                # Actualizar rol si no es gerente
                if cliente.rol != 'gerente':
                    cliente.rol = 'gerente'
                    cliente.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Rol actualizado a: gerente')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Cliente ya tiene rol gerente')
                    )

            self.stdout.write(
                self.style.SUCCESS('\n✅ ¡Gerente creado exitosamente!')
            )
            self.stdout.write(f'📧 Email: {email}')
            self.stdout.write(f'🔐 Contraseña: {password}')
            self.stdout.write(f'👤 Nombre: {nombre}')
            self.stdout.write(f'🎭 Rol: gerente')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: {str(e)}')
            )
