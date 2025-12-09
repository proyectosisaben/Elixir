from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count
from .models import Producto, Categoria, Cliente, Pedido, DetallesPedido
from django.http import JsonResponse
from .forms import RegistroClienteForm
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
import secrets
from datetime import datetime
import uuid

@api_view(['POST'])
def login_cliente(request):
    """API endpoint para iniciar sesión"""
    if request.method == 'POST':
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'success': False,
                'message': 'Email y contraseña son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Obtener usuario por email
            user = User.objects.get(email=email)
            
            # Verificar contraseña
            if user.check_password(password):
                # Obtener cliente asociado
                try:
                    cliente = Cliente.objects.get(user=user)
                    rol = cliente.rol
                    fecha_nacimiento = cliente.fecha_nacimiento.isoformat() if cliente.fecha_nacimiento else None
                except Cliente.DoesNotExist:
                    cliente = None
                    # Si es superusuario o staff de Django, crear Cliente con admin_sistema
                    if user.is_superuser or user.is_staff:
                        from datetime import date
                        cliente, created = Cliente.objects.get_or_create(
                            user=user,
                            defaults={
                                'fecha_nacimiento': date(2000, 1, 1),
                                'email_confirmado': True,
                                'rol': 'admin_sistema'
                            }
                        )
                        if not created and cliente.rol != 'admin_sistema':
                            cliente.rol = 'admin_sistema'
                            cliente.save()
                        rol = 'admin_sistema'
                    else:
                        rol = 'cliente'
                    fecha_nacimiento = None
                
                # Generar token simple
                token = secrets.token_urlsafe(32)
                
                return Response({
                    'success': True,
                    'message': 'Inicio de sesión exitoso',
                    'token': token,
                    'usuario': {
                        'id': user.id,
                        'email': user.email,
                        'nombre': user.first_name or user.username,
                        'rol': rol,
                        'fecha_nacimiento': fecha_nacimiento,
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Contraseña incorrecta'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Usuario no encontrado'
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al iniciar sesión: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'error': 'Método no permitido'
    }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
def registro_cliente(request):
    """API endpoint para registrar nuevo cliente"""
    if request.method == 'POST':
        # Convertir JSON a datos de formulario
        data = request.data
        
        # Validar que haya email y password
        email = data.get('email')
        password = data.get('password')
        password_confirm = data.get('password_confirm')
        fecha_nacimiento = data.get('fecha_nacimiento')
        
        # Validar campos requeridos
        if not all([email, password, password_confirm, fecha_nacimiento]):
            return Response({
                'success': False,
                'message': 'Todos los campos son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar que las contraseñas coincidan
        if password != password_confirm:
            return Response({
                'success': False,
                'message': 'Las contraseñas no coinciden'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar longitud de contraseña
        if len(password) < 8:
            return Response({
                'success': False,
                'message': 'La contraseña debe tener al menos 8 caracteres'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar que el email no exista
        if User.objects.filter(email=email).exists():
            return Response({
                'success': False,
                'message': 'Este correo electrónico ya está registrado'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Crear el usuario
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password
            )
            
            # Crear el cliente vinculado al usuario con rol 'cliente' por defecto
            cliente = Cliente.objects.create(
                user=user,
                fecha_nacimiento=fecha_nacimiento,
                rol='cliente'  # Rol por defecto
            )
            
            # Enviar correo de confirmación
            send_mail(
                'Confirma tu registro',
                'Gracias por registrarte en Elixir. ¡Bienvenido!',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,
            )
            
            return Response({
                'success': True,
                'message': 'Registro exitoso. Ya puedes iniciar sesión.'
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al registrar: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'error': 'Método no permitido'
    }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

def home(request):
    """API endpoint para obtener datos de home"""
    try:
        categorias = Categoria.objects.filter(activa=True).values('id', 'nombre', 'descripcion')
        productos_destacados = Producto.objects.filter(activo=True)[:8]
        productos_prueba = Producto.objects.filter(nombre__icontains="Prueba", activo=True)

        productos_data = []
        for p in productos_destacados:
            imagen_url = ''
            if hasattr(p, 'imagenes') and p.imagenes.exists():
                primera = p.imagenes.first()
                if primera and getattr(primera, 'imagen', None):
                    imagen_url = request.build_absolute_uri(primera.imagen.url)
            elif p.imagen:
                imagen_url = request.build_absolute_uri(p.imagen.url)
            if not imagen_url:
                imagen_url = 'https://via.placeholder.com/400x250?text=Sin+imagen'
            
            productos_data.append({
                'id': p.id,
                'nombre': p.nombre,
                'precio': float(p.precio) if p.precio else 0,
                'imagen': imagen_url,
                'imagen_url': p.imagen_url or imagen_url,
            })

        return JsonResponse({
            'categorias': list(categorias),
            'productos_destacados': productos_data,
            'productos_prueba': list(productos_prueba.values('id', 'nombre', 'precio')),
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)

def catalogo(request):
    """API endpoint para catálogo de productos con filtros"""
    try:
        productos = Producto.objects.filter(activo=True)
        categorias_qs = Categoria.objects.filter(activa=True)
        categoria_id = request.GET.get('categoria')
        busqueda = request.GET.get('q')

        if categoria_id:
            productos = productos.filter(categoria_id=categoria_id)

        if busqueda:
            productos = productos.filter(
                Q(nombre__icontains=busqueda) |
                Q(descripcion__icontains=busqueda)
            )

        productos_data = []
        for p in productos:
            imagen_url = ''
            if hasattr(p, 'imagenes') and p.imagenes.exists():
                primera = p.imagenes.first()
                if primera and getattr(primera, 'imagen', None):
                    imagen_url = request.build_absolute_uri(primera.imagen.url)
            elif p.imagen:
                imagen_url = request.build_absolute_uri(p.imagen.url)
            if not imagen_url:
                imagen_url = 'https://via.placeholder.com/400x250?text=Sin+imagen'
            
            productos_data.append({
                'id': p.id,
                'nombre': p.nombre,
                'sku': p.sku,
                'precio': float(p.precio) if p.precio else 0,
                'stock': p.stock,
                'descripcion': p.descripcion,
                'imagen': imagen_url,
                'imagen_url': p.imagen_url or imagen_url,
                'categoria': {'id': p.categoria.id, 'nombre': p.categoria.nombre},
            })

        categorias = [{'id': c.id, 'nombre': c.nombre} for c in categorias_qs]

        return JsonResponse({
            'productos': productos_data,
            'categorias': categorias,
            'filtros': {
                'categoria': categoria_id,
                'busqueda': busqueda,
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def detalle_producto(request, producto_id):
    """API endpoint para obtener detalle de un producto"""
    try:
        producto = get_object_or_404(Producto, id=producto_id, activo=True)
        productos_relacionados = Producto.objects.filter(
            categoria=producto.categoria,
            activo=True
        ).exclude(id=producto_id)[:4]

        imagen_url = ''
        if hasattr(producto, 'imagenes') and producto.imagenes.exists():
            primera = producto.imagenes.first()
            if primera and getattr(primera, 'imagen', None):
                imagen_url = request.build_absolute_uri(primera.imagen.url)
        elif producto.imagen:
            imagen_url = request.build_absolute_uri(producto.imagen.url)
        if not imagen_url:
            imagen_url = 'https://via.placeholder.com/400x250?text=Sin+imagen'

        relacionados = []
        for p in productos_relacionados:
            img_url = ''
            if hasattr(p, 'imagenes') and p.imagenes.exists():
                primera = p.imagenes.first()
                if primera and getattr(primera, 'imagen', None):
                    img_url = request.build_absolute_uri(primera.imagen.url)
            elif p.imagen:
                img_url = request.build_absolute_uri(p.imagen.url)
            if not img_url:
                img_url = 'https://via.placeholder.com/400x250?text=Sin+imagen'
            relacionados.append({
                'id': p.id,
                'nombre': p.nombre,
                'precio': float(p.precio),
                'imagen': img_url,
                'imagen_url': p.imagen_url or img_url,
            })

        return JsonResponse({
            'producto': {
                'id': producto.id,
                'nombre': producto.nombre,
                'sku': producto.sku,
                'precio': float(producto.precio),
                'costo': float(producto.costo),
                'stock': producto.stock,
                'descripcion': producto.descripcion,
                'imagen': imagen_url,
                'imagen_url': producto.imagen_url or imagen_url,
                'categoria': {'id': producto.categoria.id, 'nombre': producto.categoria.nombre},
                'proveedor': {'id': producto.proveedor.id, 'nombre': producto.proveedor.nombre},
                'margen_ganancia': producto.margen_ganancia,
            },
            'productos_relacionados': relacionados,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def checkout(request):
    """API endpoint para checkout (placeholder)"""
    return JsonResponse({'message': 'Checkout API endpoint'})

def api_productos(request):
    productos_qs = Producto.objects.filter(activo=True)
    categorias_qs = Categoria.objects.filter(activa=True)

    productos = []
    for p in productos_qs:
        imagen_url = ''
        try:
            # Primero intentar con imagen_url de la BD
            if p.imagen_url:
                imagen_url = p.imagen_url
            # Si no existe imagen_url, intentar con imagenes relacionadas
            elif hasattr(p, 'imagenes') and p.imagenes.exists():
                primera = p.imagenes.first()
                if primera and getattr(primera, 'imagen', None):
                    imagen_url = request.build_absolute_uri(primera.imagen.url)
            # Si no, usar imagen del producto
            elif p.imagen:
                imagen_url = request.build_absolute_uri(p.imagen.url)
        except Exception:
            imagen_url = ''
        
        # Fallback final
        if not imagen_url:
            imagen_url = 'https://via.placeholder.com/400x250?text=Sin+imagen'
        
        productos.append({
            'id': p.id,
            'nombre': p.nombre,
            'sku': p.sku,
            'precio': float(p.precio) if p.precio is not None else 0,
            'costo': float(p.costo) if p.costo is not None else 0,
            'stock': p.stock,
            'stock_minimo': p.stock_minimo,
            'descripcion': p.descripcion,
            'imagen': imagen_url,
            'imagen_url': imagen_url,
            'categoria': {
                'id': p.categoria.id,
                'nombre': p.categoria.nombre,
            },
            'activo': p.activo,
        })

    categorias = [{'id': c.id, 'nombre': c.nombre} for c in categorias_qs]

    return JsonResponse({'productos': productos, 'categorias': categorias}, safe=False)

@api_view(['POST'])
def cambiar_rol_cliente(request):
    """API endpoint para cambiar el rol de un cliente (solo admin)"""
    if request.method == 'POST':
        usuario_id = request.data.get('usuario_id')
        nuevo_rol = request.data.get('rol')
        
        # Validar que el rol sea válido
        roles_validos = ['cliente', 'vendedor', 'gerente', 'admin_sistema']
        if nuevo_rol not in roles_validos:
            return Response({
                'success': False,
                'message': f'Rol inválido. Roles válidos: {", ".join(roles_validos)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from datetime import date
            user = User.objects.get(id=usuario_id)
            # Crear o obtener cliente
            cliente, created = Cliente.objects.get_or_create(
                user=user,
                defaults={
                    'fecha_nacimiento': date(2000, 1, 1),
                    'email_confirmado': True,
                    'rol': nuevo_rol
                }
            )
            if not created:
                cliente.rol = nuevo_rol
                cliente.save()
            
            return Response({
                'success': True,
                'message': f'Rol actualizado a {cliente.get_rol_display()}',
                'rol': cliente.rol
            }, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Usuario no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al actualizar rol: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({
        'error': 'Método no permitido'
    }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
def verificar_rol(request):
    """API endpoint para verificar el rol actual de un usuario"""
    try:
        usuario_id = request.query_params.get('usuario_id')
        
        if not usuario_id:
            return Response({
                'success': False,
                'message': 'usuario_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.get(id=usuario_id)
        cliente = Cliente.objects.get(user=user)
        
        return Response({
            'success': True,
            'usuario_id': user.id,
            'email': user.email,
            'nombre': user.first_name or user.username,
            'rol': cliente.rol,
            'rol_display': cliente.get_rol_display()
        }, status=status.HTTP_200_OK)
        
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'message': 'No se encontró información del cliente'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def listar_clientes(request):
    """API endpoint para listar todos los clientes con sus roles"""
    try:
        clientes = Cliente.objects.select_related('user').all()
        clientes_data = []
        
        for cliente in clientes:
            clientes_data.append({
                'usuario_id': cliente.user_id,
                'email': cliente.user.email,
                'nombre': cliente.user.first_name or cliente.user.username,
                'rol': cliente.rol,
                'rol_display': cliente.get_rol_display(),
                'fecha_nacimiento': cliente.fecha_nacimiento.isoformat(),
                'email_confirmado': cliente.email_confirmado,
                'fecha_creacion': cliente.user.date_joined.isoformat()
            })
        
        return Response({
            'success': True,
            'total': len(clientes_data),
            'clientes': clientes_data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al listar clientes: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

# ==================== ENDPOINTS PARA PEDIDOS Y CHECKOUT ====================

@api_view(['POST'])
def crear_pedido(request):
    """Crear un nuevo pedido desde el carrito"""
    if request.method == 'POST':
        try:
            usuario_id = request.data.get('usuario_id')
            items = request.data.get('items', [])  # [{'producto_id': 1, 'cantidad': 2, 'precio': 100}]
            metodo_pago = request.data.get('metodo_pago', 'transferencia')
            
            if not usuario_id or not items:
                return Response({
                    'success': False,
                    'message': 'Usuario_id e items son requeridos'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener cliente
            cliente = Cliente.objects.get(user_id=usuario_id)
            
            # Calcular total
            total = sum(item['precio'] * item['cantidad'] for item in items)
            
            # Generar número de pedido único
            numero_pedido = f"PED-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Crear pedido
            pedido = Pedido.objects.create(
                cliente=cliente,
                numero_pedido=numero_pedido,
                total=total,
                subtotal=total,
                impuesto=0,
                descuento=0,
                estado='pendiente',
                metodo_pago=metodo_pago,
                vendedor=None  # Se asignará cuando el vendedor procese
            )
            
            # Crear detalles del pedido y reducir stock
            for item in items:
                producto = Producto.objects.get(id=item['producto_id'])
                
                # Verificar stock
                if producto.stock < item['cantidad']:
                    pedido.delete()
                    return Response({
                        'success': False,
                        'message': f'Stock insuficiente para {producto.nombre}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Crear detalle del pedido
                DetallesPedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=item['cantidad'],
                    precio_unitario=item['precio'],
                    subtotal=item['precio'] * item['cantidad']
                )
                
                # Reducir stock
                producto.stock -= item['cantidad']
                producto.save()
            
            return Response({
                'success': True,
                'message': 'Pedido creado exitosamente',
                'pedido_id': pedido.id,
                'numero_pedido': numero_pedido,
                'total': float(pedido.total),
                'estado': pedido.estado
            }, status=status.HTTP_201_CREATED)
        
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Cliente no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Producto.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Producto no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al crear pedido: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({'error': 'Método no permitido'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['GET'])
def mis_pedidos(request):
    """Obtener todos los pedidos del usuario logueado"""
    try:
        usuario_id = request.query_params.get('usuario_id')
        
        if not usuario_id:
            return Response({
                'success': False,
                'message': 'usuario_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cliente = Cliente.objects.get(user_id=usuario_id)
        
        if cliente.rol == 'cliente':
            # Clientes ven sus propios pedidos
            pedidos = Pedido.objects.filter(cliente=cliente).prefetch_related('detalles')
        elif cliente.rol in ['vendedor', 'gerente']:
            # Vendedores y gerentes ven todos los pedidos
            pedidos = Pedido.objects.all().prefetch_related('detalles')
        else:
            return Response({
                'success': False,
                'message': 'Acceso no autorizado'
            }, status=status.HTTP_403_FORBIDDEN)
        
        pedidos_data = []
        for pedido in pedidos:
            detalles = []
            for detalle in pedido.detalles.all():
                detalles.append({
                    'producto_id': detalle.producto.id,
                    'producto_nombre': detalle.producto.nombre,
                    'cantidad': detalle.cantidad,
                    'precio_unitario': float(detalle.precio_unitario),
                    'subtotal': float(detalle.subtotal)
                })
            
            pedidos_data.append({
                'pedido_id': pedido.id,
                'numero_pedido': pedido.numero_pedido,
                'cliente_email': pedido.cliente.user.email,
                'cliente_nombre': pedido.cliente.user.first_name or pedido.cliente.user.username,
                'total': float(pedido.total),
                'estado': pedido.estado,
                'metodo_pago': pedido.metodo_pago,
                'fecha_pedido': pedido.fecha_pedido.isoformat(),
                'detalles': detalles
            })
        
        return Response({
            'success': True,
            'total': len(pedidos_data),
            'pedidos': pedidos_data
        }, status=status.HTTP_200_OK)
    
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Cliente no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al obtener datos del dashboard: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def dashboard_gerente(request):
    """Obtener estadísticas del dashboard para gerentes y admin_sistema"""
    try:
        usuario_id = request.query_params.get('usuario_id')
        
        if not usuario_id:
            return Response({
                'success': False,
                'message': 'usuario_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener usuario
        user = User.objects.get(id=usuario_id)
        
        # Verificar si es superusuario o staff
        if user.is_superuser or user.is_staff:
            # Crear o obtener cliente para admin_sistema
            from datetime import date
            cliente, created = Cliente.objects.get_or_create(
                user=user,
                defaults={
                    'fecha_nacimiento': date(2000, 1, 1),
                    'email_confirmado': True,
                    'rol': 'admin_sistema'
                }
            )
            if not created and cliente.rol != 'admin_sistema':
                cliente.rol = 'admin_sistema'
                cliente.save()
            # El superusuario ahora tiene rol admin_sistema, continuar
        else:
            # Obtener cliente para usuarios normales
            try:
                cliente = Cliente.objects.get(user_id=usuario_id)
            except Cliente.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Cliente no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # VALIDACIÓN ESTRICTA: Solo gerentes pueden acceder (no admin_sistema aquí)
            # admin_sistema solo si es superusuario de Django
            if cliente.rol != 'gerente':
                return Response({
                    'success': False,
                    'message': f'❌ Acceso denegado. Solo gerentes pueden acceder al dashboard. Tu rol es: {cliente.get_rol_display()}'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Calcular estadísticas
        pedidos = Pedido.objects.all()
        # Incluir todos los pedidos excepto los cancelados
        pedidos_activos = pedidos.exclude(estado='cancelado')
        
        total_ventas = pedidos_activos.aggregate(total=Sum('total'))['total'] or 0
        total_pedidos = pedidos.count()
        total_clientes = Cliente.objects.filter(rol='cliente').count()
        
        # Productos más vendidos
        productos_vendidos = DetallesPedido.objects.values('producto__nombre').annotate(
            cantidad_total=Sum('cantidad'),
            ventas_total=Sum('subtotal')
        ).order_by('-cantidad_total')[:5]
        
        # Ingresos por estado
        ingresos_por_estado = {}
        for estado, _ in [('pagado', 1), ('en_preparacion', 1), ('enviado', 1), ('entregado', 1)]:
            total = pedidos.filter(estado=estado).aggregate(total=Sum('total'))['total'] or 0
            ingresos_por_estado[estado] = float(total)
        
        return Response({
            'success': True,
            'estadisticas': {
                'total_ventas': float(total_ventas),
                'total_pedidos': total_pedidos,
                'total_clientes': total_clientes,
                'pedidos_pagados': pedidos_activos.count(),
                'productos_vendidos': list(productos_vendidos),
                'ingresos_por_estado': ingresos_por_estado
            }
        }, status=status.HTTP_200_OK)
    
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Cliente no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al obtener dashboard: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT'])
def mi_perfil(request):
    """Obtener y actualizar perfil del usuario"""
    try:
        usuario_id = request.query_params.get('usuario_id') if request.method == 'GET' else request.data.get('usuario_id')
        
        if not usuario_id:
            return Response({
                'success': False,
                'message': 'usuario_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.get(id=usuario_id)
        cliente = Cliente.objects.get(user=user)
        
        if request.method == 'GET':
            # Obtener perfil
            pedidos = Pedido.objects.filter(cliente=cliente)
            gasto_total = pedidos.aggregate(total=Sum('total'))['total'] or 0
            
            return Response({
                'success': True,
                'perfil': {
                    'usuario_id': user.id,
                    'email': user.email,
                    'nombre': user.first_name or user.username,
                    'apellido': user.last_name,
                    'username': user.username,
                    'fecha_nacimiento': cliente.fecha_nacimiento.isoformat(),
                    'rol': cliente.rol,
                    'email_confirmado': cliente.email_confirmado,
                    'gasto_total': float(gasto_total),
                    'total_pedidos': pedidos.count(),
                    'fecha_creacion': user.date_joined.isoformat()
                }
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'PUT':
            # Actualizar perfil (excepto email y username)
            nombre = request.data.get('nombre')
            apellido = request.data.get('apellido')
            fecha_nacimiento = request.data.get('fecha_nacimiento')
            
            if nombre:
                user.first_name = nombre
            if apellido:
                user.last_name = apellido
            if fecha_nacimiento:
                cliente.fecha_nacimiento = fecha_nacimiento
            
            user.save()
            cliente.save()
            
            return Response({
                'success': True,
                'message': 'Perfil actualizado exitosamente'
            }, status=status.HTTP_200_OK)
    
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Cliente no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def marcar_pedido_pagado(request):
    """Marcar un pedido como pagado (por vendedor/gerente)"""
    try:
        usuario_id = request.data.get('usuario_id')
        pedido_id = request.data.get('pedido_id')
        
        if not usuario_id or not pedido_id:
            return Response({
                'success': False,
                'message': 'usuario_id y pedido_id son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cliente = Cliente.objects.get(user_id=usuario_id)
        
        # Solo vendedores y gerentes pueden marcar como pagado
        if cliente.rol not in ['vendedor', 'gerente']:
            return Response({
                'success': False,
                'message': 'Solo vendedores y gerentes pueden realizar esta acción'
            }, status=status.HTTP_403_FORBIDDEN)
        
        pedido = Pedido.objects.get(id=pedido_id)
        pedido.marcar_como_pagado()
        
        return Response({
            'success': True,
            'message': 'Pedido marcado como pagado',
            'estado': pedido.estado
        }, status=status.HTTP_200_OK)
    
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Cliente no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Pedido.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Pedido no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
def actualizar_producto(request, producto_id):
    """Actualizar información de un producto (vendedor/admin)"""
    try:
        usuario_id = request.data.get('usuario_id')
        
        # Verificar que el usuario sea vendedor o admin
        if usuario_id:
            cliente = Cliente.objects.get(user_id=usuario_id)
            if cliente.rol not in ['vendedor', 'admin_sistema']:
                return Response({
                    'success': False,
                    'message': 'Solo vendedores y admins pueden editar productos'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Obtener el producto
        producto = Producto.objects.get(id=producto_id)
        
        # Actualizar campos
        if 'nombre' in request.data and request.data['nombre']:
            producto.nombre = request.data['nombre']
        
        if 'descripcion' in request.data:
            producto.descripcion = request.data['descripcion']
        
        if 'precio' in request.data and request.data['precio']:
            producto.precio = request.data['precio']
        
        if 'stock' in request.data and request.data['stock'] is not None:
            producto.stock = request.data['stock']
        
        # Guardar URL de imagen en el campo imagen_url
        if 'imagen_url' in request.data and request.data['imagen_url']:
            producto.imagen_url = request.data['imagen_url']
        
        producto.save()
        
        return Response({
            'success': True,
            'message': 'Producto actualizado exitosamente',
            'producto': {
                'id': producto.id,
                'nombre': producto.nombre,
                'descripcion': producto.descripcion,
                'precio': str(producto.precio),
                'stock': producto.stock,
                'imagen_url': producto.imagen_url or ''
            }
        }, status=status.HTTP_200_OK)
    
    except Producto.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Producto no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


# =========================
# CRUD DE CATÁLOGO - ADMIN
# =========================

@api_view(['GET', 'POST'])
def catalogo_admin(request):
    """
    GET: Listar productos del catálogo con paginación
    POST: Crear nuevo producto
    """
    try:
        # Verificar que sea admin_sistema
        usuario_id = request.data.get('usuario_id') if request.method == 'POST' else request.query_params.get('usuario_id')
        
        if usuario_id:
            try:
                cliente = Cliente.objects.get(user_id=usuario_id)
                if cliente.rol != 'admin_sistema':
                    return Response({
                        'success': False,
                        'message': 'Solo administradores pueden acceder al catálogo del admin'
                    }, status=status.HTTP_403_FORBIDDEN)
            except Cliente.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Usuario no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Si no hay usuario_id, rechazar la solicitud
            return Response({
                'success': False,
                'message': 'usuario_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if request.method == 'GET':
            # Listar productos con paginación
            page = int(request.query_params.get('page', 1))
            limit = int(request.query_params.get('limit', 10))
            search = request.query_params.get('search', '')
            
            # Filtrar productos
            queryset = Producto.objects.all()
            
            if search:
                queryset = queryset.filter(
                    Q(nombre__icontains=search) |
                    Q(sku__icontains=search) |
                    Q(descripcion__icontains=search)
                )
            
            # Contar total
            total = queryset.count()
            
            # Paginar
            offset = (page - 1) * limit
            productos = queryset.order_by('-fecha_creacion')[offset:offset + limit]
            
            productos_data = []
            for producto in productos:
                productos_data.append({
                    'id': producto.id,
                    'nombre': producto.nombre,
                    'sku': producto.sku,
                    'descripcion': producto.descripcion,
                    'precio': str(producto.precio),
                    'costo': str(producto.costo),
                    'stock': producto.stock,
                    'stock_minimo': producto.stock_minimo,
                    'categoria': {
                        'id': producto.categoria.id,
                        'nombre': producto.categoria.nombre
                    },
                    'proveedor': {
                        'id': producto.proveedor.id,
                        'nombre': producto.proveedor.nombre
                    },
                    'imagen_url': producto.imagen_url or '',
                    'activo': producto.activo,
                    'margen_ganancia': producto.margen_ganancia,
                    'stock_bajo': producto.stock_bajo,
                    'fecha_creacion': producto.fecha_creacion.isoformat()
                })
            
            return Response({
                'success': True,
                'total': total,
                'page': page,
                'limit': limit,
                'total_pages': (total + limit - 1) // limit,
                'productos': productos_data
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'POST':
            # Crear nuevo producto
            from .forms import ProductoForm
            
            form_data = {
                'nombre': request.data.get('nombre', ''),
                'sku': request.data.get('sku', ''),
                'descripcion': request.data.get('descripcion', ''),
                'precio': request.data.get('precio', 0),
                'costo': request.data.get('costo', 0),
                'stock': request.data.get('stock', 0),
                'stock_minimo': request.data.get('stock_minimo', 5),
                'categoria': request.data.get('categoria_id'),
                'proveedor': request.data.get('proveedor_id'),
                'imagen_url': request.data.get('imagen_url', ''),
                'activo': request.data.get('activo', True)
            }
            
            form = ProductoForm(form_data)
            
            if form.is_valid():
                producto = form.save(commit=False)
                # Asignar el usuario creador
                usuario = User.objects.get(id=usuario_id)
                producto.creador = usuario
                producto.save()
                
                return Response({
                    'success': True,
                    'message': 'Producto creado exitosamente',
                    'producto': {
                        'id': producto.id,
                        'nombre': producto.nombre,
                        'sku': producto.sku,
                        'descripcion': producto.descripcion,
                        'precio': str(producto.precio),
                        'costo': str(producto.costo),
                        'stock': producto.stock,
                        'stock_minimo': producto.stock_minimo,
                        'imagen_url': producto.imagen_url or '',
                        'activo': producto.activo
                    }
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': 'Error en la validación del formulario',
                    'errors': form.errors
                }, status=status.HTTP_400_BAD_REQUEST)
    
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def detalle_catalogo_admin(request, producto_id):
    """
    GET: Obtener detalle de un producto
    PUT: Actualizar producto
    DELETE: Eliminar producto
    """
    try:
        # Verificar que sea admin_sistema
        usuario_id = request.data.get('usuario_id') if request.method in ['PUT', 'DELETE'] else request.query_params.get('usuario_id')
        
        if usuario_id:
            cliente = Cliente.objects.get(user_id=usuario_id)
            if cliente.rol != 'admin_sistema':
                return Response({
                    'success': False,
                    'message': 'Solo administradores pueden acceder al catálogo del admin'
                }, status=status.HTTP_403_FORBIDDEN)
        
        producto = Producto.objects.get(id=producto_id)
        
        if request.method == 'GET':
            # Obtener detalle del producto
            return Response({
                'success': True,
                'producto': {
                    'id': producto.id,
                    'nombre': producto.nombre,
                    'sku': producto.sku,
                    'descripcion': producto.descripcion,
                    'precio': str(producto.precio),
                    'costo': str(producto.costo),
                    'stock': producto.stock,
                    'stock_minimo': producto.stock_minimo,
                    'categoria': {
                        'id': producto.categoria.id,
                        'nombre': producto.categoria.nombre
                    },
                    'proveedor': {
                        'id': producto.proveedor.id,
                        'nombre': producto.proveedor.nombre
                    },
                    'imagen_url': producto.imagen_url or '',
                    'activo': producto.activo,
                    'margen_ganancia': producto.margen_ganancia,
                    'stock_bajo': producto.stock_bajo,
                    'fecha_creacion': producto.fecha_creacion.isoformat()
                }
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'PUT':
            # Actualizar producto
            from .forms import ProductoForm
            
            # Preparar datos actualizados manteniendo los existentes
            form_data = {
                'nombre': request.data.get('nombre', producto.nombre),
                'sku': request.data.get('sku', producto.sku),
                'descripcion': request.data.get('descripcion', producto.descripcion),
                'precio': request.data.get('precio', producto.precio),
                'costo': request.data.get('costo', producto.costo),
                'stock': request.data.get('stock', producto.stock),
                'stock_minimo': request.data.get('stock_minimo', producto.stock_minimo),
                'categoria': request.data.get('categoria_id', producto.categoria.id),
                'proveedor': request.data.get('proveedor_id', producto.proveedor.id),
                'imagen_url': request.data.get('imagen_url', producto.imagen_url or ''),
                'activo': request.data.get('activo', producto.activo)
            }
            
            form = ProductoForm(form_data, instance=producto)
            
            if form.is_valid():
                producto = form.save()
                
                return Response({
                    'success': True,
                    'message': 'Producto actualizado exitosamente',
                    'producto': {
                        'id': producto.id,
                        'nombre': producto.nombre,
                        'sku': producto.sku,
                        'descripcion': producto.descripcion,
                        'precio': str(producto.precio),
                        'costo': str(producto.costo),
                        'stock': producto.stock,
                        'stock_minimo': producto.stock_minimo,
                        'imagen_url': producto.imagen_url or '',
                        'activo': producto.activo
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Error en la validación del formulario',
                    'errors': form.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            # Eliminar producto
            nombre_producto = producto.nombre
            producto.delete()
            
            return Response({
                'success': True,
                'message': f'Producto "{nombre_producto}" eliminado exitosamente'
            }, status=status.HTTP_200_OK)
    
    except Producto.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Producto no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST', 'GET'])
def obtener_sliders(request):
    """Obtener configuración de sliders (GET) o actualizar (POST)"""
    try:
        usuario_id = request.data.get('usuario_id') if request.method == 'POST' else request.query_params.get('usuario_id')
        
        if request.method == 'POST':
            # Verificar que el usuario sea vendedor o admin
            if usuario_id:
                cliente = Cliente.objects.get(user_id=usuario_id)
                if cliente.rol not in ['vendedor', 'admin_sistema']:
                    return Response({
                        'success': False,
                        'message': 'Solo vendedores y admins pueden editar sliders'
                    }, status=status.HTTP_403_FORBIDDEN)
            
            # Guardar configuración en la BD
            from django.core.cache import cache
            sliders_data = request.data.get('sliders', [])
            
            # Guardar en cache
            cache.set('sliders_config', sliders_data, timeout=None)
            
            return Response({
                'success': True,
                'message': 'Sliders actualizados exitosamente',
                'sliders': sliders_data
            }, status=status.HTTP_200_OK)
        
        else:  # GET
            # Obtener configuración de sliders
            from django.core.cache import cache
            sliders_data = cache.get('sliders_config')
            
            if not sliders_data:
                # Retornar valores por defecto CON IMÁGENES
                sliders_data = [
                    {
                        'id': 1,
                        'title': '🍷 Los Mejores Vinos Chilenos',
                        'description': 'Selección premium de los valles más reconocidos de Chile. Envío rápido a domicilio.',
                        'imagen_url': 'https://images.unsplash.com/photo-1510812431401-41d2cab2707d?w=1200&h=400&fit=crop'
                    },
                    {
                        'id': 2,
                        'title': '🍺 Cervezas Artesanales',
                        'description': 'Marcas exclusivas y artesanales. Desde Kunstmann hasta Heineken, ¡todas en Elixir!',
                        'imagen_url': 'https://images.unsplash.com/photo-1535958636474-b021ee887b13?w=1200&h=400&fit=crop'
                    },
                    {
                        'id': 3,
                        'title': '🥃 Piscos y Destilados Premium',
                        'description': 'Los mejores piscos, whiskys y rones para tus celebraciones. Calidad garantizada.',
                        'imagen_url': 'https://images.unsplash.com/photo-1608500898657-fd7c41c20df3?w=1200&h=400&fit=crop'
                    }
                ]
            
            return Response({
                'success': True,
                'sliders': sliders_data
            }, status=status.HTTP_200_OK)
    
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


# =========================
# ENDPOINTS PARA CREAR/ACTUALIZAR PRODUCTOS
# =========================

@api_view(['POST'])
def crear_producto(request):
    """Crear un nuevo producto (acceso para vendedores, gerentes y admin)"""
    try:
        usuario_id = request.data.get('usuario_id')
        
        if not usuario_id:
            return Response({
                'success': False,
                'message': 'usuario_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener usuario y cliente
        user = User.objects.get(id=usuario_id)
        cliente = Cliente.objects.get(user_id=usuario_id)
        
        # Verificar permisos
        if cliente.rol not in ['vendedor', 'gerente', 'admin_sistema']:
            return Response({
                'success': False,
                'message': f'No tienes permisos para crear productos. Tu rol es: {cliente.get_rol_display()}'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Obtener categoría y proveedor (valores por defecto si no existen)
        categoria_id = request.data.get('categoria')
        proveedor_id = request.data.get('proveedor')
        
        try:
            categoria = Categoria.objects.get(id=categoria_id) if categoria_id else Categoria.objects.first()
            proveedor = Proveedor.objects.get(id=proveedor_id) if proveedor_id else Proveedor.objects.first()
        except (Categoria.DoesNotExist, Proveedor.DoesNotExist):
            return Response({
                'success': False,
                'message': 'Categoría o Proveedor no encontrados'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not categoria or not proveedor:
            return Response({
                'success': False,
                'message': 'Debe existir al menos una Categoría y un Proveedor en el sistema'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear producto
        producto = Producto.objects.create(
            nombre=request.data.get('nombre', ''),
            sku=request.data.get('sku', ''),
            descripcion=request.data.get('descripcion', ''),
            precio=request.data.get('precio', 0),
            costo=request.data.get('costo', 0),
            stock=request.data.get('stock', 0),
            stock_minimo=request.data.get('stock_minimo', 5),
            categoria=categoria,
            proveedor=proveedor,
            imagen_url=request.data.get('imagen_url', ''),
            activo=True,
            creador=user  # Asignar el creador
        )
        
        # Manejar imagen si se proporciona
        if 'imagen' in request.FILES:
            producto.imagen = request.FILES['imagen']
            producto.save()
        
        return Response({
            'success': True,
            'message': 'Producto creado exitosamente',
            'producto': {
                'id': producto.id,
                'nombre': producto.nombre,
                'sku': producto.sku,
                'descripcion': producto.descripcion,
                'precio': float(producto.precio),
                'costo': float(producto.costo),
                'stock': producto.stock,
                'stock_minimo': producto.stock_minimo,
                'categoria': {
                    'id': producto.categoria.id,
                    'nombre': producto.categoria.nombre
                },
                'imagen_url': producto.imagen_url or '',
                'activo': producto.activo,
                'creador_id': producto.creador.id if producto.creador else None
            }
        }, status=status.HTTP_201_CREATED)
    
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Cliente no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al crear producto: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
def actualizar_stock_producto(request, producto_id):
    """Actualizar stock de un producto"""
    try:
        usuario_id = request.data.get('usuario_id')
        
        if not usuario_id:
            return Response({
                'success': False,
                'message': 'usuario_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar permisos
        cliente = Cliente.objects.get(user_id=usuario_id)
        if cliente.rol not in ['vendedor', 'gerente', 'admin_sistema']:
            return Response({
                'success': False,
                'message': 'No tienes permisos para actualizar productos'
            }, status=status.HTTP_403_FORBIDDEN)
        
        producto = Producto.objects.get(id=producto_id)
        nuevo_stock = request.data.get('nuevo_stock')
        
        if nuevo_stock is None:
            return Response({
                'success': False,
                'message': 'nuevo_stock es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        producto.stock = int(nuevo_stock)
        producto.save()
        
        return Response({
            'success': True,
            'message': 'Stock actualizado correctamente',
            'producto': {
                'id': producto.id,
                'stock': producto.stock
            }
        }, status=status.HTTP_200_OK)
    
    except Producto.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Producto no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Cliente no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'DELETE'])
def obtener_eliminar_producto(request, producto_id):
    """Obtener detalles de un producto o eliminarlo"""
    try:
        usuario_id = request.query_params.get('usuario_id') if request.method == 'GET' else request.data.get('usuario_id')
        
        if not usuario_id:
            return Response({
                'success': False,
                'message': 'usuario_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        producto = Producto.objects.get(id=producto_id)
        
        if request.method == 'GET':
            return Response({
                'success': True,
                'producto': {
                    'id': producto.id,
                    'nombre': producto.nombre,
                    'sku': producto.sku,
                    'descripcion': producto.descripcion,
                    'precio': float(producto.precio),
                    'costo': float(producto.costo),
                    'stock': producto.stock,
                    'stock_minimo': producto.stock_minimo,
                    'categoria': {
                        'id': producto.categoria.id,
                        'nombre': producto.categoria.nombre
                    },
                    'proveedor': {
                        'id': producto.proveedor.id,
                        'nombre': producto.proveedor.nombre
                    },
                    'imagen_url': producto.imagen_url or '',
                    'activo': producto.activo,
                    'fecha_creacion': producto.fecha_creacion.isoformat()
                }
            }, status=status.HTTP_200_OK)
        
        elif request.method == 'DELETE':
            # Verificar permisos
            cliente = Cliente.objects.get(user_id=usuario_id)
            if cliente.rol not in ['gerente', 'admin_sistema']:
                return Response({
                    'success': False,
                    'message': 'No tienes permisos para eliminar productos'
                }, status=status.HTTP_403_FORBIDDEN)
            
            producto_nombre = producto.nombre
            producto.delete()
            
            return Response({
                'success': True,
                'message': f'Producto "{producto_nombre}" eliminado correctamente'
            }, status=status.HTTP_200_OK)
    
    except Producto.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Producto no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Cliente no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def obtener_ventas_totales(request):
    """Obtener las ventas totales y métricas de ventas en tiempo real"""
    try:
        usuario_id = request.query_params.get('usuario_id')
        
        if not usuario_id:
            return Response({
                'success': False,
                'message': 'usuario_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar permisos
        cliente = Cliente.objects.get(user_id=usuario_id)
        if cliente.rol not in ['gerente', 'admin_sistema']:
            return Response({
                'success': False,
                'message': 'No tienes permisos para ver estas métricas'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Calcular métricas de ventas
        pedidos = Pedido.objects.all()
        # Incluir todos los pedidos excepto los cancelados
        pedidos_activos = pedidos.exclude(estado='cancelado')
        
        total_ventas = pedidos_activos.aggregate(total=Sum('total'))['total'] or 0
        total_pedidos = pedidos.count()
        total_pedidos_pagados = pedidos_activos.count()
        
        # Productos más vendidos
        productos_vendidos = DetallesPedido.objects.values('producto__nombre', 'producto__id').annotate(
            cantidad_total=Sum('cantidad'),
            ventas_total=Sum('subtotal')
        ).order_by('-cantidad_total')[:5]
        
        # Conversión a lista
        productos_vendidos_list = list(productos_vendidos)
        
        return Response({
            'success': True,
            'ventas': {
                'total_ventas': float(total_ventas),
                'total_pedidos': total_pedidos,
                'total_pedidos_pagados': total_pedidos_pagados,
                'productos_vendidos': productos_vendidos_list
            }
        }, status=status.HTTP_200_OK)
    
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Cliente no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
