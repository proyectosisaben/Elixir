from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from .models import Producto, Categoria, Cliente, Pedido, DetallesPedido, AuditLog, LogSistema, EstadisticaVisita, SolicitudAutorizacion, Cupon, PromocionProducto, Reclamo, ComentarioReclamo, DireccionEnvio, REGIONES_CHILE, Proveedor, ReporteFinanciero
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncYear
from django.http import JsonResponse
from .forms import RegistroClienteForm
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from decimal import Decimal
import secrets
from datetime import datetime
import uuid
from .email_service import EmailPedidoService

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
                
                # Generar token simple y guardarlo en Cliente.api_token para autenticación por header
                token = secrets.token_urlsafe(32)
                if cliente:
                    cliente.api_token = token
                    cliente.save()
                else:
                    # si no existe cliente creado previamente, crear uno para esta cuenta
                    from datetime import date
                    cliente, created = Cliente.objects.get_or_create(
                        user=user,
                        defaults={
                            'fecha_nacimiento': date(2000, 1, 1),
                            'email_confirmado': True,
                            'rol': rol,
                            'api_token': token,
                        }
                    )
                    if not created:
                        cliente.api_token = token
                        cliente.save()

                # Registrar auditoría de login exitoso
                from django.core.exceptions import ImproperlyConfigured
                try:
                    ip_address = _get_client_ip(request)
                    user_agent = request.META.get('HTTP_USER_AGENT', '')

                    AuditLog.registrar_cambio(
                        usuario=user,
                        tipo_accion='login',
                        modelo='Cliente',
                        id_objeto=str(user.id),
                        descripcion=f'Inicio de sesión exitoso para {user.email} con rol {rol}',
                        ip_address=ip_address,
                        user_agent=user_agent
                    )

                    # Registrar log del sistema
                    LogSistema.registrar_evento(
                        nivel='info',
                        categoria='seguridad',
                        mensaje=f'Usuario {user.email} inició sesión exitosamente',
                        usuario=user,
                        datos_extra={'rol': rol, 'login_method': 'web'},
                        ip_address=ip_address,
                        user_agent=user_agent,
                        modulo='views.login',
                        funcion='login_cliente'
                    )
                except Exception as audit_error:
                    # No fallar el login por error de auditoría
                    print(f"Error registrando auditoría de login: {audit_error}")

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


@api_view(['GET'])
def ventas_analiticas(request):
    """Endpoint para HU13 - Analizar tendencias de ventas.
    Query params:
      period: daily|weekly|monthly|yearly (default monthly)
      fecha_inicio, fecha_fin (ISO)
      categoria_id, producto_id, vendedor_id
      compare: true para enviar período anterior comparativo
      user_id: ID del usuario para autenticación
    Acceso: gerente y admin_sistema
    """
    # Autenticación por user_id (consistente con otras vistas)
    usuario_id = request.query_params.get('user_id')

    if not usuario_id:
        return Response({
            'success': False,
            'message': 'user_id es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(id=usuario_id)
        cliente = Cliente.objects.get(user=user)
        if cliente.rol not in ['gerente', 'admin_sistema']:
            return Response({
                'success': False,
                'message': 'Acceso denegado. Solo gerentes y administradores pueden ver análisis de ventas.'
            }, status=status.HTTP_403_FORBIDDEN)
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

    period = request.query_params.get('period', 'monthly')
    fecha_inicio = request.query_params.get('fecha_inicio')
    fecha_fin = request.query_params.get('fecha_fin')
    categoria_id = request.query_params.get('categoria_id')
    producto_id = request.query_params.get('producto_id')
    vendedor_id = request.query_params.get('vendedor_id')
    compare = request.query_params.get('compare') in ['true', '1', 'True']

    # Logging de filtros
    import sys
    print(f'[VENTAS_ANALITICAS] Filtros recibidos:', file=sys.stderr)
    print(f'  - period: {period}', file=sys.stderr)
    print(f'  - categoria_id: {categoria_id}', file=sys.stderr)
    print(f'  - producto_id: {producto_id}', file=sys.stderr)
    print(f'  - vendedor_id: {vendedor_id}', file=sys.stderr)
    print(f'  - fecha_inicio: {fecha_inicio}', file=sys.stderr)
    print(f'  - fecha_fin: {fecha_fin}', file=sys.stderr)

    # Base queryset: detalles de pedidos cuya orden está pagada/enviado/entregado (ventas reales)
    qs = DetallesPedido.objects.select_related('pedido', 'producto', 'producto__categoria', 'pedido__usuario')
    qs = qs.exclude(pedido__estado__in=['pendiente', 'cancelado'])

    # Filtrar por fechas
    if fecha_inicio:
        try:
            dt = datetime.fromisoformat(fecha_inicio)
            qs = qs.filter(pedido__fecha_pedido__gte=dt)
        except Exception:
            pass
    if fecha_fin:
        try:
            dt = datetime.fromisoformat(fecha_fin)
            qs = qs.filter(pedido__fecha_pedido__lte=dt)
        except Exception:
            pass

    if categoria_id:
        qs = qs.filter(producto__categoria_id=categoria_id)
    if producto_id:
        qs = qs.filter(producto_id=producto_id)
    if vendedor_id:
        qs = qs.filter(pedido__vendedor_id=vendedor_id)

    # Elegir truncación por periodo
    if period == 'daily':
        trunc = TruncDay('pedido__fecha_pedido')
    elif period == 'weekly':
        trunc = TruncWeek('pedido__fecha_pedido')
    elif period == 'yearly':
        trunc = TruncYear('pedido__fecha_pedido')
    else:
        trunc = TruncMonth('pedido__fecha_pedido')

    agregados = qs.annotate(period=trunc).values('period').annotate(total=Sum('subtotal')).order_by('period')

    series = []
    for a in agregados:
        period_value = a['period']
        series.append({'period': period_value.isoformat() if period_value else None, 'total': float(a['total'] or 0)})

    # Breakdown por categoría y por producto (top 10)
    by_category_qs = qs.values('producto__categoria__id', 'producto__categoria__nombre').annotate(total=Sum('subtotal')).order_by('-total')[:20]
    by_category = [{'categoria_id': c['producto__categoria__id'], 'categoria': c['producto__categoria__nombre'], 'total': float(c['total'] or 0)} for c in by_category_qs]

    by_product_qs = qs.values('producto__id', 'producto__nombre').annotate(total=Sum('subtotal')).order_by('-total')[:20]
    by_product = [{'producto_id': p['producto__id'], 'producto': p['producto__nombre'], 'total': float(p['total'] or 0)} for p in by_product_qs]

    # Log de resultados
    import sys
    total_ventas = qs.aggregate(total=Sum('subtotal'))['total'] or 0
    print(f'[VENTAS_ANALITICAS] Resultados:', file=sys.stderr)
    print(f'  - Total de ventas: ${total_ventas}', file=sys.stderr)
    print(f'  - Categorías encontradas: {len(by_category)}', file=sys.stderr)
    print(f'  - Productos encontrados: {len(by_product)}', file=sys.stderr)
    print(f'  - Categorías: {[c["categoria"] for c in by_category]}', file=sys.stderr)

    # Totales para comparación si se solicita
    compare_data = None
    if compare and fecha_inicio and fecha_fin:
        try:
            start = datetime.fromisoformat(fecha_inicio)
            end = datetime.fromisoformat(fecha_fin)
            # calcular periodo anterior de igual duración
            delta = end - start
            prev_start = start - delta
            prev_end = start
            prev_qs = DetallesPedido.objects.select_related('pedido').exclude(pedido__estado__in=['pendiente', 'cancelado']).filter(pedido__fecha_pedido__gte=prev_start, pedido__fecha_pedido__lt=prev_end)
            total_current = qs.aggregate(total=Sum('subtotal'))['total'] or 0
            total_prev = prev_qs.aggregate(total=Sum('subtotal'))['total'] or 0
            compare_data = {'current': float(total_current), 'previous': float(total_prev)}
        except Exception:
            compare_data = None

    return Response({
        'success': True,
        'data': {
            'series': series,
            'by_category': by_category,
            'by_product': by_product,
            'compare': compare_data,
        }
    })


@api_view(['GET'])
def ventas_exportar(request):
    """Exportar datos agregados de ventas a PDF profesional (mismos params que ventas_analiticas)"""
    # Autenticación por user_id (consistente con otras vistas)
    usuario_id = request.query_params.get('user_id')

    if not usuario_id:
        return Response({
            'success': False,
            'message': 'user_id es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(id=usuario_id)
        cliente = Cliente.objects.get(user=user)
        if cliente.rol not in ['gerente', 'admin_sistema']:
            return Response({
                'success': False,
                'message': 'Acceso denegado. Solo gerentes y administradores pueden exportar análisis de ventas.'
            }, status=status.HTTP_403_FORBIDDEN)
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

    # Obtener parámetros
    period = request.query_params.get('period', 'monthly')
    fecha_inicio = request.query_params.get('fecha_inicio')
    fecha_fin = request.query_params.get('fecha_fin')
    categoria_id = request.query_params.get('categoria_id')
    producto_id = request.query_params.get('producto_id')
    vendedor_id = request.query_params.get('vendedor_id')
    compare = request.query_params.get('compare') in ['true', '1', 'True']

    # Base queryset: detalles de pedidos cuya orden está pagada/enviado/entregado
    qs = DetallesPedido.objects.select_related('pedido', 'producto', 'producto__categoria', 'pedido__usuario')
    qs = qs.exclude(pedido__estado__in=['pendiente', 'cancelado'])

    # Filtrar por fechas
    if fecha_inicio:
        try:
            dt = datetime.fromisoformat(fecha_inicio)
            qs = qs.filter(pedido__fecha_pedido__gte=dt)
        except Exception:
            pass
    if fecha_fin:
        try:
            dt = datetime.fromisoformat(fecha_fin)
            qs = qs.filter(pedido__fecha_pedido__lte=dt)
        except Exception:
            pass

    if categoria_id:
        qs = qs.filter(producto__categoria_id=categoria_id)
    if producto_id:
        qs = qs.filter(producto_id=producto_id)
    if vendedor_id:
        qs = qs.filter(pedido__vendedor_id=vendedor_id)

    # Elegir truncación por periodo
    if period == 'daily':
        trunc = TruncDay('pedido__fecha_pedido')
    elif period == 'weekly':
        trunc = TruncWeek('pedido__fecha_pedido')
    elif period == 'yearly':
        trunc = TruncYear('pedido__fecha_pedido')
    else:
        trunc = TruncMonth('pedido__fecha_pedido')

    # Agregados por período
    agregados = qs.annotate(period=trunc).values('period').annotate(total=Sum('subtotal')).order_by('period')
    series = []
    for a in agregados:
        period_value = a['period']
        series.append({'period': period_value.isoformat() if period_value else None, 'total': float(a['total'] or 0)})

    # Breakdown por categoría
    by_category_qs = qs.values('producto__categoria__id', 'producto__categoria__nombre').annotate(total=Sum('subtotal')).order_by('-total')
    by_category = [{'categoria_id': c['producto__categoria__id'], 'categoria': c['producto__categoria__nombre'], 'total': float(c['total'] or 0)} for c in by_category_qs]

    # Breakdown por producto (top 20)
    by_product_qs = qs.values('producto__id', 'producto__nombre').annotate(total=Sum('subtotal')).order_by('-total')[:20]
    by_product = [{'producto_id': p['producto__id'], 'producto': p['producto__nombre'], 'total': float(p['total'] or 0)} for p in by_product_qs]

    # Datos de comparación si se solicita
    compare_data = None
    if compare and fecha_inicio and fecha_fin:
        try:
            start = datetime.fromisoformat(fecha_inicio)
            end = datetime.fromisoformat(fecha_fin)
            delta = end - start
            prev_start = start - delta
            prev_end = start
            prev_qs = DetallesPedido.objects.select_related('pedido').exclude(pedido__estado__in=['pendiente', 'cancelado']).filter(pedido__fecha_pedido__gte=prev_start, pedido__fecha_pedido__lt=prev_end)
            if categoria_id:
                prev_qs = prev_qs.filter(producto__categoria_id=categoria_id)
            if producto_id:
                prev_qs = prev_qs.filter(producto_id=producto_id)
            if vendedor_id:
                prev_qs = prev_qs.filter(pedido__vendedor_id=vendedor_id)
            
            total_current = qs.aggregate(total=Sum('subtotal'))['total'] or 0
            total_prev = prev_qs.aggregate(total=Sum('subtotal'))['total'] or 0
            compare_data = {'current': float(total_current), 'previous': float(total_prev)}
        except Exception:
            compare_data = None

    # Generar PDF usando el nuevo servicio
    from .reportes_service import GeneradorExportacionAnalisisVentas
    
    generador = GeneradorExportacionAnalisisVentas(
        series_data=series,
        by_category=by_category,
        by_product=by_product,
        compare_data=compare_data,
        period=period
    )
    
    pdf_buffer = generador.generar_pdf()
    
    # Retornar respuesta con PDF
    from django.http import HttpResponse
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="analisis_ventas.pdf"'
    return response

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
    """API endpoint para catálogo de productos con filtros avanzados"""
    try:
        productos = Producto.objects.filter(activo=True)
        categorias_qs = Categoria.objects.filter(activa=True)
        
        # Obtener parámetros de filtros
        busqueda = request.GET.get('q', '').strip()
        categoria_ids = request.GET.getlist('categorias')
        proveedor_id = request.GET.get('proveedor')
        precio_min = request.GET.get('precio_min')
        precio_max = request.GET.get('precio_max')
        disponible = request.GET.get('disponible')  # 'true' o 'false'
        
        # Filtro de búsqueda por nombre, descripción y SKU
        if busqueda:
            productos = productos.filter(
                Q(nombre__icontains=busqueda) |
                Q(descripcion__icontains=busqueda) |
                Q(sku__icontains=busqueda)
            )
        
        # Filtro por categorías múltiples
        if categoria_ids:
            productos = productos.filter(categoria_id__in=categoria_ids)
        
        # Filtro por proveedor
        if proveedor_id:
            productos = productos.filter(proveedor_id=proveedor_id)
        
        # Filtro por rango de precio
        if precio_min:
            try:
                precio_min = float(precio_min)
                productos = productos.filter(precio__gte=precio_min)
            except ValueError:
                pass
        
        if precio_max:
            try:
                precio_max = float(precio_max)
                productos = productos.filter(precio__lte=precio_max)
            except ValueError:
                pass
        
        # Filtro por disponibilidad
        if disponible:
            if disponible.lower() == 'true':
                productos = productos.filter(stock__gt=0)
            elif disponible.lower() == 'false':
                productos = productos.filter(stock__lte=0)
        
        # Obtener proveedores para filtrado
        proveedores = {}
        for prod in productos:
            if prod.proveedor_id not in proveedores:
                proveedores[prod.proveedor_id] = prod.proveedor.nombre
        
        # Calcular rango de precios disponibles
        precio_min_disponible = productos.order_by('precio').first()
        precio_max_disponible = productos.order_by('-precio').first()
        
        precio_rango_min = float(precio_min_disponible.precio) if precio_min_disponible else 0
        precio_rango_max = float(precio_max_disponible.precio) if precio_max_disponible else 0

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
                'disponible': p.stock > 0,
                'descripcion': p.descripcion,
                'imagen': imagen_url,
                'imagen_url': p.imagen_url or imagen_url,
                'categoria': {'id': p.categoria.id, 'nombre': p.categoria.nombre},
                'proveedor': {'id': p.proveedor.id, 'nombre': p.proveedor.nombre},
            })

        categorias = [{'id': c.id, 'nombre': c.nombre} for c in categorias_qs]
        proveedores_lista = [{'id': k, 'nombre': v} for k, v in proveedores.items()]

        return JsonResponse({
            'productos': productos_data,
            'categorias': categorias,
            'proveedores': proveedores_lista,
            'total_resultados': len(productos_data),
            'rango_precios': {
                'minimo': precio_rango_min,
                'maximo': precio_rango_max,
            },
            'filtros': {
                'busqueda': busqueda,
                'categorias': categoria_ids,
                'proveedor': proveedor_id,
                'precio_min': precio_min,
                'precio_max': precio_max,
                'disponible': disponible,
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


@api_view(['GET'])
def api_categorias(request):
    """Endpoint para obtener todas las categorías activas"""
    try:
        categorias_qs = Categoria.objects.filter(activa=True).order_by('nombre')
        categorias = [{'id': c.id, 'nombre': c.nombre} for c in categorias_qs]
        return Response({
            'success': True,
            'categorias': categorias,
            'total': len(categorias)
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al obtener categorías: {str(e)}',
            'categorias': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def api_productos_lista(request):
    """Endpoint para obtener lista simple de productos activos"""
    productos_qs = Producto.objects.filter(activo=True)
    productos = [{'id': p.id, 'nombre': p.nombre} for p in productos_qs]
    return Response(productos)


@api_view(['POST'])
def cambiar_rol_cliente(request):
    """API endpoint para cambiar el rol de un cliente (solo admin)"""
    if request.method == 'POST':
        admin_usuario_id = request.data.get('admin_usuario_id')
        usuario_id = request.data.get('usuario_id')
        nuevo_rol = request.data.get('rol')

        # Verificar permisos del administrador
        if not admin_usuario_id:
            return Response({
                'success': False,
                'message': 'admin_usuario_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            admin_user = User.objects.get(id=admin_usuario_id)
            admin_cliente = Cliente.objects.get(user=admin_user)

            if admin_cliente.rol != 'admin_sistema':
                return Response({
                    'success': False,
                    'message': 'Acceso denegado. Solo administradores pueden cambiar roles.'
                }, status=status.HTTP_403_FORBIDDEN)

        except (User.DoesNotExist, Cliente.DoesNotExist):
            return Response({
                'success': False,
                'message': 'Administrador no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

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
            # Preparar datos para auditoría antes del cambio
            rol_anterior = cliente.rol if not created else None

            if not created:
                cliente.rol = nuevo_rol
                cliente.save()

            # Registrar auditoría del cambio de rol
            try:
                usuario_admin, ip_address, user_agent = _obtener_info_usuario(request)

                AuditLog.registrar_cambio(
                    usuario=usuario_admin,
                    tipo_accion='modificar',
                    modelo='Cliente',
                    id_objeto=str(user.id),
                    datos_anteriores={'rol': rol_anterior} if rol_anterior else {},
                    datos_nuevos={'rol': nuevo_rol},
                    descripcion=f'Cambio de rol para {user.email}: {rol_anterior or "Nuevo"} → {nuevo_rol}',
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            except Exception as audit_error:
                # No fallar el cambio de rol por error de auditoría
                print(f"Error registrando auditoría de cambio de rol: {audit_error}")

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
    """API endpoint para listar todos los clientes con sus roles - Solo administradores"""
    try:
        # Verificar permisos - Solo administradores pueden ver todos los clientes
        usuario_id = request.query_params.get('usuario_id')
        if not usuario_id:
            return Response({
                'success': False,
                'message': 'usuario_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(id=usuario_id)
        cliente = Cliente.objects.get(user=user)

        if cliente.rol != 'admin_sistema':
            return Response({
                'success': False,
                'message': 'Acceso denegado. Solo administradores pueden gestionar roles.'
            }, status=status.HTTP_403_FORBIDDEN)

        clientes = Cliente.objects.select_related('user').all()
        clientes_data = []
        
        for cliente in clientes:
            clientes_data.append({
                'usuario_id': cliente.user_id,
                'email': cliente.user.email,
                'nombre': cliente.user.first_name or cliente.user.username,
                'rol': cliente.rol,
                'rol_display': cliente.get_rol_display(),
                'fecha_nacimiento': cliente.fecha_nacimiento.isoformat() if cliente.fecha_nacimiento else None,
                'email_confirmado': cliente.email_confirmado,
                'fecha_creacion': cliente.user.date_joined.isoformat() if cliente.user.date_joined else None
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
            direccion_envio_id = request.data.get('direccion_envio_id')
            metodo_envio = request.data.get('metodo_envio', 'estandar')
            costo_envio_raw = request.data.get('costo_envio', 0)
            costo_envio = Decimal(str(costo_envio_raw)) if costo_envio_raw is not None else Decimal('0')

            print(f"DEBUG: usuario_id={usuario_id}, items={items}")  # Debug

            if not usuario_id or not items:
                return Response({
                    'success': False,
                    'message': 'Usuario_id e items son requeridos'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Obtener usuario y cliente
            user = User.objects.get(id=usuario_id)
            cliente = Cliente.objects.get(user=user)

            # Aplicar promociones a productos y calcular subtotal
            subtotal = Decimal('0')
            items_con_precio_actualizado = []
            from django.db import connection
            
            for item in items:
                producto = Producto.objects.get(id=item['producto_id'])
                
                # Verificar stock
                if producto.stock < item['cantidad']:
                    return Response({
                        'success': False,
                        'message': f'Stock insuficiente para {producto.nombre}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Aplicar promoción si existe
                precio_final = producto.precio_con_descuento()  # Retorna Decimal
                cantidad = Decimal(str(item['cantidad']))
                subtotal_item = precio_final * cantidad
                subtotal += subtotal_item
                
                items_con_precio_actualizado.append({
                    'producto_id': producto.id,
                    'cantidad': item['cantidad'],
                    'precio_original': float(producto.precio),
                    'precio_final': float(precio_final),
                    'subtotal': float(subtotal_item)
                })
            
            # Aplicar cupón si se proporciona
            codigo_cupon_raw = request.data.get('codigo_cupon')
            codigo_cupon = str(codigo_cupon_raw or '').strip().upper() if codigo_cupon_raw else ''
            descuento_cupon = 0
            cupon_usado = None
            
            if codigo_cupon:
                try:
                    cupon = Cupon.objects.get(codigo=codigo_cupon)
                    # Convertir subtotal a float para comparación con monto_minimo
                    subtotal_float = float(subtotal)
                    monto_minimo_float = float(cupon.monto_minimo)
                    
                    if cupon.es_valido() and subtotal_float >= monto_minimo_float:
                        descuento_decimal = cupon.calcular_descuento(subtotal_float)
                        descuento_cupon = float(descuento_decimal)
                        if descuento_cupon > 0:
                            cupon_usado = cupon
                            cupon.usar()  # Incrementar contador de usos
                except Cupon.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'Cupón no encontrado'
                    }, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    return Response({
                        'success': False,
                        'message': f'Error al aplicar cupón: {str(e)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Obtener dirección de envío si se proporciona
            direccion_envio = None
            if direccion_envio_id:
                try:
                    direccion_envio = DireccionEnvio.objects.get(id=direccion_envio_id, cliente=cliente)
                except DireccionEnvio.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'Dirección de envío no encontrada'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Calcular total final (convertir descuento_cupon a Decimal si es necesario)
            descuento_decimal = Decimal(str(descuento_cupon)) if isinstance(descuento_cupon, (int, float)) else descuento_cupon
            total = subtotal - descuento_decimal + costo_envio
            if total < 0:
                total = Decimal('0')

            # Generar número de pedido único
            numero_pedido = f"PED-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

            # Crear pedido con la estructura correcta de Railway
            # Convertir todos los valores Decimal a float para guardar en DecimalField
            pedido = Pedido.objects.create(
                cliente=cliente,
                numero_pedido=numero_pedido,
                total=float(total),
                subtotal=float(subtotal),
                impuesto=0,
                descuento=float(descuento_decimal),
                estado='pendiente',
                metodo_pago=metodo_pago,
                vendedor=None,  # Se asignará cuando el vendedor procese
                direccion_envio=direccion_envio,
                metodo_envio=metodo_envio,
                costo_envio=float(costo_envio)
            )
            
            # Crear detalles del pedido usando SQL directo con precios actualizados
            for item_actualizado in items_con_precio_actualizado:
                producto = Producto.objects.get(id=item_actualizado['producto_id'])
                
                # Crear detalle del pedido usando SQL directo
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO inventario_detallespedido
                        (pedido_id, producto_id, cantidad, precio_unitario, subtotal)
                        VALUES (%s, %s, %s, %s, %s)
                    """, [
                        pedido.id, 
                        producto.id, 
                        item_actualizado['cantidad'], 
                        item_actualizado['precio_final'], 
                        item_actualizado['subtotal']
                    ])

                # Reducir stock
                producto.stock -= item['cantidad']
                producto.save()
            
            # Registrar auditoría de creación de pedido
            try:
                ip_address = _get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')

                # Preparar datos del pedido para auditoría
                datos_pedido = {
                    'numero_pedido': numero_pedido,
                    'total': float(pedido.total),
                    'subtotal': float(pedido.subtotal),
                    'descuento': float(pedido.descuento),
                    'costo_envio': float(pedido.costo_envio),
                    'estado': pedido.estado,
                    'metodo_pago': pedido.metodo_pago,
                    'metodo_envio': pedido.metodo_envio,
                    'cliente_email': pedido.cliente.user.email,
                    'items': items_con_precio_actualizado,
                    'codigo_cupon': codigo_cupon if cupon_usado else None,
                    'direccion_envio': direccion_envio.direccion_completa if direccion_envio else None
                }

                AuditLog.registrar_cambio(
                    usuario=user,
                    tipo_accion='crear',
                    modelo='Pedido',
                    id_objeto=str(pedido.id),
                    datos_nuevos=datos_pedido,
                    descripcion=f'Pedido {numero_pedido} creado por {user.email} - Total: ${pedido.total}',
                    ip_address=ip_address,
                    user_agent=user_agent
                )

                # Registrar log del sistema
                LogSistema.registrar_evento(
                    nivel='info',
                    categoria='venta',
                    mensaje=f'Nuevo pedido {numero_pedido} creado por {user.email}',
                    usuario=user,
                    datos_extra={
                        'pedido_id': pedido.id,
                        'numero_pedido': numero_pedido,
                        'total': float(pedido.total),
                        'items_count': len(items)
                    },
                    ip_address=ip_address,
                    user_agent=user_agent,
                    modulo='views.checkout',
                    funcion='crear_pedido'
                )
            except Exception as audit_error:
                # No fallar la creación del pedido por error de auditoría
                print(f"Error registrando auditoría de pedido: {audit_error}")

            # Enviar email de confirmación al cliente
            try:
                EmailPedidoService.enviar_confirmacion_pedido(pedido)
            except Exception as email_error:
                # No fallar la creación del pedido por error de email
                print(f"Error enviando email de confirmación: {email_error}")

            return Response({
                'success': True,
                'message': 'Pedido creado exitosamente',
                'pedido_id': pedido.id,
                'numero_pedido': numero_pedido,
                'subtotal': float(pedido.subtotal),
                'descuento': float(pedido.descuento),
                'total': float(pedido.total),
                'estado': pedido.estado,
                'cupon_aplicado': codigo_cupon if cupon_usado else None
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
        
        user = User.objects.get(id=usuario_id)
        cliente = Cliente.objects.get(user=user)

        # En el perfil personal, siempre mostrar solo los pedidos del cliente actual
        # independientemente de su rol. Los administradores que necesiten ver todos
        # los pedidos deberían usar una API diferente específicamente para eso.
        pedidos = Pedido.objects.filter(cliente=cliente)
        
        pedidos_data = []
        for pedido in pedidos:
            # Obtener detalles del pedido usando SQL directo
            from django.db import connection
            detalles = []
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT dp.producto_id, p.nombre, dp.cantidad, dp.precio_unitario, dp.subtotal
                    FROM inventario_detallespedido dp
                    JOIN inventario_producto p ON dp.producto_id = p.id
                    WHERE dp.pedido_id = %s
                """, [pedido.id])
                for row in cursor.fetchall():
                    detalles.append({
                        'producto_id': row[0],
                        'producto_nombre': row[1],
                        'cantidad': row[2],
                        'precio_unitario': float(row[3]),
                        'subtotal': float(row[4])
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
            
            # VALIDACIÓN: Vendedores, gerentes y admin_sistema pueden acceder
            if cliente.rol not in ['vendedor', 'gerente', 'admin_sistema']:
                return Response({
                    'success': False,
                    'message': f'❌ Acceso denegado. Solo vendedores, gerentes y administradores pueden acceder al dashboard. Tu rol es: {cliente.get_rol_display()}'
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Calcular estadísticas
        pedidos = Pedido.objects.all()
        # Incluir todos los pedidos excepto los cancelados
        pedidos_activos = pedidos.exclude(estado='cancelado')
        
        total_ventas = pedidos_activos.aggregate(total=Sum('total'))['total'] or 0
        total_pedidos = pedidos.count()
        total_clientes = Cliente.objects.filter(rol='cliente').count()
        
        # Productos más vendidos - usar SQL directo
        from django.db import connection
        productos_vendidos = []
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT p.nombre, SUM(dp.cantidad) as cantidad_total,
                       SUM(dp.subtotal) as ventas_total
                FROM inventario_detallespedido dp
                JOIN inventario_producto p ON dp.producto_id = p.id
                GROUP BY p.nombre
                ORDER BY cantidad_total DESC
                LIMIT 5
            """)
            for row in cursor.fetchall():
                productos_vendidos.append({
                    'producto__nombre': row[0],
                    'cantidad_total': row[1],
                    'ventas_total': float(row[2])
                })
        
        # Ingresos por estado
        ingresos_por_estado = {}
        for estado, _ in [('pagado', 1), ('en_preparacion', 1), ('enviado', 1), ('entregado', 1)]:
            total = pedidos.filter(estado=estado).aggregate(total=Sum('total'))['total'] or 0
            ingresos_por_estado[estado] = float(total)

        # Ventas agrupadas por día (últimos 30 días) - HU 50
        from django.db.models.functions import TruncDay
        from datetime import datetime, timedelta
        hace_30_dias = datetime.now() - timedelta(days=30)

        ventas_por_dia = pedidos_activos.filter(fecha_pedido__gte=hace_30_dias).annotate(
            dia=TruncDay('fecha_pedido')
        ).values('dia').annotate(
            total_ventas=Sum('total'),
            cantidad_pedidos=Count('id')
        ).order_by('dia')

        ventas_diarias = []
        for venta in ventas_por_dia:
            ventas_diarias.append({
                'fecha': venta['dia'].isoformat(),
                'total_ventas': float(venta['total_ventas'] or 0),
                'cantidad_pedidos': venta['cantidad_pedidos']
            })

        return Response({
            'success': True,
            'estadisticas': {
                'total_ventas': float(total_ventas),
                'total_pedidos': total_pedidos,
                'total_clientes': total_clientes,
                'pedidos_pagados': pedidos_activos.count(),
                'productos_vendidos': list(productos_vendidos),
                'ingresos_por_estado': ingresos_por_estado,
                'ventas_por_dia': ventas_diarias
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
                    'fecha_nacimiento': cliente.fecha_nacimiento.isoformat() if cliente.fecha_nacimiento else None,
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
    """Marcar un pedido como pagado (por vendedor/gerente/admin)"""
    try:
        usuario_id = request.data.get('usuario_id')
        pedido_id = request.data.get('pedido_id')
        
        if not usuario_id or not pedido_id:
            return Response({
                'success': False,
                'message': 'usuario_id y pedido_id son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.get(id=usuario_id)
        
        # Permitir superuser/staff (admin Django)
        if not (user.is_superuser or user.is_staff):
            cliente = Cliente.objects.get(user_id=usuario_id)
            # Solo vendedores, gerentes y admin_sistema pueden marcar como pagado
            if cliente.rol not in ['vendedor', 'gerente', 'admin_sistema']:
                return Response({
                    'success': False,
                    'message': 'Solo vendedores, gerentes y administradores pueden realizar esta acción'
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


@api_view(['POST'])
def cambiar_estado_pedido(request):
    """
    API endpoint genérico para cambiar el estado de un pedido.
    Estados permitidos: en_preparacion, enviado, entregado, cancelado
    """
    try:
        usuario_id = request.data.get('usuario_id')
        pedido_id = request.data.get('pedido_id')
        nuevo_estado = request.data.get('estado')

        if not usuario_id or not pedido_id or not nuevo_estado:
            return Response({
                'success': False,
                'message': 'usuario_id, pedido_id y estado son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(id=usuario_id)

        # Permitir superuser/staff (admin Django)
        if not (user.is_superuser or user.is_staff):
            try:
                cliente = Cliente.objects.get(user_id=usuario_id)
                # Solo vendedores, gerentes y admin_sistema pueden cambiar estados
                if cliente.rol not in ['vendedor', 'gerente', 'admin_sistema']:
                    return Response({
                        'success': False,
                        'message': 'Acceso denegado. Solo vendedores, gerentes y administradores pueden cambiar estados de pedidos.'
                    }, status=status.HTTP_403_FORBIDDEN)
            except Cliente.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Usuario no tiene un cliente asociado.'
                }, status=status.HTTP_403_FORBIDDEN)

        # Validar estado permitido
        estados_permitidos = ['pagado', 'en_preparacion', 'enviado', 'entregado', 'cancelado']
        if nuevo_estado not in estados_permitidos:
            return Response({
                'success': False,
                'message': f'Estado no válido. Estados permitidos: {", ".join(estados_permitidos)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Obtener y validar pedido
        try:
            pedido = Pedido.objects.get(id=pedido_id)
        except Pedido.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Pedido no encontrado.'
            }, status=status.HTTP_404_NOT_FOUND)

        estado_anterior = pedido.estado

        # Validar transiciones de estado permitidas
        if nuevo_estado == 'pagado':
            if pedido.estado != 'pendiente':
                return Response({
                    'success': False,
                    'message': f'No se puede marcar como pagado un pedido que está en estado "{pedido.get_estado_display()}".'
                }, status=status.HTTP_400_BAD_REQUEST)
        elif nuevo_estado == 'en_preparacion':
            if pedido.estado not in ['pendiente', 'pagado']:
                return Response({
                    'success': False,
                    'message': f'No se puede marcar como en preparación un pedido que está en estado "{pedido.get_estado_display()}".'
                }, status=status.HTTP_400_BAD_REQUEST)
        elif nuevo_estado == 'enviado':
            if pedido.estado not in ['pagado', 'en_preparacion']:
                return Response({
                    'success': False,
                    'message': f'No se puede marcar como enviado un pedido que está en estado "{pedido.get_estado_display()}".'
                }, status=status.HTTP_400_BAD_REQUEST)
        elif nuevo_estado == 'entregado':
            if pedido.estado != 'enviado':
                return Response({
                    'success': False,
                    'message': f'No se puede marcar como entregado un pedido que está en estado "{pedido.get_estado_display()}".'
                }, status=status.HTTP_400_BAD_REQUEST)
        elif nuevo_estado == 'cancelado':
            if pedido.estado == 'entregado':
                return Response({
                    'success': False,
                    'message': 'No se puede cancelar un pedido que ya fue entregado.'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Aplicar cambio de estado
        if nuevo_estado == 'pagado':
            pedido.marcar_como_pagado()
        elif nuevo_estado == 'en_preparacion':
            pedido.estado = 'en_preparacion'
            pedido.save()
        elif nuevo_estado == 'enviado':
            pedido.marcar_como_enviado()
        elif nuevo_estado == 'entregado':
            pedido.marcar_como_entregado()
        elif nuevo_estado == 'cancelado':
            pedido.estado = 'cancelado'
            pedido.save()

        # Registrar en auditoría
        from .models import AuditLog
        AuditLog.registrar_cambio(
            usuario=user,
            tipo_accion='modificar',
            modelo='Pedido',
            id_objeto=pedido.id,
            datos_anteriores={'estado': estado_anterior},
            datos_nuevos={'estado': nuevo_estado},
            descripcion=f'Pedido {pedido.numero_pedido} cambió de estado "{estado_anterior}" a "{nuevo_estado}" por {user.username}'
        )

        # Enviar notificación por email al cliente según el cambio de estado
        emails_enviados = []
        try:
            emails_enviados = EmailPedidoService.enviar_notificacion_por_estado(
                pedido, estado_anterior, nuevo_estado
            )
        except Exception as email_error:
            # No fallar el cambio de estado por error de email
            print(f"Error enviando email de notificación: {email_error}")

        mensaje_respuesta = f'Pedido {pedido.numero_pedido} cambió a estado "{pedido.get_estado_display()}" exitosamente.'
        if emails_enviados:
            mensaje_respuesta += f' Se notificó al cliente por email.'

        return Response({
            'success': True,
            'message': mensaje_respuesta,
            'estado': pedido.estado,
            'estado_display': pedido.get_estado_display(),
            'email_enviado': len(emails_enviados) > 0
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error al cambiar estado del pedido: {str(e)}'
        },         status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def confirmar_envio_pedido(request):
    """
    API endpoint específico para que el vendedor confirme el envío de un pedido.
    Envía automáticamente un correo al cliente notificando que su pedido está en camino.
    """
    try:
        usuario_id = request.data.get('usuario_id')
        pedido_id = request.data.get('pedido_id')
        notas_envio = request.data.get('notas', '')  # Notas opcionales del vendedor

        if not usuario_id or not pedido_id:
            return Response({
                'success': False,
                'message': 'usuario_id y pedido_id son requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(id=usuario_id)

        # Verificar permisos - solo vendedores, gerentes y admin pueden confirmar envíos
        if not (user.is_superuser or user.is_staff):
            try:
                cliente = Cliente.objects.get(user_id=usuario_id)
                if cliente.rol not in ['vendedor', 'gerente', 'admin_sistema']:
                    return Response({
                        'success': False,
                        'message': 'Acceso denegado. Solo vendedores, gerentes y administradores pueden confirmar envíos.'
                    }, status=status.HTTP_403_FORBIDDEN)
            except Cliente.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Usuario no tiene un cliente asociado.'
                }, status=status.HTTP_403_FORBIDDEN)

        # Obtener pedido
        try:
            pedido = Pedido.objects.get(id=pedido_id)
        except Pedido.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Pedido no encontrado.'
            }, status=status.HTTP_404_NOT_FOUND)

        # Validar que el pedido pueda ser marcado como enviado
        if pedido.estado not in ['pagado', 'en_preparacion']:
            return Response({
                'success': False,
                'message': f'No se puede confirmar el envío de un pedido en estado "{pedido.get_estado_display()}". El pedido debe estar pagado o en preparación.'
            }, status=status.HTTP_400_BAD_REQUEST)

        estado_anterior = pedido.estado

        # Actualizar estado y agregar notas si las hay
        pedido.estado = 'enviado'
        if notas_envio:
            pedido.notas = f"{pedido.notas or ''}\n[Envío] {notas_envio}".strip()
        pedido.save()

        # Registrar en auditoría
        AuditLog.registrar_cambio(
            usuario=user,
            tipo_accion='modificar',
            modelo='Pedido',
            id_objeto=pedido.id,
            datos_anteriores={'estado': estado_anterior},
            datos_nuevos={'estado': 'enviado', 'notas_envio': notas_envio},
            descripcion=f'Envío confirmado para pedido {pedido.numero_pedido} por {user.username}'
        )

        # Enviar notificación por email al cliente
        email_enviado = False
        try:
            email_enviado = EmailPedidoService.enviar_notificacion_enviado(pedido)
        except Exception as email_error:
            print(f"Error enviando email de notificación de envío: {email_error}")

        mensaje = f'Envío confirmado para pedido {pedido.numero_pedido}.'
        if email_enviado:
            mensaje += f' Se ha notificado al cliente ({pedido.cliente.user.email}) por correo electrónico.'

        return Response({
            'success': True,
            'message': mensaje,
            'pedido': {
                'id': pedido.id,
                'numero_pedido': pedido.numero_pedido,
                'estado': pedido.estado,
                'estado_display': pedido.get_estado_display(),
                'cliente_email': pedido.cliente.user.email
            },
            'email_enviado': email_enviado
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error al confirmar envío del pedido: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def listar_pedidos_gestion(request):
    """
    API endpoint para listar pedidos individuales para gestión administrativa.
    HU 50: Gestión de pedidos desde dashboard administrativo
    """
    try:
        usuario_id = request.query_params.get('usuario_id')
        estado_filtro = request.query_params.get('estado', 'todos')

        if not usuario_id:
            return Response({
                'success': False,
                'message': 'usuario_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar permisos (vendedor, gerente o admin_sistema)
        user = User.objects.get(id=usuario_id)
        try:
            cliente = Cliente.objects.get(user=user)
            if cliente.rol not in ['vendedor', 'gerente', 'admin_sistema'] and not (user.is_staff or user.is_superuser):
                return Response({
                    'success': False,
                    'message': 'Acceso denegado. Solo vendedores, gerentes y administradores pueden gestionar pedidos.'
                }, status=status.HTTP_403_FORBIDDEN)
        except Cliente.DoesNotExist:
            if not (user.is_staff or user.is_superuser):
                return Response({
                    'success': False,
                    'message': 'Acceso denegado. Solo vendedores, gerentes y administradores pueden gestionar pedidos.'
                }, status=status.HTTP_403_FORBIDDEN)

        # Construir queryset base
        pedidos = Pedido.objects.select_related('cliente__user', 'vendedor__user').prefetch_related('detalles')

        # Aplicar filtro de estado
        if estado_filtro and estado_filtro != 'todos':
            pedidos = pedidos.filter(estado=estado_filtro)

        # Ordenar por fecha descendente y limitar a 50 resultados
        pedidos = pedidos.order_by('-fecha_pedido')[:50]

        # Serializar pedidos
        pedidos_data = []
        for pedido in pedidos:
            # Calcular total de productos
            total_productos = sum(detalle.cantidad for detalle in pedido.detalles.all())

            pedidos_data.append({
                'id': pedido.id,
                'numero_pedido': pedido.numero_pedido,
                'cliente_email': pedido.cliente.user.email,
                'cliente_nombre': pedido.cliente.user.get_full_name() or pedido.cliente.user.username,
                'vendedor': pedido.vendedor.user.get_full_name() if pedido.vendedor else None,
                'total': float(pedido.total),
                'estado': pedido.estado,
                'estado_display': pedido.get_estado_display(),
                'fecha_pedido': pedido.fecha_pedido.isoformat(),
                'metodo_pago': pedido.metodo_pago,
                'metodo_envio': pedido.metodo_envio or 'N/A',
                'total_productos': total_productos
            })

        return Response({
            'success': True,
            'pedidos': pedidos_data,
            'total': len(pedidos_data),
            'filtro_estado': estado_filtro
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error al listar pedidos: {str(e)}'
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


# ==================== AUDITORÍA Y TRAZABILIDAD ====================

def _get_client_ip(request):
    """Obtiene la IP real del cliente considerando proxies"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip

def _obtener_info_usuario(request):
    """Obtiene usuario e información de IP/User-Agent de la request.

    Soporta autenticación por:
    - session (request.user)
    - campo `user_id` en body (POST)
    - header `Authorization: Token <token>` (busca Cliente.api_token)
    """
    usuario = None
    ip_address = ""
    user_agent = ""

    # 1) Session Django
    if request.user and request.user.is_authenticated:
        usuario = request.user

    # 2) Si no hay sesión, intentar token en header Authorization: Token <token>
    if not usuario:
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header and auth_header.startswith('Token '):
            token = auth_header.split(' ', 1)[1].strip()
            try:
                cliente_token = Cliente.objects.get(api_token=token)
                usuario = cliente_token.user
            except Cliente.DoesNotExist:
                usuario = None

    # 3) Como fallback (por compatibilidad) permitir user_id en body/query
    if not usuario:
        user_id = None
        if request.method == 'GET':
            user_id = request.query_params.get('user_id') if hasattr(request, 'query_params') else request.GET.get('user_id')
        else:
            user_id = request.data.get('user_id') if hasattr(request, 'data') else request.POST.get('user_id')

        if user_id:
            try:
                usuario = User.objects.get(id=user_id)
            except User.DoesNotExist:
                usuario = None

    # Obtener IP del cliente
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR', '')

    # Obtener User-Agent
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    return usuario, ip_address, user_agent


def _verificar_permisos_auditoria(usuario):
    """Verifica si el usuario tiene permiso para ver auditoría (Gerente, Admin Sistema o Superuser)"""
    if not usuario or not usuario.is_authenticated:
        return False
    
    # Superuser y staff (Django admin) siempre tienen acceso
    if usuario.is_superuser or usuario.is_staff:
        return True
    
    # Verificar rol en Cliente
    try:
        cliente = Cliente.objects.get(user=usuario)
        # Permitir gerente y admin_sistema
        return cliente.rol in ['gerente', 'admin_sistema']
    except Cliente.DoesNotExist:
        return False


@api_view(['GET', 'POST'])
def listar_audit_logs(request):
    """
    API endpoint para listar logs de auditoría con filtros avanzados.
    Acceso: Solo Gerente y Admin Sistema

    GET: Listar logs con filtros
    Filtros disponibles:
    - usuario_id: ID del usuario
    - tipo_accion: crear, modificar, eliminar, estado, rol
    - modelo: Producto, Pedido, Cliente, User
    - fecha_inicio: Formato ISO 8601
    - fecha_fin: Formato ISO 8601
    - id_objeto: ID del objeto modificado
    - descripcion: Búsqueda en descripción
    - pagina: Número de página (default 1)
    - items_por_pagina: Items por página (default 50, máximo 500)
    """
    try:
        # Para GET usar query_params, para otros métodos usar data
        if request.method == 'GET':
            usuario_id = request.query_params.get('user_id')
        else:
            usuario_id = request.data.get('user_id')

        if not usuario_id:
            return Response({
                'success': False,
                'message': 'user_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        usuario = User.objects.get(id=usuario_id)
        ip_address = request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Verificar permisos
        if not _verificar_permisos_auditoria(usuario):
            return Response({
                'success': False,
                'message': 'Acceso denegado. Solo Gerentes y Administradores del Sistema pueden ver auditoría.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Obtener parámetros
        datos = request.query_params if request.method == 'GET' else request.data
        
        # Construir queryset con filtros
        queryset = AuditLog.objects.all()
        
        # Filtro por usuario
        if datos.get('usuario_id'):
            queryset = queryset.filter(usuario_id=datos.get('usuario_id'))
        
        # Filtro por tipo de acción
        if datos.get('tipo_accion'):
            queryset = queryset.filter(tipo_accion=datos.get('tipo_accion'))
        
        # Filtro por modelo
        if datos.get('modelo'):
            queryset = queryset.filter(modelo=datos.get('modelo'))
        
        # Filtro por rango de fechas
        if datos.get('fecha_inicio'):
            queryset = queryset.filter(fecha__gte=datos.get('fecha_inicio'))
        if datos.get('fecha_fin'):
            queryset = queryset.filter(fecha__lte=datos.get('fecha_fin'))
        
        # Filtro por ID de objeto
        if datos.get('id_objeto'):
            queryset = queryset.filter(id_objeto=datos.get('id_objeto'))
        
        # Búsqueda en descripción
        if datos.get('descripcion'):
            queryset = queryset.filter(descripcion__icontains=datos.get('descripcion'))
        
        # Contar total de resultados
        total = queryset.count()
        
        # Paginación
        pagina = int(datos.get('pagina', 1))
        items_por_pagina = int(datos.get('items_por_pagina', 50))
        items_por_pagina = min(items_por_pagina, 500)  # Máximo 500 items
        
        inicio = (pagina - 1) * items_por_pagina
        fin = inicio + items_por_pagina
        
        logs = queryset[inicio:fin]
        
        from .serializers import AuditLogSerializer
        serializer = AuditLogSerializer(logs, many=True)
        
        total_paginas = (total + items_por_pagina - 1) // items_por_pagina
        
        return Response({
            'success': True,
            'total': total,
            'pagina': pagina,
            'total_paginas': total_paginas,
            'items_por_pagina': items_por_pagina,
            'logs': serializer.data
        }, status=status.HTTP_200_OK)
    
    except ValueError as e:
        return Response({
            'success': False,
            'message': f'Parámetro inválido: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def detalle_audit_log(request, log_id):
    """
    API endpoint para obtener el detalle de un log de auditoría específico.
    Acceso: Solo Gerente y Admin Sistema
    """
    try:
        usuario_id = request.data.get('user_id')

        if not usuario_id:
            return Response({
                'success': False,
                'message': 'user_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        usuario = User.objects.get(id=usuario_id)
        ip_address = request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Verificar permisos
        if not _verificar_permisos_auditoria(usuario):
            return Response({
                'success': False,
                'message': 'Acceso denegado.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        log = AuditLog.objects.get(id=log_id)
        
        from .serializers import AuditLogSerializer
        serializer = AuditLogSerializer(log)
        
        # Verificar integridad del hash
        hash_verificado = log.hash_integridad == log.generar_hash_integridad()
        
        return Response({
            'success': True,
            'log': serializer.data,
            'hash_verificado': hash_verificado
        }, status=status.HTTP_200_OK)
    
    except AuditLog.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Log no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def estadisticas_auditoria(request):
    """
    API endpoint para obtener estadísticas de auditoría.
    Acceso: Solo Gerente y Admin Sistema
    
    Retorna:
    - Total de logs
    - Logs por tipo de acción
    - Logs por modelo
    - Logs por usuario (Top 10)
    - Actividad últimas 24 horas
    - Logs con hash inválido (potencial manipulación)
    """
    try:
        usuario_id = request.data.get('user_id')

        if not usuario_id:
            return Response({
                'success': False,
                'message': 'user_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        usuario = User.objects.get(id=usuario_id)
        ip_address = request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Verificar permisos
        if not _verificar_permisos_auditoria(usuario):
            return Response({
                'success': False,
                'message': 'Acceso denegado.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        from datetime import timedelta
        from django.db.models import Count
        
        # Total de logs
        total_logs = AuditLog.objects.count()
        
        # Logs por tipo de acción
        logs_por_tipo = AuditLog.objects.values('tipo_accion').annotate(
            cantidad=Count('id')
        ).order_by('-cantidad')
        
        # Logs por modelo
        logs_por_modelo = AuditLog.objects.values('modelo').annotate(
            cantidad=Count('id')
        ).order_by('-cantidad')
        
        # Top 10 usuarios más activos
        top_usuarios = AuditLog.objects.values(
            'usuario__email',
            'usuario__id'
        ).annotate(
            cantidad=Count('id')
        ).order_by('-cantidad')[:10]
        
        # Actividad últimas 24 horas
        hace_24h = timezone.now() - timedelta(hours=24)
        logs_24h = AuditLog.objects.filter(fecha__gte=hace_24h).count()
        
        # Logs por hora (últimas 24 horas)
        from django.db.models.functions import TruncHour
        logs_por_hora = AuditLog.objects.filter(
            fecha__gte=hace_24h
        ).annotate(
            hora=TruncHour('fecha')
        ).values('hora').annotate(
            cantidad=Count('id')
        ).order_by('hora')
        
        # Verificar integridad de hashes (logs potencialmente manipulados)
        logs_sospechosos = []
        for log in AuditLog.objects.all()[:100]:  # Verificar últimos 100
            if log.hash_integridad != log.generar_hash_integridad():
                logs_sospechosos.append({
                    'id': log.id,
                    'usuario_email': log.usuario.email if log.usuario else 'N/A',
                    'fecha': log.fecha.isoformat(),
                    'tipo_accion': log.tipo_accion,
                    'modelo': log.modelo,
                })
        
        # Preparar tipos de acción con etiquetas
        tipos_accion = dict(AuditLog._meta.get_field('tipo_accion').choices)
        modelos = dict(AuditLog._meta.get_field('modelo').choices)
        
        return Response({
            'success': True,
            'estadisticas': {
                'total_logs': total_logs,
                'logs_ultimas_24h': logs_24h,
                'logs_por_tipo_accion': [
                    {
                        'tipo': item['tipo_accion'],
                        'tipo_display': tipos_accion.get(item['tipo_accion'], '?'),
                        'cantidad': item['cantidad']
                    }
                    for item in logs_por_tipo
                ],
                'logs_por_modelo': [
                    {
                        'modelo': item['modelo'],
                        'modelo_display': modelos.get(item['modelo'], '?'),
                        'cantidad': item['cantidad']
                    }
                    for item in logs_por_modelo
                ],
                'top_usuarios_activos': [
                    {
                        'usuario_id': item['usuario__id'],
                        'usuario_email': item['usuario__email'],
                        'cantidad': item['cantidad']
                    }
                    for item in top_usuarios
                ],
                'logs_por_hora_24h': [
                    {
                        'hora': item['hora'].isoformat() if item['hora'] else None,
                        'cantidad': item['cantidad']
                    }
                    for item in logs_por_hora
                ],
                'logs_potencialmente_manipulados': {
                    'cantidad': len(logs_sospechosos),
                    'detalles': logs_sospechosos
                }
            }
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def exportar_audit_logs(request):
    """
    API endpoint para exportar logs de auditoría en formato CSV.
    Acceso: Solo Gerente y Admin Sistema

    Parámetros (iguales a listar_audit_logs)
    """
    try:
        # Para GET usar query_params, para otros métodos usar data
        if request.method == 'GET':
            usuario_id = request.query_params.get('user_id')
        else:
            usuario_id = request.data.get('user_id')

        if not usuario_id:
            return Response({
                'success': False,
                'message': 'user_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        usuario = User.objects.get(id=usuario_id)
        ip_address = request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Verificar permisos
        if not _verificar_permisos_auditoria(usuario):
            return Response({
                'success': False,
                'message': 'Acceso denegado.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        import csv
        from io import StringIO
        from django.http import HttpResponse
        
        # Obtener parámetros
        datos = request.query_params
        
        # Construir queryset con los mismos filtros
        queryset = AuditLog.objects.all()
        
        if datos.get('usuario_id'):
            queryset = queryset.filter(usuario_id=datos.get('usuario_id'))
        if datos.get('tipo_accion'):
            queryset = queryset.filter(tipo_accion=datos.get('tipo_accion'))
        if datos.get('modelo'):
            queryset = queryset.filter(modelo=datos.get('modelo'))
        if datos.get('fecha_inicio'):
            queryset = queryset.filter(fecha__gte=datos.get('fecha_inicio'))
        if datos.get('fecha_fin'):
            queryset = queryset.filter(fecha__lte=datos.get('fecha_fin'))
        if datos.get('id_objeto'):
            queryset = queryset.filter(id_objeto=datos.get('id_objeto'))
        if datos.get('descripcion'):
            queryset = queryset.filter(descripcion__icontains=datos.get('descripcion'))
        
        # Limitar a 10000 registros máximo para exportación
        queryset = queryset.order_by('-fecha')[:10000]
        
        # Crear CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Escribir encabezados
        writer.writerow([
            'ID',
            'Fecha',
            'Usuario',
            'Tipo de Acción',
            'Modelo',
            'ID Objeto',
            'Descripción',
            'IP Address',
            'Hash de Integridad'
        ])
        
        # Escribir datos
        count = 0
        for log in queryset:
            count += 1
            try:
                writer.writerow([
                    log.id,
                    log.fecha.isoformat() if log.fecha else 'N/A',
                    log.usuario.email if log.usuario else 'N/A',
                    log.get_tipo_accion_display(),
                    log.modelo,
                    log.id_objeto,
                    log.descripcion,
                    log.ip_address,
                    log.hash_integridad,
                ])
            except Exception as row_err:
                print(f"Error escribiendo fila para log {log.id}: {row_err}")
                writer.writerow([log.id, 'ERROR', str(row_err), '', '', '', '', '', ''])
        
        # Registrar la exportación como auditoría (comentado para evitar loops infinitos)
        # try:
        #     AuditLog.registrar_cambio(
        #         usuario=usuario,
        #         tipo_accion='crear',
        #         modelo='AuditLog',
        #         id_objeto='export',
        #         descripcion=f'Exportación de {count} logs de auditoría',
        #         ip_address=ip_address,
        #         user_agent=user_agent
        #     )
        # except Exception as audit_err:
        #     print(f"Error registrando auditoría de exportación: {audit_err}")
        
        response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="auditoria_logs.csv"'
        return response
    
    except Exception as e:
        import traceback
        print(f'Error en exportar_audit_logs: {str(e)}')
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error al exportar: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def dashboard_admin_estadisticas(request):
    """
    API endpoint para obtener estadísticas del dashboard de administrador.
    Acceso: Solo Admin Sistema
    """
    try:
        usuario_id = request.data.get('user_id')

        if not usuario_id:
            return Response({
                'success': False,
                'message': 'user_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        usuario = User.objects.get(id=usuario_id)
        ip_address = request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Verificar permisos - Solo admin sistema
        if usuario.cliente.rol != 'admin_sistema':
            return Response({
                'success': False,
                'message': 'Acceso denegado. Solo administradores del sistema pueden ver estas estadísticas.'
            }, status=status.HTTP_403_FORBIDDEN)

        from django.db.models import Count, Sum, Avg
        from django.db.models.functions import TruncMonth, TruncDay

        # Estadísticas generales
        total_productos = Producto.objects.filter(activo=True).count()
        total_clientes = Cliente.objects.count()
        total_pedidos = Pedido.objects.count()
        pedidos_pendientes = Pedido.objects.filter(estado='pendiente').count()

        # Ventas totales
        ventas_totales = Pedido.objects.filter(estado__in=['pagado', 'en_preparacion', 'enviado', 'entregado']).aggregate(
            total=Sum('total')
        )['total'] or 0

        # Productos con stock bajo
        productos_stock_bajo = Producto.objects.filter(activo=True, stock__lte=F('stock_minimo')).count()

        # Pedidos por mes (últimos 12 meses)
        from datetime import datetime, timedelta
        hace_12_meses = datetime.now() - timedelta(days=365)

        pedidos_por_mes = Pedido.objects.filter(
            fecha_pedido__gte=hace_12_meses
        ).annotate(
            mes=TruncMonth('fecha_pedido')
        ).values('mes').annotate(
            cantidad=Count('id'),
            total_ventas=Sum('total')
        ).order_by('mes')

        # Top productos más vendidos
        top_productos = DetallesPedido.objects.values(
            'producto__nombre'
        ).annotate(
            cantidad_total=Sum('cantidad'),
            ingresos_totales=Sum('subtotal')
        ).order_by('-cantidad_total')[:10]

        # Usuarios más activos (por pedidos)
        usuarios_activos = Cliente.objects.annotate(
            total_pedidos=Count('pedidos')
        ).filter(total_pedidos__gt=0).order_by('-total_pedidos')[:10]

        # Estadísticas de auditoría
        total_logs = AuditLog.objects.count()
        logs_ultima_semana = AuditLog.objects.filter(
            fecha__gte=datetime.now() - timedelta(days=7)
        ).count()

        return Response({
            'success': True,
            'estadisticas': {
                'generales': {
                    'total_productos': total_productos,
                    'total_clientes': total_clientes,
                    'total_pedidos': total_pedidos,
                    'pedidos_pendientes': pedidos_pendientes,
                    'ventas_totales': float(ventas_totales),
                    'productos_stock_bajo': productos_stock_bajo
                },
                'ventas_por_mes': list(pedidos_por_mes),
                'top_productos': list(top_productos),
                'usuarios_activos': [
                    {
                        'email': cliente.user.email,
                        'rol': cliente.get_rol_display(),
                        'total_pedidos': cliente.total_pedidos
                    }
                    for cliente in usuarios_activos
                ],
                'auditoria': {
                    'total_logs': total_logs,
                    'logs_ultima_semana': logs_ultima_semana
                }
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        print(f'Error en dashboard_admin_estadisticas: {str(e)}')
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def listar_solicitudes_autorizacion(request):
    """
    API endpoint para listar solicitudes de autorización.
    Acceso: Vendedor, Gerente, Admin Sistema
    """
    try:
        usuario_id = request.query_params.get('user_id')

        if not usuario_id:
            return Response({
                'success': False,
                'message': 'user_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        usuario = User.objects.get(id=usuario_id)

        # Verificar que el usuario tenga un cliente asociado
        try:
            cliente = Cliente.objects.get(user=usuario)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Usuario no tiene un cliente asociado.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Intentar reparar la tabla si es necesario
        try:
            reparar_tabla_solicitudes()
        except Exception as repair_error:
            print(f"Error en reparación de tabla: {repair_error}")
            # Continuar de todas formas

        # Verificar permisos
        if cliente.rol not in ['vendedor', 'gerente', 'admin_sistema']:
            return Response({
                'success': False,
                'message': 'Acceso denegado.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Obtener parámetros de filtrado
        estado = request.query_params.get('estado', '')
        tipo = request.query_params.get('tipo', '')
        solicitante_id = request.query_params.get('solicitante_id', '')
        fecha_inicio = request.query_params.get('fecha_inicio', '')
        fecha_fin = request.query_params.get('fecha_fin', '')
        prioridad = request.query_params.get('prioridad', '')
        pagina = int(request.query_params.get('pagina', 1))
        items_por_pagina = int(request.query_params.get('items_por_pagina', 20))

        # Construir queryset
        queryset = SolicitudAutorizacion.objects.all()

        # Filtrar según el rol del usuario
        if cliente.rol == 'vendedor':
            # Vendedores solo ven sus propias solicitudes
            queryset = queryset.filter(solicitante=usuario)
        # Gerentes y admin_sistema ven todas las solicitudes

        if estado:
            queryset = queryset.filter(estado=estado)
        if tipo:
            queryset = queryset.filter(tipo_solicitud=tipo)
        if solicitante_id:
            queryset = queryset.filter(solicitante_id=solicitante_id)
        if prioridad:
            queryset = queryset.filter(prioridad=prioridad)

        # Filtros de fecha
        if fecha_inicio:
            try:
                from datetime import datetime
                dt_inicio = datetime.fromisoformat(fecha_inicio.replace('Z', '+00:00'))
                queryset = queryset.filter(fecha_solicitud__gte=dt_inicio)
            except:
                pass
        if fecha_fin:
            try:
                from datetime import datetime
                dt_fin = datetime.fromisoformat(fecha_fin.replace('Z', '+00:00'))
                queryset = queryset.filter(fecha_solicitud__lte=dt_fin)
            except:
                pass

        # Ordenar por fecha más reciente
        queryset = queryset.order_by('-fecha_solicitud')

        # Paginación
        total = queryset.count()
        inicio = (pagina - 1) * items_por_pagina
        fin = inicio + items_por_pagina
        solicitudes_paginadas = queryset[inicio:fin]

        # Serializar datos
        solicitudes = []
        for solicitud in solicitudes_paginadas:
            solicitudes.append({
                'id': solicitud.id,
                'solicitante': {
                    'id': solicitud.solicitante.id,
                    'email': solicitud.solicitante.email,
                    'rol': solicitud.solicitante.cliente.get_rol_display() if hasattr(solicitud.solicitante, 'cliente') and solicitud.solicitante.cliente else 'N/A'
                },
                'aprobador': None,  # Temporalmente deshabilitado por problema de migración
                'tipo_solicitud': solicitud.get_tipo_solicitud_display(),
                'estado': solicitud.get_estado_display(),
                'prioridad': solicitud.get_prioridad_display(),
                'motivo': solicitud.motivo,
                'comentario_respuesta': solicitud.comentario_respuesta,
                'fecha_solicitud': solicitud.fecha_solicitud.isoformat(),
                'fecha_respuesta': solicitud.fecha_respuesta.isoformat() if solicitud.fecha_respuesta else None,
                'producto_afectado': {
                    'id': solicitud.producto_afectado.id,
                    'nombre': solicitud.producto_afectado.nombre,
                    'sku': solicitud.producto_afectado.sku
                } if solicitud.producto_afectado else None
            })

        total_paginas = (total + items_por_pagina - 1) // items_por_pagina

        return Response({
            'success': True,
            'solicitudes': solicitudes,
            'paginacion': {
                'pagina': pagina,
                'total_paginas': total_paginas,
                'items_por_pagina': items_por_pagina,
                'total': total
            }
        }, status=status.HTTP_200_OK)

        # Obtener parámetros de filtrado
        estado = request.query_params.get('estado', '')
        tipo = request.query_params.get('tipo', '')
        solicitante_id = request.query_params.get('solicitante_id', '')
        fecha_inicio = request.query_params.get('fecha_inicio', '')
        fecha_fin = request.query_params.get('fecha_fin', '')
        prioridad = request.query_params.get('prioridad', '')
        pagina = int(request.query_params.get('pagina', 1))
        items_por_pagina = int(request.query_params.get('items_por_pagina', 20))

        # Construir queryset
        queryset = SolicitudAutorizacion.objects.all()

        if estado:
            queryset = queryset.filter(estado=estado)
        if tipo:
            queryset = queryset.filter(tipo_solicitud=tipo)
        if solicitante_id:
            queryset = queryset.filter(solicitante_id=solicitante_id)
        if prioridad:
            queryset = queryset.filter(prioridad=prioridad)

        # Filtros de fecha
        if fecha_inicio:
            try:
                from datetime import datetime
                dt_inicio = datetime.fromisoformat(fecha_inicio.replace('Z', '+00:00'))
                queryset = queryset.filter(fecha_solicitud__gte=dt_inicio)
            except:
                pass
        if fecha_fin:
            try:
                from datetime import datetime
                dt_fin = datetime.fromisoformat(fecha_fin.replace('Z', '+00:00'))
                queryset = queryset.filter(fecha_solicitud__lte=dt_fin)
            except:
                pass

        # Ordenar por fecha más reciente
        queryset = queryset.order_by('-fecha_solicitud')

        # Paginación
        total = queryset.count()
        inicio = (pagina - 1) * items_por_pagina
        fin = inicio + items_por_pagina
        solicitudes_paginadas = queryset[inicio:fin]

        # Serializar datos
        solicitudes = []
        for solicitud in solicitudes_paginadas:
            solicitudes.append({
                'id': solicitud.id,
                'solicitante': {
                    'id': solicitud.solicitante.id,
                    'email': solicitud.solicitante.email,
                    'rol': solicitud.solicitante.cliente.get_rol_display() if hasattr(solicitud.solicitante, 'cliente') and solicitud.solicitante.cliente else 'N/A'
                },
                'aprobador': None,  # Temporalmente deshabilitado por problema de migración
                'tipo_solicitud': solicitud.get_tipo_solicitud_display(),
                'estado': solicitud.get_estado_display(),
                'prioridad': solicitud.get_prioridad_display(),
                'motivo': solicitud.motivo,
                'comentario_respuesta': solicitud.comentario_respuesta,
                'fecha_solicitud': solicitud.fecha_solicitud.isoformat(),
                'fecha_respuesta': solicitud.fecha_respuesta.isoformat() if solicitud.fecha_respuesta else None,
                'producto_afectado': {
                    'id': solicitud.producto_afectado.id,
                    'nombre': solicitud.producto_afectado.nombre,
                    'sku': solicitud.producto_afectado.sku
                } if solicitud.producto_afectado else None
            })

        total_paginas = (total + items_por_pagina - 1) // items_por_pagina

        return Response({
            'success': True,
            'solicitudes': solicitudes,
            'paginacion': {
                'pagina': pagina,
                'total_paginas': total_paginas,
                'items_por_pagina': items_por_pagina,
                'total': total
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        print(f'Error en listar_solicitudes_autorizacion: {str(e)}')
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def crear_solicitud_autorizacion(request):
    """
    API endpoint para crear una nueva solicitud de autorización.
    Acceso: Vendedor, Gerente, Admin Sistema
    """
    try:
        usuario_id = request.data.get('user_id')

        if not usuario_id:
            return Response({
                'success': False,
                'message': 'user_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        usuario = User.objects.get(id=usuario_id)
        ip_address = request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Intentar reparar la tabla si es necesario
        try:
            reparar_tabla_solicitudes()
        except Exception as repair_error:
            print(f"Error en reparación de tabla: {repair_error}")
            # Continuar de todas formas

        # Verificar que el usuario tenga un cliente asociado
        try:
            cliente = Cliente.objects.get(user=usuario)
        except Cliente.DoesNotExist:
            # Si no existe cliente, intentar crearlo para usuarios con permisos especiales
            if usuario.is_staff or usuario.is_superuser:
                from datetime import date
                cliente = Cliente.objects.create(
                    user=usuario,
                    fecha_nacimiento=date(2000, 1, 1),
                    email_confirmado=True,
                    rol='admin_sistema'
                )
            else:
                return Response({
                    'success': False,
                    'message': 'Usuario no tiene un cliente asociado.'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Obtener datos del request
        datos = request.data
        tipo_solicitud = datos.get('tipo_solicitud')
        modelo_afectado = datos.get('modelo_afectado')
        id_objeto_afectado = datos.get('id_objeto_afectado')
        datos_anteriores = datos.get('datos_anteriores', {})
        datos_nuevos = datos.get('datos_nuevos', {})

        # Verificar si los datos llegan como strings JSON (de versiones anteriores del frontend)
        if isinstance(datos_anteriores, str):
            import json
            try:
                datos_anteriores = json.loads(datos_anteriores)
            except:
                datos_anteriores = {}
        if isinstance(datos_nuevos, str):
            import json
            try:
                datos_nuevos = json.loads(datos_nuevos)
            except:
                datos_nuevos = {}

        motivo = datos.get('motivo', '')
        prioridad = datos.get('prioridad', 'media')

        # Debug: Imprimir datos recibidos
        print(f"Creando solicitud - Usuario: {usuario.id}, Tipo: {tipo_solicitud}, Datos nuevos: {datos_nuevos}")

        try:
            # Crear la solicitud usando el método estático
            solicitud = SolicitudAutorizacion.crear_solicitud(
                solicitante=usuario,
                tipo_solicitud=tipo_solicitud,
                modelo_afectado=modelo_afectado,
                id_objeto_afectado=id_objeto_afectado,
                datos_anteriores=datos_anteriores,
                datos_nuevos=datos_nuevos,
                motivo=motivo,
                prioridad=prioridad,
                ip_address=ip_address,
                user_agent=user_agent
            )

            print(f"Solicitud creada exitosamente: ID {solicitud.id}")
            return Response({
                'success': True,
                'message': 'Solicitud creada exitosamente.',
                'solicitud_id': solicitud.id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Error al crear solicitud: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({
                'success': False,
                'message': f'Error al crear solicitud: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    except ValueError as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        import traceback
        print(f'Error en crear_solicitud_autorizacion: {str(e)}')
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def gestionar_solicitud_autorizacion(request, solicitud_id):
    """
    API endpoint para aprobar o rechazar una solicitud de autorización.
    Acceso: Gerente, Admin Sistema
    """
    print(f"🚀 GESTION AUTORIZACION - INICIO: solicitud_id={solicitud_id}")

    try:
        # Debug: Imprimir datos recibidos
        print(f"📝 GESTION - Datos recibidos: {request.data}")
        print(f"🌐 GESTION - Método: {request.method}, URL: {request.path}")

        usuario_id = request.data.get('user_id')

        if not usuario_id:
            print("DEBUG GESTION - ERROR: user_id no proporcionado")
            return Response({
                'success': False,
                'message': 'user_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        usuario = User.objects.get(id=usuario_id)
        ip_address = request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        print(f"DEBUG GESTION - Usuario encontrado: {usuario.id} ({usuario.username})")

        # Verificar que el usuario tenga un cliente asociado
        try:
            cliente = Cliente.objects.get(user=usuario)
        except Cliente.DoesNotExist:
            print(f"DEBUG GESTION - ERROR: Cliente no encontrado para usuario {usuario.id}")
            return Response({
                'success': False,
                'message': 'Usuario no tiene un cliente asociado.'
            }, status=status.HTTP_403_FORBIDDEN)

        print(f"DEBUG GESTION - Cliente encontrado: {cliente.rol}")

        # Intentar reparar la tabla si es necesario
        try:
            reparar_tabla_solicitudes()
        except Exception as repair_error:
            print(f"Error en reparación de tabla: {repair_error}")
            # Continuar de todas formas

        # Verificar permisos - Solo gerente y admin pueden gestionar
        if cliente.rol not in ['gerente', 'admin_sistema']:
            print(f"DEBUG GESTION - ERROR: Permisos insuficientes. Rol: {cliente.rol}")
            return Response({
                'success': False,
                'message': 'Acceso denegado. Solo gerentes y administradores pueden gestionar solicitudes.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Obtener la solicitud
        try:
            solicitud = SolicitudAutorizacion.objects.get(id=solicitud_id)
            print(f"DEBUG GESTION - Solicitud encontrada: ID {solicitud.id}, Estado actual: {solicitud.estado}")
        except SolicitudAutorizacion.DoesNotExist:
            print(f"DEBUG GESTION - ERROR: Solicitud {solicitud_id} no encontrada")
            return Response({
                'success': False,
                'message': 'Solicitud no encontrada.'
            }, status=status.HTTP_404_NOT_FOUND)

        # Obtener acción y comentario
        datos = request.data
        accion = datos.get('accion')  # 'aprobar' o 'rechazar'
        comentario = datos.get('comentario', '')

        print(f"DEBUG GESTION - Procesando solicitud {solicitud_id}")
        print(f"  - Acción: {accion}")
        print(f"  - Comentario: '{comentario}'")
        print(f"  - Usuario: {usuario.id} ({cliente.rol})")
        print(f"  - Estado actual: {solicitud.estado}")

        # Verificar que la solicitud esté pendiente
        if solicitud.estado != 'pendiente':
            print(f"⚠️ GESTION - Solicitud {solicitud_id} ya procesada (estado: {solicitud.estado})")
            return Response({
                'success': False,
                'message': f'La solicitud ya fue procesada (estado: {solicitud.estado}).'
            }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                'success': False,
                'message': 'Solicitud no encontrada.'
            }, status=status.HTTP_404_NOT_FOUND)

        # Verificar permisos para gestionar
        if cliente.rol not in ['gerente', 'admin_sistema']:
            return Response({
                'success': False,
                'message': 'Solo gerentes pueden gestionar solicitudes.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Aprobar o rechazar la solicitud (versión simplificada por problema de migración)
        if accion == 'aprobar':
            print(f"DEBUG GESTION - Aprobando solicitud {solicitud.id}")
            # Actualización manual simplificada
            estado_anterior = solicitud.estado
            solicitud.estado = 'aprobada'
            solicitud.fecha_respuesta = timezone.now()
            solicitud.comentario_respuesta = comentario
            # solicitud.aprobador = usuario  # Deshabilitado por problema de migración

            try:
                solicitud.save()
                print(f"DEBUG GESTION - Solicitud {solicitud.id} guardada exitosamente: '{estado_anterior}' -> 'aprobada'")

                # Verificar que se guardó correctamente
                solicitud_verificada = SolicitudAutorizacion.objects.get(id=solicitud.id)
                print(f"DEBUG GESTION - Verificación: Estado actual en BD: {solicitud_verificada.estado}")

            except Exception as save_error:
                print(f"DEBUG GESTION - ERROR al guardar: {save_error}")
                return Response({
                    'success': False,
                    'message': f'Error al guardar cambios: {str(save_error)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            mensaje = 'Solicitud aprobada exitosamente.'

        elif accion == 'rechazar':
            print(f"DEBUG GESTION - Rechazando solicitud {solicitud.id}")
            # Actualización manual simplificada
            estado_anterior = solicitud.estado
            solicitud.estado = 'rechazada'
            solicitud.fecha_respuesta = timezone.now()
            solicitud.comentario_respuesta = comentario
            # solicitud.aprobador = usuario  # Deshabilitado por problema de migración

            try:
                solicitud.save()
                print(f"DEBUG GESTION - Solicitud {solicitud.id} guardada exitosamente: '{estado_anterior}' -> 'rechazada'")

                # Verificar que se guardó correctamente
                solicitud_verificada = SolicitudAutorizacion.objects.get(id=solicitud.id)
                print(f"DEBUG GESTION - Verificación: Estado actual en BD: {solicitud_verificada.estado}")

            except Exception as save_error:
                print(f"DEBUG GESTION - ERROR al guardar: {save_error}")
                return Response({
                    'success': False,
                    'message': f'Error al guardar cambios: {str(save_error)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            mensaje = 'Solicitud rechazada exitosamente.'
        else:
            return Response({
                'success': False,
                'message': 'Acción inválida. Use "aprobar" o "rechazar".'
            }, status=status.HTTP_400_BAD_REQUEST)

        print(f"✅ GESTION - ÉXITO COMPLETO: {mensaje}")
        return Response({
            'success': True,
            'message': mensaje,
            'solicitud': {
                'id': solicitud.id,
                'estado': solicitud.get_estado_display(),
                'comentario_respuesta': solicitud.comentario_respuesta or comentario,
                'fecha_respuesta': solicitud.fecha_respuesta.isoformat() if solicitud.fecha_respuesta else None
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"❌ GESTION - ERROR GENERAL: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


# ================================
# VISTAS PARA NOTIFICACIONES DE AUTORIZACIONES - HU 50
# ================================

@api_view(['GET'])
def notificaciones_autorizaciones(request):
    """
    API endpoint para obtener notificaciones de autorizaciones pendientes.
    HU 50: Sistema de notificaciones para cambios pendientes de autorización
    """
    try:
        usuario_id = request.query_params.get('user_id')

        if not usuario_id:
            return Response({
                'success': False,
                'message': 'user_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar permisos (gerente o admin_sistema)
        user = User.objects.get(id=usuario_id)
        try:
            cliente = Cliente.objects.get(user=user)
            if cliente.rol not in ['gerente', 'admin_sistema'] and not (user.is_staff or user.is_superuser):
                return Response({
                    'success': False,
                    'message': 'Acceso denegado.'
                }, status=status.HTTP_403_FORBIDDEN)
        except Cliente.DoesNotExist:
            if not (user.is_staff or user.is_superuser):
                return Response({
                    'success': False,
                    'message': 'Acceso denegado.'
                }, status=status.HTTP_403_FORBIDDEN)

        # Contar solicitudes pendientes
        solicitudes_pendientes = SolicitudAutorizacion.objects.filter(estado='pendiente').count()

        # Obtener últimas 5 solicitudes pendientes
        ultimas_solicitudes = SolicitudAutorizacion.objects.filter(
            estado='pendiente'
        ).select_related('solicitante', 'producto_afectado').order_by('-fecha_solicitud')[:5]

        notificaciones = []
        for solicitud in ultimas_solicitudes:
            try:
                notificaciones.append({
                    'id': solicitud.id,
                    'tipo': 'autorizacion_pendiente',
                    'titulo': f'Nueva solicitud de {solicitud.solicitante.get_full_name() or solicitud.solicitante.username}',
                    'mensaje': f'{solicitud.get_tipo_solicitud_display()} - {solicitud.producto_afectado.nombre if solicitud.producto_afectado else "Producto no especificado"}',
                    'fecha': solicitud.fecha_solicitud.isoformat(),
                    'prioridad': solicitud.prioridad,
                    'url': '/autorizaciones/gerente'
                })
            except Exception as e:
                # Si hay problemas con los campos, crear notificación básica
                print(f"Error procesando solicitud {solicitud.id}: {e}")
                notificaciones.append({
                    'id': solicitud.id,
                    'tipo': 'autorizacion_pendiente',
                    'titulo': 'Nueva solicitud pendiente',
                    'mensaje': 'Solicitud de autorización requiere atención',
                    'fecha': solicitud.fecha_solicitud.isoformat(),
                    'prioridad': 'media',
                    'url': '/autorizaciones/gerente'
                })

        return Response({
            'success': True,
            'notificaciones': {
                'total_pendientes': solicitudes_pendientes,
                'ultimas': notificaciones
            }
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error al obtener notificaciones: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


# ================================
# VISTA DE PRUEBA PARA AUTORIZACIONES
# ================================

@api_view(['GET'])
def reparar_autorizaciones(request):
    """Vista para forzar la reparación de la tabla de autorizaciones"""
    try:
        resultado = reparar_tabla_solicitudes()
        return Response({
            'success': True,
            'message': 'Reparación completada',
            'reparacion_realizada': resultado
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error en reparación: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def test_gestion_autorizacion(request, solicitud_id):
    """Vista de test para verificar gestión de autorizaciones"""
    print(f"🧪 TEST GESTION - solicitud_id: {solicitud_id}")
    print(f"🧪 TEST GESTION - request.data: {request.data}")

    return Response({
        'success': True,
        'message': f'Test gestión solicitud {solicitud_id}',
        'datos_recibidos': request.data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
def test_autorizaciones(request):
    """Vista de prueba para verificar que las rutas y modelos funcionan"""
    try:
        # Intentar reparar la tabla primero
        reparacion_realizada = reparar_tabla_solicitudes()

        # Verificar estructura de la tabla usando SQL directo
        from django.db import connection

        # Verificar si la tabla existe y qué columnas tiene
        table_info = {}
        try:
            with connection.cursor() as cursor:
                # Verificar si la tabla existe
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables
                    WHERE table_schema = DATABASE() AND table_name = 'inventario_solicitudautorizacion'
                """)
                table_exists = cursor.fetchone()[0] > 0
                table_info['table_exists'] = table_exists

                if table_exists:
                    # Obtener columnas de la tabla
                    cursor.execute("""
                        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                        FROM information_schema.columns
                        WHERE table_schema = DATABASE() AND table_name = 'inventario_solicitudautorizacion'
                        ORDER BY ORDINAL_POSITION
                    """)
                    columns = cursor.fetchall()
                    table_info['columns'] = [
                        {'name': col[0], 'type': col[1], 'nullable': col[2], 'default': col[3]}
                        for col in columns
                    ]

                    # Intentar contar registros
                    cursor.execute("SELECT COUNT(*) FROM inventario_solicitudautorizacion")
                    total_solicitudes = cursor.fetchone()[0]
                    table_info['total_records'] = total_solicitudes
                else:
                    table_info['total_records'] = 0

        except Exception as db_error:
            table_info['db_error'] = str(db_error)

        # Verificar usuario actual si está autenticado
        user_id = request.query_params.get('user_id')
        user_info = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                try:
                    cliente = Cliente.objects.get(user=user)
                    user_info = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'rol': cliente.rol,
                        'cliente_existe': True
                    }
                except Cliente.DoesNotExist:
                    user_info = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'cliente_existe': False,
                        'error': 'Cliente no encontrado'
                    }
            except User.DoesNotExist:
                user_info = {'error': 'Usuario no encontrado'}

        return Response({
            'success': True,
            'message': 'Diagnóstico de autorizaciones completado',
            'table_info': table_info,
            'user_info': user_info,
            'reparacion_realizada': reparacion_realizada,
            'timestamp': str(datetime.now())
        }, status=status.HTTP_200_OK)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        # Si hay error con el modelo, intentar crear/reparar la tabla
        if 'Unknown column' in str(e) or 'aprobador_id' in str(e):
            table_repaired = reparar_tabla_solicitudes()
            if table_repaired:
                return Response({
                    'success': False,
                    'message': f'Error original: {str(e)}. Tabla reparada automáticamente. Intenta recargar la página.',
                    'table_repaired': True,
                    'error_details': error_details
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'success': False,
            'message': f'Error: {str(e)}',
            'error_details': error_details
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ================================
# VISTAS PARA CONSULTA DE CLIENTES - HU 23
# ================================

@api_view(['GET'])
def detalle_cliente(request, cliente_id):
    """
    API endpoint para obtener información detallada de un cliente.
    HU 23: Vista detallada de cliente con historial de compras
    """
    try:
        usuario_id = request.query_params.get('user_id')

        if not usuario_id:
            return Response({
                'success': False,
                'message': 'user_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar permisos (vendedor, gerente, admin_sistema)
        usuario = User.objects.get(id=usuario_id)
        try:
            cliente_usuario = Cliente.objects.get(user=usuario)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Usuario no tiene un cliente asociado.'
            }, status=status.HTTP_403_FORBIDDEN)

        if cliente_usuario.rol not in ['vendedor', 'gerente', 'admin_sistema']:
            return Response({
                'success': False,
                'message': 'Acceso denegado. Solo vendedores, gerentes y administradores pueden consultar clientes.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Obtener el cliente solicitado
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Cliente no encontrado.'
            }, status=status.HTTP_404_NOT_FOUND)

        # Estadísticas del cliente
        pedidos_cliente = Pedido.objects.filter(cliente=cliente, estado__in=['pagado', 'en_preparacion', 'enviado', 'entregado'])

        # Estadísticas básicas
        total_pedidos = pedidos_cliente.count()
        total_gastado = pedidos_cliente.aggregate(total=Sum('total'))['total'] or 0
        ticket_promedio = total_gastado / total_pedidos if total_pedidos > 0 else 0

        # Última compra
        ultima_compra = pedidos_cliente.order_by('-fecha_pedido').first()
        ultima_compra_info = None
        if ultima_compra:
            ultima_compra_info = {
                'id': ultima_compra.id,
                'fecha': ultima_compra.fecha_pedido.isoformat(),
                'total': float(ultima_compra.total),
                'estado': ultima_compra.get_estado_display()
            }

        # Productos favoritos (más comprados por este cliente)
        productos_favoritos = []
        if total_pedidos > 0:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT p.nombre, p.id, SUM(dp.cantidad) as cantidad_total,
                           SUM(dp.subtotal) as total_gastado, COUNT(DISTINCT dp.pedido_id) as pedidos_donde_aparece
                    FROM inventario_detallespedido dp
                    JOIN inventario_producto p ON dp.producto_id = p.id
                    JOIN inventario_pedido ped ON dp.pedido_id = ped.id
                    WHERE ped.cliente_id = %s AND ped.estado IN ('pagado', 'en_preparacion', 'enviado', 'entregado')
                    GROUP BY p.nombre, p.id
                    ORDER BY cantidad_total DESC
                    LIMIT 10
                """, [cliente.id])

                for row in cursor.fetchall():
                    productos_favoritos.append({
                        'id': row[1],
                        'nombre': row[0],
                        'cantidad_total': row[2],
                        'total_gastado': float(row[3]),
                        'pedidos_donde_aparece': row[4]
                    })

        # Historial de pedidos (últimos 20)
        historial_pedidos = []
        for pedido in pedidos_cliente.order_by('-fecha_pedido')[:20]:
            detalles_pedido = []
            for detalle in pedido.detalles.all():
                detalles_pedido.append({
                    'producto': {
                        'id': detalle.producto.id,
                        'nombre': detalle.producto.nombre,
                        'sku': getattr(detalle.producto, 'sku', 'N/A')
                    },
                    'cantidad': detalle.cantidad,
                    'precio_unitario': float(detalle.precio_unitario),
                    'subtotal': float(detalle.subtotal)
                })

            historial_pedidos.append({
                'id': pedido.id,
                'fecha_pedido': pedido.fecha_pedido.isoformat(),
                'estado': pedido.get_estado_display(),
                'total': float(pedido.total),
                'subtotal': float(pedido.subtotal or 0),
                'impuesto': float(pedido.impuesto or 0),
                'descuento': float(pedido.descuento or 0),
                'metodo_pago': pedido.metodo_pago or 'N/A',
                'notas': pedido.notas or '',
                'detalles': detalles_pedido
            })

        return Response({
            'success': True,
            'cliente': {
                'id': cliente.id,
                'user': {
                    'id': cliente.user.id,
                    'username': cliente.user.username,
                    'email': cliente.user.email,
                    'first_name': cliente.user.first_name,
                    'last_name': cliente.user.last_name,
                    'date_joined': cliente.user.date_joined.isoformat()
                },
                'rol': cliente.get_rol_display(),
                'fecha_nacimiento': cliente.fecha_nacimiento.isoformat() if cliente.fecha_nacimiento else None,
                'email_confirmado': cliente.email_confirmado,
                'telefono': getattr(cliente, 'telefono', None),
                'direccion': getattr(cliente, 'direccion', None),
                'comuna': getattr(cliente, 'comuna', None),
                'fecha_registro': cliente.user.date_joined.isoformat()  # Usar fecha de registro del usuario
            },
            'estadisticas': {
                'total_pedidos': total_pedidos,
                'total_gastado': float(total_gastado),
                'ticket_promedio': float(ticket_promedio),
                'ultima_compra': ultima_compra_info
            },
            'productos_favoritos': productos_favoritos,
            'historial_pedidos': historial_pedidos
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error al obtener detalle del cliente: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def buscar_clientes(request):
    """
    API endpoint para buscar clientes por email o nombre.
    HU 23: Buscador de clientes por email/nombre en Dashboard
    """
    try:
        usuario_id = request.query_params.get('user_id')
        query = request.query_params.get('q', '').strip()

        if not usuario_id:
            return Response({
                'success': False,
                'message': 'user_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar permisos
        usuario = User.objects.get(id=usuario_id)
        try:
            cliente_usuario = Cliente.objects.get(user=usuario)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Usuario no tiene un cliente asociado.'
            }, status=status.HTTP_403_FORBIDDEN)

        if cliente_usuario.rol not in ['vendedor', 'gerente', 'admin_sistema']:
            return Response({
                'success': False,
                'message': 'Acceso denegado. Solo vendedores, gerentes y administradores pueden buscar clientes.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Buscar clientes
        clientes = Cliente.objects.select_related('user').filter(rol='cliente')

        if query:
            # Buscar por email, nombre o apellido
            clientes = clientes.filter(
                Q(user__email__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(user__username__icontains=query)
            )

        # Limitar resultados y ordenar
        clientes = clientes.order_by('-user__date_joined')[:50]

        # Serializar resultados
        resultados = []
        for cliente in clientes:
            # Estadísticas rápidas
            pedidos_count = Pedido.objects.filter(
                cliente=cliente,
                estado__in=['pagado', 'en_preparacion', 'enviado', 'entregado']
            ).count()

            total_gastado = Pedido.objects.filter(
                cliente=cliente,
                estado__in=['pagado', 'en_preparacion', 'enviado', 'entregado']
            ).aggregate(total=Sum('total'))['total'] or 0

            resultados.append({
                'id': cliente.id,
                'user': {
                    'id': cliente.user.id,
                    'username': cliente.user.username,
                    'email': cliente.user.email,
                    'first_name': cliente.user.first_name,
                    'last_name': cliente.user.last_name,
                    'date_joined': cliente.user.date_joined.isoformat()
                },
                'telefono': getattr(cliente, 'telefono', None),  # Campo opcional
                'fecha_nacimiento': cliente.fecha_nacimiento.isoformat() if cliente.fecha_nacimiento else None,
                'estadisticas': {
                    'total_pedidos': pedidos_count,
                    'total_gastado': float(total_gastado)
                }
            })

        return Response({
            'success': True,
            'query': query,
            'total_resultados': len(resultados),
            'clientes': resultados
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error al buscar clientes: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

# ================================
# FUNCIONES DE UTILIDAD PARA AUTORIZACIONES
# ================================

def reparar_tabla_solicitudes():
    """Función para reparar la tabla de solicitudes si faltan columnas"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            # Verificar si la tabla existe
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables
                WHERE table_schema = DATABASE() AND table_name = 'inventario_solicitudautorizacion'
            """)
            table_exists = cursor.fetchone()[0] > 0

            if not table_exists:
                # Crear la tabla completa
                # Primero, intentar obtener la estructura actual de la tabla para recrearla correctamente
                existing_structure = {}
                try:
                    cursor.execute("""
                        DESCRIBE inventario_solicitudautorizacion
                    """)
                    columns = cursor.fetchall()
                    for col in columns:
                        col_name = col[0]
                        col_type = col[1]
                        is_nullable = col[2] == 'YES'
                        default_value = col[4]
                        existing_structure[col_name] = {
                            'type': col_type,
                            'nullable': is_nullable,
                            'default': default_value
                        }
                except:
                    pass

                # Hacer backup si hay datos
                try:
                    cursor.execute("SELECT COUNT(*) FROM inventario_solicitudautorizacion")
                    count = cursor.fetchone()[0]
                    if count > 0:
                        print(f"Respaldando {count} registros existentes...")
                        # Crear tabla temporal con datos existentes
                        cursor.execute("""
                            CREATE TABLE temp_solicitudes_backup AS
                            SELECT * FROM inventario_solicitudautorizacion
                        """)
                except Exception as e:
                    print(f"Error al hacer backup: {e}")

                # Recrear tabla con estructura completa y compatible
                cursor.execute("""
                    CREATE TABLE inventario_solicitudautorizacion_new (
                        id BIGINT AUTO_INCREMENT PRIMARY KEY,
                        fecha_solicitud DATETIME NOT NULL,
                        fecha_respuesta DATETIME NULL,
                        estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
                        tipo_solicitud VARCHAR(50) NOT NULL,
                        modelo_afectado VARCHAR(100) NOT NULL,
                        id_objeto_afectado VARCHAR(255) NULL,
                        datos_anteriores JSON NULL,
                        datos_nuevos JSON NULL,
                        motivo LONGTEXT NOT NULL,
                        comentario_respuesta LONGTEXT NULL,
                        comentario_revision LONGTEXT NULL,
                        prioridad VARCHAR(20) NOT NULL DEFAULT 'media',
                        ip_solicitante VARCHAR(45) NULL,
                        user_agent_solicitante VARCHAR(255) NULL,
                        solicitante_id BIGINT NOT NULL,
                        aprobador_id BIGINT NULL,
                        producto_afectado_id BIGINT NULL
                    )
                """)

                # Agregar foreign keys por separado para evitar errores
                try:
                    cursor.execute("ALTER TABLE inventario_solicitudautorizacion_new ADD CONSTRAINT fk_solicitante FOREIGN KEY (solicitante_id) REFERENCES auth_user(id)")
                    cursor.execute("ALTER TABLE inventario_solicitudautorizacion_new ADD CONSTRAINT fk_aprobador FOREIGN KEY (aprobador_id) REFERENCES auth_user(id)")
                    cursor.execute("ALTER TABLE inventario_solicitudautorizacion_new ADD CONSTRAINT fk_producto_afectado FOREIGN KEY (producto_afectado_id) REFERENCES inventario_producto(id)")
                except Exception as fk_error:
                    print(f"Error creando foreign keys: {fk_error}")
                    # Continuar sin foreign keys si hay error

                # Intentar migrar datos de la tabla antigua si existe
                try:
                    # Intentar insertar con todos los campos disponibles
                    try:
                        cursor.execute("""
                            INSERT INTO inventario_solicitudautorizacion_new
                            (id, fecha_solicitud, fecha_respuesta, estado, tipo_solicitud, modelo_afectado,
                             id_objeto_afectado, datos_anteriores, datos_nuevos, motivo, comentario_respuesta,
                             comentario_revision, prioridad, ip_solicitante, user_agent_solicitante,
                             solicitante_id, aprobador_id, producto_afectado_id)
                            SELECT id, fecha_solicitud, fecha_respuesta, estado, tipo_solicitud, modelo_afectado,
                                   id_objeto_afectado, datos_anteriores, datos_nuevos, motivo,
                                   COALESCE(comentario_respuesta, ''),
                                   COALESCE(comentario_revision, ''),
                                   COALESCE(prioridad, 'media'),
                                   ip_solicitante, user_agent_solicitante,
                                   solicitante_id, aprobador_id, producto_afectado_id
                            FROM inventario_solicitudautorizacion
                        """)
                    except Exception as insert_error:
                        print(f"Error en inserción completa, intentando inserción básica: {insert_error}")
                        # Intento básico con campos mínimos
                        try:
                            cursor.execute("""
                                INSERT INTO inventario_solicitudautorizacion_new
                                (id, fecha_solicitud, estado, tipo_solicitud, modelo_afectado, motivo, solicitante_id)
                                SELECT id, fecha_solicitud, estado, tipo_solicitud, modelo_afectado, motivo, solicitante_id
                                FROM inventario_solicitudautorizacion
                            """)
                        except Exception as basic_error:
                            print(f"Error incluso en inserción básica: {basic_error}")
                            # Si ni siquiera la básica funciona, continuar sin datos
                    print("Datos migrados exitosamente a nueva tabla")
                except Exception as e:
                    print(f"Error migrando datos (posiblemente tabla vacía): {e}")

                # Reemplazar tabla antigua
                cursor.execute("DROP TABLE IF EXISTS inventario_solicitudautorizacion")
                cursor.execute("RENAME TABLE inventario_solicitudautorizacion_new TO inventario_solicitudautorizacion")

                # Limpiar backup
                try:
                    cursor.execute("DROP TABLE IF EXISTS temp_solicitudes_backup")
                except:
                    pass
                print("Tabla inventario_solicitudautorizacion creada exitosamente")
                return True
            else:
                # Estrategia más agresiva: recrear la tabla si faltan columnas críticas
                cursor.execute("""
                    SELECT COLUMN_NAME FROM information_schema.columns
                    WHERE table_schema = DATABASE() AND table_name = 'inventario_solicitudautorizacion'
                """)
                existing_columns = [row[0] for row in cursor.fetchall()]

                # Columnas críticas que deben existir
                critical_columns = ['id', 'fecha_solicitud', 'estado', 'tipo_solicitud',
                                  'modelo_afectado', 'motivo', 'solicitante_id']

                missing_critical = [col for col in critical_columns if col not in existing_columns]

                if missing_critical:
                    print(f"Columnas críticas faltantes: {missing_critical}. Recreando tabla...")
                    # Hacer backup de datos existentes si es posible
                    try:
                        cursor.execute("SELECT COUNT(*) FROM inventario_solicitudautorizacion")
                        count = cursor.fetchone()[0]
                        if count > 0:
                            print(f"Haciendo backup de {count} registros existentes...")
                            # Crear tabla temporal para backup
                            cursor.execute("""
                                CREATE TABLE temp_solicitudes_backup AS
                                SELECT * FROM inventario_solicitudautorizacion
                            """)
                    except:
                        pass

                    # Recrear tabla
                    cursor.execute("DROP TABLE inventario_solicitudautorizacion")

                    cursor.execute("""
                        CREATE TABLE inventario_solicitudautorizacion (
                            id BIGINT AUTO_INCREMENT PRIMARY KEY,
                            fecha_solicitud DATETIME NOT NULL,
                            fecha_respuesta DATETIME NULL,
                            estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
                            tipo_solicitud VARCHAR(50) NOT NULL,
                            modelo_afectado VARCHAR(100) NOT NULL,
                            id_objeto_afectado VARCHAR(255) NULL,
                            datos_anteriores JSON NULL,
                            datos_nuevos JSON NULL,
                            motivo LONGTEXT NOT NULL,
                            comentario_respuesta LONGTEXT NULL,
                            prioridad VARCHAR(20) NOT NULL DEFAULT 'media',
                            ip_solicitante VARCHAR(45) NULL,
                            user_agent_solicitante VARCHAR(255) NULL,
                            solicitante_id BIGINT NOT NULL,
                            aprobador_id BIGINT NULL,
                            producto_afectado_id BIGINT NULL,
                            FOREIGN KEY (solicitante_id) REFERENCES auth_user(id),
                            FOREIGN KEY (aprobador_id) REFERENCES auth_user(id),
                            FOREIGN KEY (producto_afectado_id) REFERENCES inventario_producto(id)
                        )
                    """)

                    print("Tabla inventario_solicitudautorizacion recreada exitosamente")
                    return True

                # Verificar y agregar columnas faltantes (estrategia original)
                alterations = []

                if 'aprobador_id' not in existing_columns:
                    alterations.append("ADD COLUMN aprobador_id BIGINT NULL")

                if 'fecha_respuesta' not in existing_columns:
                    alterations.append("ADD COLUMN fecha_respuesta DATETIME NULL")

                if 'comentario_respuesta' not in existing_columns:
                    alterations.append("ADD COLUMN comentario_respuesta LONGTEXT NULL")

                if 'prioridad' not in existing_columns:
                    alterations.append("ADD COLUMN prioridad VARCHAR(20) NOT NULL DEFAULT 'media'")

                if 'ip_solicitante' not in existing_columns:
                    alterations.append("ADD COLUMN ip_solicitante VARCHAR(45) NULL")

                if 'user_agent_solicitante' not in existing_columns:
                    alterations.append("ADD COLUMN user_agent_solicitante VARCHAR(255) NULL")

                if 'producto_afectado_id' not in existing_columns:
                    alterations.append("ADD COLUMN producto_afectado_id BIGINT NULL")

                if alterations:
                    alter_sql = f"ALTER TABLE inventario_solicitudautorizacion {', '.join(alterations)}"
                    cursor.execute(alter_sql)
                    print(f"Columnas agregadas a inventario_solicitudautorizacion: {alterations}")
                    return True

        return False
    except Exception as e:
        print(f"Error reparando tabla de solicitudes: {e}")
        import traceback
        traceback.print_exc()
        return False

# ================================
# VISTAS PARA FILTROS AVANZADOS DE VENTAS - HU 50
# ================================

@api_view(['GET'])
def ventas_filtradas_gerente(request):
    """
    API endpoint para filtros avanzados de ventas en dashboard administrativo.
    HU 50: Filtros avanzados de ventas (fecha, vendedor, estado, producto más vendido)
    """
    try:
        # Para GET usar query_params, para otros métodos usar data
        if request.method == 'GET':
            usuario_id = request.query_params.get('usuario_id')
        else:
            usuario_id = request.data.get('usuario_id')

        if not usuario_id:
            return Response({
                'success': False,
                'message': 'usuario_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar permisos (vendedor, gerente o admin_sistema)
        user = User.objects.get(id=usuario_id)
        try:
            cliente = Cliente.objects.get(user=user)
            if cliente.rol not in ['vendedor', 'gerente', 'admin_sistema'] and not (user.is_staff or user.is_superuser):
                return Response({
                    'success': False,
                    'message': 'Acceso denegado. Solo vendedores, gerentes y administradores pueden acceder a estos filtros.'
                }, status=status.HTTP_403_FORBIDDEN)
        except Cliente.DoesNotExist:
            if not (user.is_staff or user.is_superuser):
                return Response({
                    'success': False,
                    'message': 'Acceso denegado. Solo vendedores, gerentes y administradores pueden acceder a estos filtros.'
                }, status=status.HTTP_403_FORBIDDEN)

        # Obtener parámetros de filtro
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        vendedor_id = request.query_params.get('vendedor_id')
        estado_pedido = request.query_params.get('estado')
        producto_id = request.query_params.get('producto_id')
        agrupar_por = request.query_params.get('agrupar_por', 'dia')  # dia, semana, mes

        # Construir queryset base
        pedidos = Pedido.objects.select_related('cliente__user', 'vendedor__user').prefetch_related('detalles__producto')

        # Aplicar filtros
        if fecha_inicio:
            try:
                from datetime import datetime
                dt_inicio = datetime.fromisoformat(fecha_inicio.replace('Z', '+00:00'))
                pedidos = pedidos.filter(fecha_pedido__gte=dt_inicio)
            except:
                pass

        if fecha_fin:
            try:
                from datetime import datetime
                dt_fin = datetime.fromisoformat(fecha_fin.replace('Z', '+00:00'))
                pedidos = pedidos.filter(fecha_pedido__lte=dt_fin)
            except:
                pass

        if vendedor_id:
            pedidos = pedidos.filter(vendedor_id=vendedor_id)

        if estado_pedido:
            pedidos = pedidos.filter(estado=estado_pedido)

        # Obtener datos de ventas agrupadas por período
        from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
        from django.db.models import Sum, Count

        if agrupar_por == 'dia':
            ventas_agrupadas = pedidos.annotate(
                periodo=TruncDay('fecha_pedido')
            ).values('periodo').annotate(
                total_ventas=Sum('total'),
                cantidad_pedidos=Count('id'),
                total_productos=Sum('detalles__cantidad')
            ).order_by('-periodo')
        elif agrupar_por == 'semana':
            ventas_agrupadas = pedidos.annotate(
                periodo=TruncWeek('fecha_pedido')
            ).values('periodo').annotate(
                total_ventas=Sum('total'),
                cantidad_pedidos=Count('id'),
                total_productos=Sum('detalles__cantidad')
            ).order_by('-periodo')
        elif agrupar_por == 'mes':
            ventas_agrupadas = pedidos.annotate(
                periodo=TruncMonth('fecha_pedido')
            ).values('periodo').annotate(
                total_ventas=Sum('total'),
                cantidad_pedidos=Count('id'),
                total_productos=Sum('detalles__cantidad')
            ).order_by('-periodo')

        # Convertir a lista y formatear
        ventas_por_periodo = []
        for venta in ventas_agrupadas:
            ventas_por_periodo.append({
                'periodo': venta['periodo'].isoformat() if venta['periodo'] else None,
                'total_ventas': float(venta['total_ventas'] or 0),
                'cantidad_pedidos': venta['cantidad_pedidos'],
                'total_productos': venta['total_productos'] or 0,
                'promedio_pedido': float(venta['total_ventas'] or 0) / venta['cantidad_pedidos'] if venta['cantidad_pedidos'] > 0 else 0
            })

        # Productos más vendidos con filtros aplicados
        productos_vendidos = []
        if producto_id:
            # Si se filtra por producto específico
            detalles_filtrados = DetallesPedido.objects.filter(
                pedido__in=pedidos,
                producto_id=producto_id
            ).select_related('producto')
        else:
            # Top productos
            detalles_filtrados = DetallesPedido.objects.filter(
                pedido__in=pedidos
            ).select_related('producto')

        # Solo ejecutar consulta SQL si hay pedidos
        if pedidos.exists():
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT p.nombre, p.id, SUM(dp.cantidad) as cantidad_total,
                           SUM(dp.subtotal) as ventas_total,
                           AVG(dp.precio_unitario) as precio_promedio
                    FROM inventario_detallespedido dp
                    JOIN inventario_producto p ON dp.producto_id = p.id
                    WHERE dp.pedido_id IN %s
                    GROUP BY p.nombre, p.id
                    ORDER BY cantidad_total DESC
                    LIMIT 10
                """, [tuple(pedidos.values_list('id', flat=True))])
            for row in cursor.fetchall():
                productos_vendidos.append({
                    'producto_id': row[1],
                    'producto_nombre': row[0],
                    'cantidad_total': row[2],
                    'ventas_total': float(row[3]),
                    'precio_promedio': float(row[4])
                })

        # Ventas por vendedor (si aplica filtro)
        ventas_por_vendedor = []
        if not vendedor_id:
            vendedores_data = pedidos.values('vendedor__user__first_name', 'vendedor__user__last_name', 'vendedor_id').annotate(
                total_ventas=Sum('total'),
                cantidad_pedidos=Count('id')
            ).order_by('-total_ventas')

            for vendedor in vendedores_data:
                if vendedor['vendedor_id']:
                    ventas_por_vendedor.append({
                        'vendedor_id': vendedor['vendedor_id'],
                        'vendedor_nombre': f"{vendedor['vendedor__user__first_name']} {vendedor['vendedor__user__last_name']}",
                        'total_ventas': float(vendedor['total_ventas'] or 0),
                        'cantidad_pedidos': vendedor['cantidad_pedidos']
                    })

        # Estadísticas generales con filtros aplicados
        total_pedidos_filtrados = pedidos.count()
        total_ventas_filtradas = pedidos.aggregate(total=Sum('total'))['total'] or 0
        total_productos_vendidos = pedidos.aggregate(total=Sum('detalles__cantidad'))['total'] or 0

        return Response({
            'success': True,
            'filtros_aplicados': {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'vendedor_id': vendedor_id,
                'estado': estado_pedido,
                'producto_id': producto_id,
                'agrupar_por': agrupar_por
            },
            'estadisticas': {
                'total_pedidos': total_pedidos_filtrados,
                'total_ventas': float(total_ventas_filtradas),
                'total_productos': total_productos_vendidos,
                'promedio_pedido': float(total_ventas_filtradas) / total_pedidos_filtrados if total_pedidos_filtrados > 0 else 0
            },
            'ventas_por_periodo': ventas_por_periodo,
            'productos_mas_vendidos': productos_vendidos,
            'ventas_por_vendedor': ventas_por_vendedor
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Error al obtener ventas filtradas: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


# ================================
# VISTAS PARA MONITOREO DEL SISTEMA - HU 40
# ================================

@api_view(['GET'])
def logs_sistema(request):
    """
    API endpoint para obtener logs del sistema con filtros avanzados.
    Acceso: Solo Admin Sistema
    """
    usuario_id = request.query_params.get('usuario_id')

    if not usuario_id:
        return Response({
            'success': False,
            'message': 'usuario_id es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(id=usuario_id)
        cliente = Cliente.objects.get(user=user)
        if cliente.rol != 'admin_sistema':
            return Response({
                'success': False,
                'message': 'Acceso denegado. Solo administradores del sistema pueden ver logs del sistema.'
            }, status=status.HTTP_403_FORBIDDEN)
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

    try:
        # Obtener parámetros de filtro
        nivel = request.GET.get('nivel')
        categoria = request.GET.get('categoria')
        usuario_log = request.GET.get('usuario_id_log')
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        modulo = request.GET.get('modulo')
        pagina = int(request.GET.get('pagina', 1))
        items_por_pagina = int(request.GET.get('items_por_pagina', 50))

        try:
            # Construir queryset
            queryset = LogSistema.objects.all()

            if nivel:
                queryset = queryset.filter(nivel=nivel)
            if categoria:
                queryset = queryset.filter(categoria=categoria)
            if usuario_log:
                queryset = queryset.filter(usuario_id=usuario_log)
            if modulo:
                queryset = queryset.filter(modulo__icontains=modulo)

            # Filtros de fecha
            if fecha_inicio:
                try:
                    from datetime import datetime
                    dt_inicio = datetime.fromisoformat(fecha_inicio.replace('Z', '+00:00'))
                    queryset = queryset.filter(fecha_creacion__gte=dt_inicio)
                except:
                    pass
            if fecha_fin:
                try:
                    from datetime import datetime
                    dt_fin = datetime.fromisoformat(fecha_fin.replace('Z', '+00:00'))
                    queryset = queryset.filter(fecha_creacion__lte=dt_fin)
                except:
                    pass

            # Paginación
            total = queryset.count()
            inicio = (pagina - 1) * items_por_pagina
            fin = inicio + items_por_pagina
            logs = queryset[inicio:fin]

            # Serializar datos
            logs_data = []
            for log in logs:
                logs_data.append({
                    'id': log.id,
                    'nivel': log.nivel,
                    'nivel_display': log.get_nivel_display(),
                    'categoria': log.categoria,
                    'categoria_display': log.get_categoria_display(),
                    'mensaje': log.mensaje,
                    'datos_extra': log.datos_extra,
                    'usuario': log.usuario.username if log.usuario else None,
                    'usuario_email': log.usuario.email if log.usuario else None,
                    'ip_address': log.ip_address,
                    'fecha_creacion': log.fecha_creacion.isoformat(),
                    'modulo': log.modulo,
                    'funcion': log.funcion
                })

            total_paginas = (total + items_por_pagina - 1) // items_por_pagina

        except Exception as e:
            # Si las tablas no existen, devolver datos vacíos
            print(f"Advertencia: Tabla LogSistema no disponible: {e}")
            total = 0
            pagina = 1
            total_paginas = 0
            items_por_pagina = 50
            logs_data = []

        return Response({
            'success': True,
            'total': total,
            'pagina': pagina,
            'total_paginas': total_paginas,
            'items_por_pagina': items_por_pagina,
            'logs': logs_data
        })

    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al obtener logs del sistema: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def estadisticas_sistema(request):
    """
    API endpoint para obtener estadísticas de monitoreo del sistema.
    Acceso: Solo Admin Sistema
    """
    usuario_id = request.query_params.get('usuario_id')

    if not usuario_id:
        return Response({
            'success': False,
            'message': 'usuario_id es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(id=usuario_id)
        cliente = Cliente.objects.get(user=user)
        if cliente.rol != 'admin_sistema':
            return Response({
                'success': False,
                'message': 'Acceso denegado. Solo administradores del sistema pueden ver estadísticas del sistema.'
            }, status=status.HTTP_403_FORBIDDEN)
    except (User.DoesNotExist, Cliente.DoesNotExist) as e:
        print(f"Error de autenticación: {e}")
        return Response({
            'success': False,
            'message': 'Usuario o cliente no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)

    try:
        from django.db.models import Count, Sum, Avg
        from django.db.models.functions import TruncHour, TruncDay, TruncMonth
        from datetime import datetime, timedelta

        # Estadísticas de logs del sistema (con manejo de tablas inexistentes)
        try:
            logs_totales = LogSistema.objects.count()
            logs_por_nivel = LogSistema.objects.values('nivel').annotate(cantidad=Count('id')).order_by('-cantidad')
            logs_por_categoria = LogSistema.objects.values('categoria').annotate(cantidad=Count('id')).order_by('-cantidad')

            # Logs de las últimas 24 horas
            hace_24h = datetime.now() - timedelta(hours=24)
            logs_ultimas_24h = LogSistema.objects.filter(fecha_creacion__gte=hace_24h).count()

            # Logs críticos de las últimas 24 horas
            logs_criticos_24h = LogSistema.objects.filter(
                fecha_creacion__gte=hace_24h,
                nivel__in=['error', 'critical']
            ).count()

            # Usuarios activos (con actividad en las últimas 24h)
            usuarios_activos_24h = LogSistema.objects.filter(
                fecha_creacion__gte=hace_24h
            ).values('usuario').distinct().count()
        except Exception as e:
            # Si las tablas no existen, devolver valores por defecto
            print(f"Advertencia: Tablas de LogSistema no disponibles: {e}")
            logs_totales = 0
            logs_por_nivel = []
            logs_por_categoria = []
            logs_ultimas_24h = 0
            logs_criticos_24h = 0
            usuarios_activos_24h = 0

        # Estadísticas de visitas a productos (con manejo de tablas inexistentes)
        try:
            visitas_totales = EstadisticaVisita.objects.count()
            productos_mas_visitados = EstadisticaVisita.objects.values('producto__nombre').annotate(
                visitas=Count('id')
            ).order_by('-visitas')[:10]

            # Visitas por fuente - simplificado para evitar problemas de columnas
            visitas_por_fuente = []
        except Exception as e:
            # Si las tablas no existen, devolver valores por defecto
            print(f"Advertencia: Tablas de EstadisticaVisita no disponibles: {e}")
            visitas_totales = 0
            productos_mas_visitados = []
            visitas_por_fuente = []

        # Pedidos por hora (últimas 24 horas)
        pedidos_por_hora = Pedido.objects.filter(
            fecha_pedido__gte=hace_24h
        ).annotate(
            hora=TruncHour('fecha_pedido')
        ).values('hora').annotate(
            cantidad=Count('id')
        ).order_by('hora')

        # Pedidos por día (últimos 7 días)
        hace_7_dias = datetime.now() - timedelta(days=7)
        pedidos_por_dia = Pedido.objects.filter(
            fecha_pedido__gte=hace_7_dias
        ).annotate(
            dia=TruncDay('fecha_pedido')
        ).values('dia').annotate(
            cantidad=Count('id'),
            total_ventas=Sum('total')
        ).order_by('dia')

        return Response({
            'success': True,
            'estadisticas': {
                'logs_sistema': {
                    'total': logs_totales,
                    'ultimas_24h': logs_ultimas_24h,
                    'criticos_24h': logs_criticos_24h,
                    'por_nivel': list(logs_por_nivel),
                    'por_categoria': list(logs_por_categoria)
                },
                'visitas_productos': {
                    'total': visitas_totales,
                    'productos_mas_visitados': list(productos_mas_visitados),
                    'por_fuente': list(visitas_por_fuente)
                },
                'actividad': {
                    'usuarios_activos_24h': usuarios_activos_24h,
                    'pedidos_por_hora': [
                        {
                            'hora': item['hora'].isoformat() if item['hora'] else None,
                            'cantidad': item['cantidad']
                        }
                        for item in pedidos_por_hora
                    ],
                    'pedidos_por_dia': [
                        {
                            'dia': item['dia'].isoformat() if item['dia'] else None,
                            'cantidad': item['cantidad'],
                            'total_ventas': float(item['total_ventas'] or 0)
                        }
                        for item in pedidos_por_dia
                    ]
                }
            }
        })

    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al obtener estadísticas del sistema: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def sugerencias_productos(request):
    """API endpoint para autocompletado de productos"""
    try:
        query = request.GET.get('q', '').strip()
        
        if not query or len(query) < 2:
            return Response({
                'sugerencias': [],
                'mensaje': 'Ingrese al menos 2 caracteres'
            })
        
        # Buscar en nombre, SKU y descripción
        productos = Producto.objects.filter(
            activo=True
        ).filter(
            Q(nombre__icontains=query) |
            Q(sku__icontains=query) |
            Q(descripcion__icontains=query)
        )[:15]  # Limitar a 15 resultados
        
        sugerencias = []
        for p in productos:
            sugerencias.append({
                'id': p.id,
                'nombre': p.nombre,
                'sku': p.sku,
                'precio': float(p.precio) if p.precio else 0,
                'categoria': p.categoria.nombre,
            })
        
        return Response({
            'sugerencias': sugerencias,
            'total': len(sugerencias)
        })
    
    except Exception as e:
        return Response({
            'error': str(e),
            'sugerencias': []
        }, status=400)



@api_view(['POST'])
def registrar_visita_producto(request):
    """
    API endpoint para registrar una visita a un producto.
    Acceso: Todos los usuarios (incluyendo anónimos)
    """
    try:
        producto_id = request.data.get('producto_id')
        tiempo_visualizacion = request.data.get('tiempo_visualizacion', 0)
        fuente = request.data.get('fuente', 'catalogo')

        if not producto_id:
            return Response({
                'success': False,
                'message': 'producto_id es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Obtener usuario si está autenticado
        usuario = None
        try:
            usuario_id = request.data.get('usuario_id')
            if usuario_id:
                usuario = User.objects.get(id=usuario_id)
        except:
            pass

        # Obtener producto
        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Producto no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

        # Obtener IP y User-Agent
        ip_address = _get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Registrar visita
        EstadisticaVisita.objects.create(
            producto=producto,
            usuario=usuario,
            tiempo_visualizacion=tiempo_visualizacion,
            fuente=fuente,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return Response({
            'success': True,
            'message': 'Visita registrada correctamente'
        })

    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al registrar visita: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


# ==================== REPORTES FINANCIEROS ====================

@api_view(['POST'])
def generar_reporte_financiero(request):
    """
    API endpoint para generar reportes financieros en PDF
    
    POST body:
    {
        "tipo_reporte": "resumen_completo|ventas_general|productos_top|ingresos_categoria|comparativa_periodos",
        "fecha_inicio": "YYYY-MM-DD",
        "fecha_fin": "YYYY-MM-DD",
        "categoria_id": (opcional),
        "emails_destino": ["email1@example.com", "email2@example.com"] (opcional),
        "enviar_email": true/false (opcional)
    }
    """
    from datetime import datetime
    from .reportes_service import GeneradorReporteFinanciero
    from django.core.files.base import ContentFile
    import json
    
    # Verificar permiso
    if not request.user.is_authenticated:
        return Response({
            'success': False,
            'message': 'Debe estar autenticado'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        cliente = Cliente.objects.get(user=request.user)
        if cliente.rol not in ['gerente', 'admin_sistema']:
            return Response({
                'success': False,
                'message': 'Solo gerentes y administradores pueden generar reportes'
            }, status=status.HTTP_403_FORBIDDEN)
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no tiene perfil de cliente'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Validar datos
        tipo_reporte = request.data.get('tipo_reporte', 'resumen_completo')
        fecha_inicio_str = request.data.get('fecha_inicio')
        fecha_fin_str = request.data.get('fecha_fin')
        categoria_id = request.data.get('categoria_id')
        emails_destino = request.data.get('emails_destino', [])
        enviar_email = request.data.get('enviar_email', False)
        
        if not fecha_inicio_str or not fecha_fin_str:
            return Response({
                'success': False,
                'message': 'fecha_inicio y fecha_fin son requeridas'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Convertir fechas
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
        
        if fecha_inicio > fecha_fin:
            return Response({
                'success': False,
                'message': 'fecha_inicio debe ser menor que fecha_fin'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener categoría si se especifica
        categoria = None
        if categoria_id:
            try:
                categoria = Categoria.objects.get(id=categoria_id)
            except Categoria.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Categoría no encontrada'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Generar PDF
        generador = GeneradorReporteFinanciero(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tipo_reporte=tipo_reporte,
            categoria=categoria
        )
        
        pdf_buffer = generador.generar_pdf()
        
        # Crear registro de reporte
        nombre_archivo = f"reporte_{tipo_reporte}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        reporte = ReporteFinanciero(
            generador=request.user,
            tipo_reporte=tipo_reporte,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            categoria=categoria,
            estado='generado',
            emails_destino=json.dumps(emails_destino) if emails_destino else '[]'
        )
        
        # Guardar PDF
        reporte.archivo_pdf.save(nombre_archivo, ContentFile(pdf_buffer.getvalue()))
        reporte.save()
        
        # Registrar auditoría
        AuditLog.objects.create(
            usuario=request.user,
            accion='generar_reporte_financiero',
            tabla='inventario_reportefinanciero',
            registro_id=reporte.id,
            detalles=f"Reporte {tipo_reporte} generado para período {fecha_inicio} a {fecha_fin}"
        )
        
        # Enviar email si se solicita
        if enviar_email and emails_destino:
            try:
                send_mail(
                    subject=f'Reporte Financiero - {tipo_reporte}',
                    message=f'Se ha generado el reporte solicitado para el período {fecha_inicio} a {fecha_fin}.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=emails_destino,
                    fail_silently=False,
                    html_message=f'<h2>Reporte Financiero</h2><p>Se ha generado el reporte <strong>{tipo_reporte}</strong> para el período <strong>{fecha_inicio}</strong> a <strong>{fecha_fin}</strong>.</p>'
                )
                reporte.estado = 'enviado_email'
                reporte.save()
            except Exception as e:
                # No fallar si no se puede enviar email
                AuditLog.objects.create(
                    usuario=request.user,
                    accion='error_envio_email_reporte',
                    tabla='inventario_reportefinanciero',
                    registro_id=reporte.id,
                    detalles=f"Error al enviar email: {str(e)}"
                )
        
        return Response({
            'success': True,
            'message': 'Reporte generado correctamente',
            'reporte_id': reporte.id,
            'archivo': reporte.archivo_pdf.url if reporte.archivo_pdf else None,
            'generado_en': reporte.fecha_creacion.isoformat()
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        import traceback
        return Response({
            'success': False,
            'message': f'Error al generar reporte: {str(e)}',
            'detalle': traceback.format_exc() if settings.DEBUG else None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def listar_reportes_financieros(request):
    """
    API endpoint para listar reportes financieros generados
    
    Parámetros de query:
    - tipo_reporte: filtrar por tipo (opcional)
    - estado: filtrar por estado (opcional)
    - limite: cantidad de reportes a mostrar (default: 50)
    """
    
    # Verificar autenticación
    if not request.user.is_authenticated:
        return Response({
            'success': False,
            'message': 'Debe estar autenticado'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        cliente = Cliente.objects.get(user=request.user)
        if cliente.rol not in ['gerente', 'admin_sistema']:
            return Response({
                'success': False,
                'message': 'Solo gerentes y administradores pueden ver reportes'
            }, status=status.HTTP_403_FORBIDDEN)
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no tiene perfil de cliente'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Aplicar filtros
        reportes = ReporteFinanciero.objects.all().order_by('-fecha_creacion')
        
        tipo_reporte = request.query_params.get('tipo_reporte')
        if tipo_reporte:
            reportes = reportes.filter(tipo_reporte=tipo_reporte)
        
        estado = request.query_params.get('estado')
        if estado:
            reportes = reportes.filter(estado=estado)
        
        # Limitar resultados
        limite = int(request.query_params.get('limite', 50))
        reportes = reportes[:limite]
        
        # Serializar
        datos_reportes = []
        for reporte in reportes:
            datos_reportes.append({
                'id': reporte.id,
                'tipo_reporte': reporte.tipo_reporte,
                'fecha_inicio': reporte.fecha_inicio.isoformat(),
                'fecha_fin': reporte.fecha_fin.isoformat(),
                'estado': reporte.estado,
                'generado_por': reporte.generador.email,
                'fecha_creacion': reporte.fecha_creacion.isoformat(),
                'archivo_url': reporte.archivo_pdf.url if reporte.archivo_pdf else None,
                'categoria': reporte.categoria.nombre if reporte.categoria else None
            })
        
        return Response({
            'success': True,
            'cantidad': len(datos_reportes),
            'reportes': datos_reportes
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al listar reportes: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def eliminar_reporte(request, reporte_id):
    """API endpoint para eliminar un reporte financiero"""
    
    if not request.user.is_authenticated:
        return Response({
            'success': False,
            'message': 'Debe estar autenticado'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        reporte = ReporteFinanciero.objects.get(id=reporte_id)
        
        # Verificar permiso (solo el generador o admin)
        cliente = Cliente.objects.get(user=request.user)
        if reporte.generador != request.user and cliente.rol != 'admin_sistema':
            return Response({
                'success': False,
                'message': 'No tiene permiso para eliminar este reporte'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Eliminar archivo
        if reporte.archivo_pdf:
            reporte.archivo_pdf.delete()
        
        # Registrar auditoría
        AuditLog.objects.create(
            usuario=request.user,
            accion='eliminar_reporte_financiero',
            tabla='inventario_reportefinanciero',
            registro_id=reporte.id,
            detalles=f"Reporte {reporte.tipo_reporte} eliminado"
        )
        
        reporte.delete()
        
        return Response({
            'success': True,
            'message': 'Reporte eliminado correctamente'
        })
        
    except ReporteFinanciero.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Reporte no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al eliminar reporte: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ENDPOINTS PARA CUPONES Y PROMOCIONES (HU 11) ====================

def _verificar_permisos_gerente_admin(usuario):
    """Verifica si el usuario tiene permisos de gerente o admin"""
    if not usuario or not usuario.is_authenticated:
        return False
    
    if usuario.is_superuser or usuario.is_staff:
        return True
    
    try:
        cliente = Cliente.objects.get(user=usuario)
        return cliente.rol in ['gerente', 'admin_sistema']
    except Cliente.DoesNotExist:
        return False


@api_view(['GET', 'POST'])
def gestionar_cupones(request):
    """CRUD completo para cupones - Solo gerentes y admins"""
    from .serializers import CuponSerializer
    # Obtener usuario_id de query params o data
    usuario_id = request.query_params.get('usuario_id') or request.data.get('usuario_id')
    
    if not usuario_id:
        return Response({
            'success': False,
            'message': 'usuario_id es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id=usuario_id)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Verificar permisos
    if not _verificar_permisos_gerente_admin(user):
        return Response({
            'success': False,
            'message': 'Acceso denegado. Solo gerentes y administradores pueden gestionar cupones.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        # Listar cupones
        try:
            cupones = Cupon.objects.all().order_by('-fecha_creacion')
            serializer = CuponSerializer(cupones, many=True)
            return Response({
                'success': True,
                'cupones': serializer.data
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al listar cupones: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        # Crear cupón
        try:
            data = request.data.copy()
            
            # Validaciones
            codigo = data.get('codigo', '').strip().upper()
            if not codigo:
                return Response({
                    'success': False,
                    'message': 'El código del cupón es requerido'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verificar que el código no exista
            if Cupon.objects.filter(codigo=codigo).exists():
                return Response({
                    'success': False,
                    'message': 'Ya existe un cupón con ese código'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            tipo_descuento = data.get('tipo_descuento', 'porcentaje')
            descuento_porcentaje = data.get('descuento_porcentaje')
            descuento_monto = data.get('descuento_monto')
            
            # Validar que tenga al menos un tipo de descuento
            if tipo_descuento == 'porcentaje' and not descuento_porcentaje:
                return Response({
                    'success': False,
                    'message': 'El descuento porcentaje es requerido para cupones de tipo porcentaje'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if tipo_descuento == 'monto' and not descuento_monto:
                return Response({
                    'success': False,
                    'message': 'El descuento monto es requerido para cupones de tipo monto'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validar porcentaje
            if descuento_porcentaje and (float(descuento_porcentaje) < 0 or float(descuento_porcentaje) > 100):
                return Response({
                    'success': False,
                    'message': 'El descuento porcentaje debe estar entre 0 y 100'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validar fechas
            fecha_inicio = data.get('fecha_inicio')
            fecha_fin = data.get('fecha_fin')
            if not fecha_inicio or not fecha_fin:
                return Response({
                    'success': False,
                    'message': 'Las fechas de inicio y fin son requeridas'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Crear cupón
            data['codigo'] = codigo
            data['creado_por'] = user.id
            serializer = CuponSerializer(data=data)
            
            if serializer.is_valid():
                cupon = serializer.save()
                
                # Registrar auditoría
                ip_address = _get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                AuditLog.registrar_cambio(
                    usuario=user,
                    tipo_accion='crear',
                    modelo='Cupon',
                    id_objeto=str(cupon.id),
                    datos_nuevos=serializer.data,
                    descripcion=f'Cupón {cupon.codigo} creado por {user.email}',
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                return Response({
                    'success': True,
                    'message': 'Cupón creado exitosamente',
                    'cupon': CuponSerializer(cupon).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': 'Error de validación',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al crear cupón: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
def gestionar_cupon(request, cupon_id):
    """Obtener, actualizar o eliminar un cupón específico"""
    from .serializers import CuponSerializer
    
    # Obtener usuario_id de query params o data
    usuario_id = request.query_params.get('usuario_id') or request.data.get('usuario_id')
    
    if not usuario_id:
        return Response({
            'success': False,
            'message': 'usuario_id es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id=usuario_id)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Verificar permisos
    if not _verificar_permisos_gerente_admin(user):
        return Response({
            'success': False,
            'message': 'Acceso denegado. Solo gerentes y administradores pueden gestionar cupones.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        cupon = Cupon.objects.get(id=cupon_id)
    except Cupon.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Cupón no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = CuponSerializer(cupon)
        return Response({
            'success': True,
            'cupon': serializer.data
        })
    
    elif request.method == 'PUT':
        try:
            data = request.data.copy()
            
            # No permitir cambiar el código
            if 'codigo' in data:
                del data['codigo']
            
            # Validaciones similares a crear
            tipo_descuento = data.get('tipo_descuento', cupon.tipo_descuento)
            descuento_porcentaje = data.get('descuento_porcentaje')
            descuento_monto = data.get('descuento_monto')
            
            if tipo_descuento == 'porcentaje' and descuento_porcentaje:
                if float(descuento_porcentaje) < 0 or float(descuento_porcentaje) > 100:
                    return Response({
                        'success': False,
                        'message': 'El descuento porcentaje debe estar entre 0 y 100'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = CuponSerializer(cupon, data=data, partial=True)
            if serializer.is_valid():
                datos_anteriores = CuponSerializer(cupon).data
                cupon = serializer.save()
                
                # Registrar auditoría
                ip_address = _get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                AuditLog.registrar_cambio(
                    usuario=user,
                    tipo_accion='modificar',
                    modelo='Cupon',
                    id_objeto=str(cupon.id),
                    datos_anteriores=datos_anteriores,
                    datos_nuevos=serializer.data,
                    descripcion=f'Cupón {cupon.codigo} modificado por {user.email}',
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                return Response({
                    'success': True,
                    'message': 'Cupón actualizado exitosamente',
                    'cupon': CuponSerializer(cupon).data
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Error de validación',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al actualizar cupón: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            codigo_cupon = cupon.codigo
            
            # Registrar auditoría antes de eliminar
            ip_address = _get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            AuditLog.registrar_cambio(
                usuario=user,
                tipo_accion='eliminar',
                modelo='Cupon',
                id_objeto=str(cupon.id),
                datos_anteriores=CuponSerializer(cupon).data,
                descripcion=f'Cupón {codigo_cupon} eliminado por {user.email}',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            cupon.delete()
            return Response({
                'success': True,
                'message': 'Cupón eliminado exitosamente'
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al eliminar cupón: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def validar_cupon(request):
    """Validar un cupón para usar en checkout - Acceso público"""
    try:
        codigo = request.data.get('codigo', '').strip().upper()
        monto_total = float(request.data.get('monto_total', 0))
        
        if not codigo:
            return Response({
                'success': False,
                'message': 'El código del cupón es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cupon = Cupon.objects.get(codigo=codigo)
        except Cupon.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Cupón no encontrado',
                'valido': False
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validar cupón
        if not cupon.es_valido():
            return Response({
                'success': False,
                'message': 'El cupón no está vigente o ha alcanzado su límite de usos',
                'valido': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar monto mínimo (convertir ambos a float para comparación)
        monto_minimo_float = float(cupon.monto_minimo)
        if monto_total < monto_minimo_float:
            return Response({
                'success': False,
                'message': f'El monto mínimo para usar este cupón es ${monto_minimo_float}',
                'valido': False,
                'monto_minimo': monto_minimo_float
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calcular descuento (el método retorna Decimal, convertir a float)
        from decimal import Decimal
        descuento_decimal = cupon.calcular_descuento(monto_total)
        descuento = float(descuento_decimal)
        monto_final = monto_total - descuento
        
        return Response({
            'success': True,
            'valido': True,
            'cupon': {
                'codigo': cupon.codigo,
                'tipo_descuento': cupon.tipo_descuento,
                'descuento_porcentaje': float(cupon.descuento_porcentaje) if cupon.descuento_porcentaje else None,
                'descuento_monto': float(cupon.descuento_monto) if cupon.descuento_monto else None,
            },
            'descuento': float(descuento),
            'monto_original': float(monto_total),
            'monto_final': float(monto_final)
        })
        
    except ValueError:
        return Response({
            'success': False,
            'message': 'El monto total debe ser un número válido'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al validar cupón: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
def gestionar_promociones(request):
    """CRUD completo para promociones de productos - Solo gerentes y admins"""
    from .serializers import PromocionProductoSerializer
    
    # Verificar permisos
    if not _verificar_permisos_gerente_admin(request.user):
        return Response({
            'success': False,
            'message': 'Acceso denegado. Solo gerentes y administradores pueden gestionar promociones.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        # Listar promociones
        try:
            producto_id = request.query_params.get('producto_id')
            if producto_id:
                promociones = PromocionProducto.objects.filter(producto_id=producto_id).order_by('-fecha_creacion')
            else:
                promociones = PromocionProducto.objects.all().order_by('-fecha_creacion')
            
            serializer = PromocionProductoSerializer(promociones, many=True)
            return Response({
                'success': True,
                'promociones': serializer.data
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al listar promociones: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        # Crear promoción
        try:
            data = request.data.copy()
            
            # Validaciones
            producto_id = data.get('producto')
            if not producto_id:
                return Response({
                    'success': False,
                    'message': 'El producto es requerido'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                producto = Producto.objects.get(id=producto_id)
            except Producto.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Producto no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            
            descuento_porcentaje = data.get('descuento_porcentaje')
            if not descuento_porcentaje:
                return Response({
                    'success': False,
                    'message': 'El descuento porcentaje es requerido'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            descuento_porcentaje = float(descuento_porcentaje)
            if descuento_porcentaje < 0 or descuento_porcentaje > 100:
                return Response({
                    'success': False,
                    'message': 'El descuento porcentaje debe estar entre 0 y 100'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            fecha_inicio = data.get('fecha_inicio')
            fecha_fin = data.get('fecha_fin')
            if not fecha_inicio or not fecha_fin:
                return Response({
                    'success': False,
                    'message': 'Las fechas de inicio y fin son requeridas'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Crear promoción
            data['creado_por'] = request.user.id
            serializer = PromocionProductoSerializer(data=data)
            
            if serializer.is_valid():
                promocion = serializer.save()
                
                # Registrar auditoría
                ip_address = _get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                AuditLog.registrar_cambio(
                    usuario=request.user,
                    tipo_accion='crear',
                    modelo='PromocionProducto',
                    id_objeto=str(promocion.id),
                    datos_nuevos=serializer.data,
                    descripcion=f'Promoción creada para {producto.nombre} por {request.user.email}',
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                return Response({
                    'success': True,
                    'message': 'Promoción creada exitosamente',
                    'promocion': PromocionProductoSerializer(promocion).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': 'Error de validación',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al crear promoción: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
def gestionar_promocion(request, promocion_id):
    """Obtener, actualizar o eliminar una promoción específica"""
    from .serializers import PromocionProductoSerializer
    
    # Verificar permisos
    if not _verificar_permisos_gerente_admin(request.user):
        return Response({
            'success': False,
            'message': 'Acceso denegado. Solo gerentes y administradores pueden gestionar promociones.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        promocion = PromocionProducto.objects.get(id=promocion_id)
    except PromocionProducto.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Promoción no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = PromocionProductoSerializer(promocion)
        return Response({
            'success': True,
            'promocion': serializer.data
        })
    
    elif request.method == 'PUT':
        try:
            data = request.data.copy()
            
            # Validar descuento si se proporciona
            if 'descuento_porcentaje' in data:
                descuento_porcentaje = float(data['descuento_porcentaje'])
                if descuento_porcentaje < 0 or descuento_porcentaje > 100:
                    return Response({
                        'success': False,
                        'message': 'El descuento porcentaje debe estar entre 0 y 100'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = PromocionProductoSerializer(promocion, data=data, partial=True)
            if serializer.is_valid():
                datos_anteriores = PromocionProductoSerializer(promocion).data
                promocion = serializer.save()
                
                # Registrar auditoría
                ip_address = _get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                AuditLog.registrar_cambio(
                    usuario=request.user,
                    tipo_accion='modificar',
                    modelo='PromocionProducto',
                    id_objeto=str(promocion.id),
                    datos_anteriores=datos_anteriores,
                    datos_nuevos=serializer.data,
                    descripcion=f'Promoción de {promocion.producto.nombre} modificada por {request.user.email}',
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                
                return Response({
                    'success': True,
                    'message': 'Promoción actualizada exitosamente',
                    'promocion': PromocionProductoSerializer(promocion).data
                })
            else:
                return Response({
                    'success': False,
                    'message': 'Error de validación',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al actualizar promoción: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'DELETE':
        try:
            producto_nombre = promocion.producto.nombre
            
            # Registrar auditoría antes de eliminar
            ip_address = _get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            AuditLog.registrar_cambio(
                usuario=request.user,
                tipo_accion='eliminar',
                modelo='PromocionProducto',
                id_objeto=str(promocion.id),
                datos_anteriores=PromocionProductoSerializer(promocion).data,
                descripcion=f'Promoción de {producto_nombre} eliminada por {request.user.email}',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            promocion.delete()
            return Response({
                'success': True,
                'message': 'Promoción eliminada exitosamente'
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al eliminar promoción: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def reportes_efectividad_promociones(request):
    """Reportes de efectividad de cupones y promociones - Solo gerentes y admins"""
    from django.db.models import Sum, Count, Avg
    from django.utils import timezone
    from datetime import timedelta
    
    # Verificar permisos
    if not _verificar_permisos_gerente_admin(request.user):
        return Response({
            'success': False,
            'message': 'Acceso denegado. Solo gerentes y administradores pueden ver reportes.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Parámetros opcionales
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        
        # Reporte de cupones más usados
        cupones_usados = Cupon.objects.filter(usos_actuales__gt=0).order_by('-usos_actuales')[:10]
        cupones_data = []
        for cupon in cupones_usados:
            cupones_data.append({
                'codigo': cupon.codigo,
                'tipo_descuento': cupon.tipo_descuento,
                'descuento_porcentaje': float(cupon.descuento_porcentaje) if cupon.descuento_porcentaje else None,
                'descuento_monto': float(cupon.descuento_monto) if cupon.descuento_monto else None,
                'usos_actuales': cupon.usos_actuales,
                'usos_maximos': cupon.usos_maximos,
                'porcentaje_uso': round((cupon.usos_actuales / cupon.usos_maximos) * 100, 2) if cupon.usos_maximos > 0 else 0
            })
        
        # Reporte de descuentos otorgados (estimado basado en usos)
        total_descuentos_estimado = 0
        for cupon in Cupon.objects.filter(usos_actuales__gt=0):
            # Estimación: promedio de $50 por uso (esto se puede mejorar con datos reales de pedidos)
            if cupon.tipo_descuento == 'porcentaje' and cupon.descuento_porcentaje:
                total_descuentos_estimado += (50 * cupon.usos_actuales * float(cupon.descuento_porcentaje)) / 100
            elif cupon.tipo_descuento == 'monto' and cupon.descuento_monto:
                total_descuentos_estimado += float(cupon.descuento_monto) * cupon.usos_actuales
        
        # Reporte de productos con promoción
        ahora = timezone.now()
        promociones_activas = PromocionProducto.objects.filter(
            activa=True,
            fecha_inicio__lte=ahora,
            fecha_fin__gte=ahora
        )
        
        productos_con_promocion = []
        for promocion in promociones_activas:
            productos_con_promocion.append({
                'producto_id': promocion.producto.id,
                'producto_nombre': promocion.producto.nombre,
                'descuento_porcentaje': float(promocion.descuento_porcentaje),
                'precio_original': float(promocion.producto.precio),
                'precio_con_descuento': float(promocion.calcular_precio_con_descuento()),
                'fecha_inicio': promocion.fecha_inicio.isoformat(),
                'fecha_fin': promocion.fecha_fin.isoformat()
            })
        
        # Estadísticas generales
        total_cupones = Cupon.objects.count()
        cupones_activos = Cupon.objects.filter(activo=True).count()
        cupones_vigentes = Cupon.objects.filter(
            activo=True,
            fecha_inicio__lte=ahora,
            fecha_fin__gte=ahora,
            usos_actuales__lt=F('usos_maximos')
        ).count()
        
        total_promociones = PromocionProducto.objects.count()
        promociones_activas_count = promociones_activas.count()
        
        return Response({
            'success': True,
            'reporte': {
                'cupones_mas_usados': cupones_data,
                'total_descuentos_estimado': round(total_descuentos_estimado, 2),
                'productos_con_promocion': productos_con_promocion,
                'estadisticas': {
                    'total_cupones': total_cupones,
                    'cupones_activos': cupones_activos,
                    'cupones_vigentes': cupones_vigentes,
                    'total_promociones': total_promociones,
                    'promociones_activas': promociones_activas_count
                }
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al generar reporte: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ENDPOINTS PARA RECLAMOS (HU 18) ====================

def _verificar_permisos_reclamos(user):
    """Verifica si el usuario tiene permisos para gestionar reclamos"""
    try:
        cliente = user.cliente
        return cliente.rol in ['vendedor', 'gerente', 'admin_sistema']
    except:
        return user.is_superuser


def _enviar_notificacion_reclamo(reclamo, tipo_cambio='estado'):
    """Envía notificación por email cuando cambia el estado de un reclamo"""
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        cliente_email = reclamo.cliente.user.email
        cliente_nombre = reclamo.cliente.user.get_full_name() or reclamo.cliente.user.email
        
        if tipo_cambio == 'estado':
            asunto = f"Actualización de Reclamo #{reclamo.id} - {reclamo.titulo}"
            mensaje = f"""
Hola {cliente_nombre},

Tu reclamo ha sido actualizado:

Reclamo: {reclamo.titulo}
Estado: {reclamo.get_estado_display()}
Tipo: {reclamo.get_tipo_display()}
Prioridad: {reclamo.get_prioridad_display()}

"""
            if reclamo.resolucion:
                mensaje += f"Resolución:\n{reclamo.resolucion}\n\n"
            
            if reclamo.asignado_a:
                mensaje += f"Asignado a: {reclamo.asignado_a.get_full_name() or reclamo.asignado_a.email}\n"
            
            mensaje += f"\nPuedes ver más detalles en el sistema.\n\nSaludos,\nEquipo de Atención al Cliente"
        
        elif tipo_cambio == 'comentario':
            ultimo_comentario = reclamo.comentarios.last()
            if ultimo_comentario and not ultimo_comentario.es_interno:
                asunto = f"Nuevo comentario en Reclamo #{reclamo.id}"
                mensaje = f"""
Hola {cliente_nombre},

Se ha agregado un nuevo comentario a tu reclamo:

Reclamo: {reclamo.titulo}
Comentario: {ultimo_comentario.comentario}
Por: {ultimo_comentario.usuario.get_full_name() or ultimo_comentario.usuario.email}

Puedes ver más detalles en el sistema.

Saludos,
Equipo de Atención al Cliente
"""
            else:
                return  # No enviar email si es comentario interno
        
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [cliente_email],
            fail_silently=True
        )
    except Exception as e:
        print(f"Error enviando notificación de reclamo: {e}")


@api_view(['GET', 'POST'])
def gestionar_reclamos(request):
    """CRUD completo para reclamos"""
    from .serializers import ReclamoSerializer
    
    usuario_id = request.query_params.get('usuario_id') or request.data.get('usuario_id')
    
    if not usuario_id:
        return Response({
            'success': False,
            'message': 'usuario_id es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id=usuario_id)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # Listar reclamos
        try:
            cliente = user.cliente
            rol = cliente.rol
            
            # Filtros
            estado = request.query_params.get('estado')
            tipo = request.query_params.get('tipo')
            prioridad = request.query_params.get('prioridad')
            cliente_id = request.query_params.get('cliente_id')
            
            # Construir query
            query = Q()
            
            # Si es cliente, solo ver sus propios reclamos
            if rol == 'cliente':
                query &= Q(cliente=cliente)
            # Si es vendedor/gerente/admin, puede ver todos o filtrar por cliente
            elif rol in ['vendedor', 'gerente', 'admin_sistema']:
                if cliente_id:
                    query &= Q(cliente_id=cliente_id)
                # Si está asignado a alguien, puede ver los asignados a él
                if request.query_params.get('mis_reclamos') == 'true':
                    query &= Q(asignado_a=user)
            
            # Aplicar filtros adicionales
            if estado:
                query &= Q(estado=estado)
            if tipo:
                query &= Q(tipo=tipo)
            if prioridad:
                query &= Q(prioridad=prioridad)
            
            reclamos = Reclamo.objects.filter(query).select_related('cliente__user', 'asignado_a', 'pedido_relacionado').prefetch_related('comentarios').order_by('-fecha_creacion')
            
            serializer = ReclamoSerializer(reclamos, many=True)
            
            return Response({
                'success': True,
                'reclamos': serializer.data,
                'total': reclamos.count()
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al listar reclamos: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        # Crear reclamo
        try:
            cliente = user.cliente
            
            # Cualquier usuario autenticado puede crear un reclamo
            data = request.data.copy()
            data['cliente'] = cliente.id
            
            serializer = ReclamoSerializer(data=data)
            if serializer.is_valid():
                reclamo = serializer.save()
                
                # Registrar en log
                try:
                    LogSistema.objects.create(
                        nivel='INFO',
                        categoria='reclamos',
                        mensaje=f'Reclamo #{reclamo.id} creado por {user.email}',
                        usuario=user,
                        ip_address=request.META.get('REMOTE_ADDR', ''),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        modulo='views.reclamos',
                        funcion='gestionar_reclamos'
                    )
                except:
                    pass
                
                return Response({
                    'success': True,
                    'message': 'Reclamo creado exitosamente',
                    'reclamo': ReclamoSerializer(reclamo).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': 'Error de validación',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al crear reclamo: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
def gestionar_reclamo(request, reclamo_id):
    """Obtener, actualizar o eliminar un reclamo específico"""
    from .serializers import ReclamoSerializer
    
    usuario_id = request.query_params.get('usuario_id') or request.data.get('usuario_id')
    
    if not usuario_id:
        return Response({
            'success': False,
            'message': 'usuario_id es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id=usuario_id)
        reclamo = Reclamo.objects.get(id=reclamo_id)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Reclamo.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Reclamo no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Verificar permisos
    try:
        cliente = user.cliente
        rol = cliente.rol
        
        # Cliente solo puede ver/editar sus propios reclamos
        if rol == 'cliente' and reclamo.cliente != cliente:
            return Response({
                'success': False,
                'message': 'No tienes permiso para acceder a este reclamo'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Solo vendedores, gerentes y admins pueden modificar reclamos
        if request.method in ['PUT', 'DELETE'] and rol not in ['vendedor', 'gerente', 'admin_sistema']:
            return Response({
                'success': False,
                'message': 'No tienes permiso para modificar reclamos'
            }, status=status.HTTP_403_FORBIDDEN)
    except:
        if not user.is_superuser:
            return Response({
                'success': False,
                'message': 'Acceso denegado'
            }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = ReclamoSerializer(reclamo)
        return Response({
            'success': True,
            'reclamo': serializer.data
        })
    
    elif request.method == 'PUT':
        estado_anterior = reclamo.estado
        data = request.data.copy()
        
        serializer = ReclamoSerializer(reclamo, data=data, partial=True)
        if serializer.is_valid():
            reclamo = serializer.save()
            
            # Si cambió el estado, enviar notificación
            if reclamo.estado != estado_anterior:
                _enviar_notificacion_reclamo(reclamo, 'estado')
            
            # Si se marcó como resuelto, actualizar fecha_resolucion
            if reclamo.estado == 'resuelto' and not reclamo.fecha_resolucion:
                reclamo.marcar_como_resuelto(
                    resolucion_texto=data.get('resolucion', ''),
                    usuario_resolutor=user
                )
            
            return Response({
                'success': True,
                'message': 'Reclamo actualizado exitosamente',
                'reclamo': ReclamoSerializer(reclamo).data
            })
        else:
            return Response({
                'success': False,
                'message': 'Error de validación',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Solo gerentes y admins pueden eliminar
        try:
            cliente = user.cliente
            if cliente.rol not in ['gerente', 'admin_sistema']:
                return Response({
                    'success': False,
                    'message': 'Solo gerentes y administradores pueden eliminar reclamos'
                }, status=status.HTTP_403_FORBIDDEN)
        except:
            if not user.is_superuser:
                return Response({
                    'success': False,
                    'message': 'Acceso denegado'
                }, status=status.HTTP_403_FORBIDDEN)
        
        reclamo.delete()
        return Response({
            'success': True,
            'message': 'Reclamo eliminado exitosamente'
        })


@api_view(['GET', 'POST'])
def gestionar_comentarios_reclamo(request, reclamo_id):
    """Gestionar comentarios de un reclamo"""
    from .serializers import ComentarioReclamoSerializer
    
    usuario_id = request.query_params.get('usuario_id') or request.data.get('usuario_id')
    
    if not usuario_id:
        return Response({
            'success': False,
            'message': 'usuario_id es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id=usuario_id)
        reclamo = Reclamo.objects.get(id=reclamo_id)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Reclamo.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Reclamo no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Verificar permisos
    try:
        cliente = user.cliente
        rol = cliente.rol
        
        # Cliente solo puede ver comentarios públicos de sus reclamos
        if rol == 'cliente' and reclamo.cliente != cliente:
            return Response({
                'success': False,
                'message': 'No tienes permiso para acceder a este reclamo'
            }, status=status.HTTP_403_FORBIDDEN)
    except:
        if not user.is_superuser:
            return Response({
                'success': False,
                'message': 'Acceso denegado'
            }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        # Listar comentarios
        try:
            cliente = user.cliente
            rol = cliente.rol
            
            # Si es cliente, solo ver comentarios públicos
            if rol == 'cliente':
                comentarios = reclamo.comentarios.filter(es_interno=False)
            else:
                # Staff puede ver todos los comentarios
                comentarios = reclamo.comentarios.all()
            
            comentarios = comentarios.select_related('usuario').order_by('fecha_creacion')
            serializer = ComentarioReclamoSerializer(comentarios, many=True)
            
            return Response({
                'success': True,
                'comentarios': serializer.data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al listar comentarios: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'POST':
        # Crear comentario
        try:
            data = request.data.copy()
            data['reclamo'] = reclamo_id
            data['usuario'] = user.id
            
            serializer = ComentarioReclamoSerializer(data=data)
            if serializer.is_valid():
                comentario = serializer.save(usuario=user)
                
                # Enviar notificación si el comentario es público
                if not comentario.es_interno:
                    _enviar_notificacion_reclamo(reclamo, 'comentario')
                
                return Response({
                    'success': True,
                    'message': 'Comentario agregado exitosamente',
                    'comentario': ComentarioReclamoSerializer(comentario).data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': 'Error de validación',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'Error al crear comentario: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def reporte_reclamos(request):
    """Reporte de efectividad de reclamos"""
    usuario_id = request.query_params.get('usuario_id')
    
    if not usuario_id:
        return Response({
            'success': False,
            'message': 'usuario_id es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id=usuario_id)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Verificar permisos
    if not _verificar_permisos_reclamos(user):
        return Response({
            'success': False,
            'message': 'Acceso denegado. Solo vendedores, gerentes y administradores pueden ver reportes.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        from django.db.models import Avg, Count, Q
        from django.utils import timezone
        from datetime import timedelta
        
        # Filtros de fecha
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        
        query = Q()
        if fecha_inicio:
            query &= Q(fecha_creacion__gte=fecha_inicio)
        if fecha_fin:
            query &= Q(fecha_creacion__lte=fecha_fin)
        
        reclamos = Reclamo.objects.filter(query)
        
        # Estadísticas generales
        total_reclamos = reclamos.count()
        reclamos_abiertos = reclamos.filter(estado='abierto').count()
        reclamos_en_proceso = reclamos.filter(estado='en_proceso').count()
        reclamos_resueltos = reclamos.filter(estado='resuelto').count()
        reclamos_cerrados = reclamos.filter(estado='cerrado').count()
        
        # Tiempo promedio de resolución
        reclamos_resueltos_con_fecha = reclamos.filter(
            estado__in=['resuelto', 'cerrado'],
            fecha_resolucion__isnull=False
        )
        
        tiempos_resolucion = []
        for reclamo in reclamos_resueltos_con_fecha:
            tiempo = reclamo.tiempo_resolucion_horas()
            if tiempo:
                tiempos_resolucion.append(tiempo)
        
        tiempo_promedio_horas = sum(tiempos_resolucion) / len(tiempos_resolucion) if tiempos_resolucion else 0
        
        # Satisfacción promedio
        reclamos_con_satisfaccion = reclamos.filter(satisfaccion_cliente__isnull=False)
        satisfaccion_promedio = reclamos_con_satisfaccion.aggregate(
            promedio=Avg('satisfaccion_cliente')
        )['promedio'] or 0
        
        # Por tipo
        por_tipo = reclamos.values('tipo').annotate(
            total=Count('id'),
            resueltos=Count('id', filter=Q(estado__in=['resuelto', 'cerrado']))
        )
        
        # Por prioridad
        por_prioridad = reclamos.values('prioridad').annotate(
            total=Count('id'),
            resueltos=Count('id', filter=Q(estado__in=['resuelto', 'cerrado']))
        )
        
        # Reclamos por mes (últimos 6 meses)
        from django.db.models.functions import TruncMonth
        seis_meses_atras = timezone.now() - timedelta(days=180)
        reclamos_por_mes = reclamos.filter(
            fecha_creacion__gte=seis_meses_atras
        ).annotate(
            mes=TruncMonth('fecha_creacion')
        ).values('mes').annotate(
            total=Count('id')
        ).order_by('mes')
        
        return Response({
            'success': True,
            'reporte': {
                'estadisticas_generales': {
                    'total_reclamos': total_reclamos,
                    'abiertos': reclamos_abiertos,
                    'en_proceso': reclamos_en_proceso,
                    'resueltos': reclamos_resueltos,
                    'cerrados': reclamos_cerrados
                },
                'tiempo_promedio_resolucion_horas': round(tiempo_promedio_horas, 2),
                'tiempo_promedio_resolucion_dias': round(tiempo_promedio_horas / 24, 2),
                'satisfaccion_promedio': round(float(satisfaccion_promedio), 2),
                'por_tipo': list(por_tipo),
                'por_prioridad': list(por_prioridad),
                'reclamos_por_mes': list(reclamos_por_mes)
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al generar reporte: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ENDPOINTS PARA POS (HU 22) ====================

def _verificar_permisos_pos(user):
    """Verifica si el usuario tiene permisos para usar el POS"""
    try:
        cliente = user.cliente
        return cliente.rol in ['vendedor', 'gerente', 'admin_sistema']
    except:
        return user.is_superuser


@api_view(['GET'])
def pos_buscar_producto(request):
    """Búsqueda rápida de productos para POS - por nombre o SKU"""
    usuario_id = request.query_params.get('usuario_id')
    
    if not usuario_id:
        return Response({
            'success': False,
            'message': 'usuario_id es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id=usuario_id)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Verificar permisos
    if not _verificar_permisos_pos(user):
        return Response({
            'success': False,
            'message': 'Acceso denegado. Solo vendedores, gerentes y administradores pueden usar el POS.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    query = request.query_params.get('q', '').strip()
    
    if not query:
        return Response({
            'success': True,
            'productos': []
        })
    
    try:
        # Buscar por nombre o SKU
        productos = Producto.objects.filter(
            Q(nombre__icontains=query) | Q(sku__icontains=query),
            activo=True
        ).select_related('categoria')[:20]  # Limitar a 20 resultados
        
        resultados = []
        for producto in productos:
            # Aplicar promoción si existe
            precio_final = producto.precio_con_descuento()
            tiene_promocion = producto.tiene_promocion_activa()
            descuento_porcentaje = None
            if tiene_promocion:
                promocion = producto.obtener_promocion_activa()
                if promocion:
                    descuento_porcentaje = float(promocion.descuento_porcentaje)
            
            resultados.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'sku': producto.sku,
                'precio': float(producto.precio),
                'precio_con_descuento': float(precio_final),
                'stock': producto.stock,
                'categoria': producto.categoria.nombre,
                'imagen_url': producto.imagen_url or '',
                'tiene_promocion': tiene_promocion,
                'descuento_porcentaje': descuento_porcentaje
            })
        
        return Response({
            'success': True,
            'productos': resultados
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al buscar productos: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _generar_numero_boleta():
    """Genera un número de boleta correlativo único"""
    from datetime import datetime
    fecha_actual = datetime.now()
    fecha_str = fecha_actual.strftime('%Y%m%d')
    
    # Buscar el último número de boleta del día
    ultimo_pedido = Pedido.objects.filter(
        numero_pedido__startswith=f'BOL-{fecha_str}'
    ).order_by('-numero_pedido').first()
    
    if ultimo_pedido:
        # Extraer el número secuencial
        try:
            ultimo_numero = int(ultimo_pedido.numero_pedido.split('-')[-1])
            nuevo_numero = ultimo_numero + 1
        except:
            nuevo_numero = 1
    else:
        nuevo_numero = 1
    
    # Formato: BOL-YYYYMMDD-XXXX
    numero_boleta = f'BOL-{fecha_str}-{str(nuevo_numero).zfill(4)}'
    return numero_boleta


@api_view(['POST'])
def pos_crear_venta(request):
    """Crear venta rápida desde POS"""
    usuario_id = request.data.get('usuario_id')
    
    if not usuario_id:
        return Response({
            'success': False,
            'message': 'usuario_id es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id=usuario_id)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Verificar permisos
    if not _verificar_permisos_pos(user):
        return Response({
            'success': False,
            'message': 'Acceso denegado. Solo vendedores, gerentes y administradores pueden usar el POS.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        items = request.data.get('items', [])
        metodo_pago = request.data.get('metodo_pago', 'efectivo')
        cliente_id = request.data.get('cliente_id', None)  # Opcional para ventas presenciales
        
        if not items:
            return Response({
                'success': False,
                'message': 'Debe agregar al menos un producto'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener o crear cliente genérico para ventas presenciales
        if cliente_id:
            try:
                cliente = Cliente.objects.get(id=cliente_id)
            except Cliente.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Cliente no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Crear cliente genérico "Venta Presencial" si no existe
            try:
                user_generico = User.objects.get(email='venta_presencial@elixir.com')
                cliente = Cliente.objects.get(user=user_generico)
            except (User.DoesNotExist, Cliente.DoesNotExist):
                # Crear usuario asociado
                user_generico = User.objects.create_user(
                    username=f'venta_presencial_{int(timezone.now().timestamp())}',
                    email='venta_presencial@elixir.com',
                    password=secrets.token_urlsafe(32)
                )
                cliente = Cliente.objects.create(
                    user=user_generico,
                    rol='cliente'
                )
        
        # Obtener vendedor
        try:
            vendedor = Cliente.objects.get(user=user)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Usuario no es un vendedor válido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calcular totales
        from decimal import Decimal
        subtotal = Decimal('0.00')
        items_validos = []
        
        for item in items:
            try:
                producto = Producto.objects.get(id=item['producto_id'])
                
                # Verificar stock
                cantidad = int(item['cantidad'])
                if cantidad > producto.stock:
                    return Response({
                        'success': False,
                        'message': f'Stock insuficiente para {producto.nombre}. Stock disponible: {producto.stock}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Aplicar promoción si existe
                precio_final = producto.precio_con_descuento()
                subtotal_item = precio_final * Decimal(str(cantidad))
                subtotal += subtotal_item
                
                items_validos.append({
                    'producto': producto,
                    'cantidad': cantidad,
                    'precio_unitario': precio_final,
                    'subtotal': subtotal_item
                })
                
            except Producto.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Producto con ID {item.get("producto_id")} no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'Error procesando item: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generar número de boleta
        numero_boleta = _generar_numero_boleta()
        
        # Crear pedido
        pedido = Pedido.objects.create(
            cliente=cliente,
            vendedor=vendedor,
            numero_pedido=numero_boleta,
            total=float(subtotal),
            subtotal=float(subtotal),
            impuesto=0,
            descuento=0,
            estado='pagado',  # Venta presencial se marca como pagada inmediatamente
            metodo_pago=metodo_pago
        )
        
        # Crear detalles del pedido
        for item in items_validos:
            DetallesPedido.objects.create(
                pedido=pedido,
                producto=item['producto'],
                cantidad=item['cantidad'],
                precio_unitario=item['precio_unitario'],
                subtotal=item['subtotal']
            )
            
            # Reducir stock
            item['producto'].stock -= item['cantidad']
            item['producto'].save()
        
        # Registrar en log
        try:
            LogSistema.objects.create(
                nivel='INFO',
                categoria='ventas',
                mensaje=f'Venta POS creada: {numero_boleta} por {user.email}',
                usuario=user,
                ip_address=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                modulo='views.pos',
                funcion='pos_crear_venta'
            )
        except:
            pass
        
        return Response({
            'success': True,
            'message': 'Venta creada exitosamente',
            'pedido': {
                'id': pedido.id,
                'numero_boleta': numero_boleta,
                'total': float(pedido.total),
                'fecha': pedido.fecha_pedido.isoformat(),
                'metodo_pago': metodo_pago
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al crear venta: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def pos_cierre_caja(request):
    """Cierre de caja diario con resumen de ventas"""
    usuario_id = request.query_params.get('usuario_id')
    
    if not usuario_id:
        return Response({
            'success': False,
            'message': 'usuario_id es requerido'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id=usuario_id)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Verificar permisos
    if not _verificar_permisos_pos(user):
        return Response({
            'success': False,
            'message': 'Acceso denegado. Solo vendedores, gerentes y administradores pueden usar el POS.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        from django.db.models import Sum, Count, Q
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        # Filtros de fecha
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        
        if not fecha_inicio:
            fecha_inicio = timezone.now().date()
        else:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        
        if not fecha_fin:
            fecha_fin = fecha_inicio
        else:
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        
        # Obtener vendedor
        try:
            vendedor = Cliente.objects.get(user=user)
        except Cliente.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Usuario no es un vendedor válido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Filtrar ventas POS del día (boletas)
        ventas = Pedido.objects.filter(
            numero_pedido__startswith='BOL-',
            vendedor=vendedor,
            fecha_pedido__date__gte=fecha_inicio,
            fecha_pedido__date__lte=fecha_fin,
            estado='pagado'
        )
        
        # Estadísticas
        total_ventas = ventas.count()
        total_ingresos = ventas.aggregate(Sum('total'))['total__sum'] or 0
        
        # Por método de pago
        por_metodo_pago = ventas.values('metodo_pago').annotate(
            cantidad=Count('id'),
            total=Sum('total')
        )
        
        # Ventas por hora
        from django.db.models.functions import TruncHour
        ventas_por_hora = ventas.annotate(
            hora=TruncHour('fecha_pedido')
        ).values('hora').annotate(
            cantidad=Count('id'),
            total=Sum('total')
        ).order_by('hora')
        
        # Productos más vendidos
        productos_vendidos = DetallesPedido.objects.filter(
            pedido__in=ventas
        ).values(
            'producto__nombre',
            'producto__sku'
        ).annotate(
            cantidad_vendida=Sum('cantidad'),
            total_ventas=Sum('subtotal')
        ).order_by('-cantidad_vendida')[:10]
        
        # Lista de ventas del día
        ventas_lista = ventas.select_related('cliente__user').order_by('-fecha_pedido')[:50]
        ventas_detalle = []
        for venta in ventas_lista:
            ventas_detalle.append({
                'numero_boleta': venta.numero_pedido,
                'fecha': venta.fecha_pedido.isoformat(),
                'total': float(venta.total),
                'metodo_pago': venta.metodo_pago,
                'cliente': venta.cliente.user.email if venta.cliente.user else 'Venta Presencial'
            })
        
        return Response({
            'success': True,
            'cierre_caja': {
                'fecha_inicio': fecha_inicio.isoformat(),
                'fecha_fin': fecha_fin.isoformat(),
                'vendedor': user.email,
                'estadisticas': {
                    'total_ventas': total_ventas,
                    'total_ingresos': float(total_ingresos),
                    'promedio_venta': float(total_ingresos / total_ventas) if total_ventas > 0 else 0
                },
                'por_metodo_pago': list(por_metodo_pago),
                'ventas_por_hora': list(ventas_por_hora),
                'productos_mas_vendidos': list(productos_vendidos),
                'ventas_del_dia': ventas_detalle
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al generar cierre de caja: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ENDPOINTS PARA RECOMENDACIONES (HU 32) ====================

@api_view(['GET'])
def obtener_recomendaciones(request):
    """Obtener recomendaciones personalizadas para un usuario"""
    usuario_id = request.query_params.get('usuario_id')
    limite = int(request.query_params.get('limite', 12))
    producto_id = request.query_params.get('producto_id', None)  # Para productos relacionados
    tipo = request.query_params.get('tipo', 'personalizado')  # 'personalizado' o 'vendidos_semana'
    
    try:
        from django.db.models import Count, Sum, F
        from collections import Counter
        from decimal import Decimal
        from django.utils import timezone
        from datetime import timedelta
        
        recomendaciones = []
        productos_excluidos = set()
        
        # Si el tipo es "vendidos_semana", mostrar productos más vendidos (simulando esta semana)
        if tipo == 'vendidos_semana':
            # Obtener productos más vendidos por categoría (asegurar diversidad de categorías)
            categorias = Categoria.objects.filter(activa=True)
            
            productos_por_categoria = []
            for categoria in categorias:
                productos_cat = Producto.objects.filter(
                    categoria=categoria,
                    activo=True
                ).annotate(
                    total_vendido=Sum('detallespedido__cantidad'),
                    veces_vendido=Count('detallespedido__id')
                ).filter(
                    total_vendido__gt=0
                ).order_by('-total_vendido', '-veces_vendido')[:3]  # Top 3 por categoría
                
                productos_por_categoria.extend(productos_cat)
            
            # Si no hay productos vendidos, obtener productos activos de diferentes categorías
            if not productos_por_categoria:
                productos_por_categoria = Producto.objects.filter(
                    activo=True
                ).select_related('categoria').order_by('?')[:limite]  # Aleatorio para diversidad
            
            # Agregar productos de diferentes categorías
            categorias_agregadas = set()
            for producto in productos_por_categoria:
                if len(recomendaciones) >= limite:
                    break
                
                # Priorizar productos de categorías diferentes
                if producto.categoria_id not in categorias_agregadas or len(categorias_agregadas) >= 3:
                    precio_final = producto.precio_con_descuento()
                    tiene_promocion = producto.tiene_promocion_activa()
                    descuento_porcentaje = None
                    if tiene_promocion:
                        promocion = producto.obtener_promocion_activa()
                        if promocion:
                            descuento_porcentaje = float(promocion.descuento_porcentaje)
                    
                    total_vendido = getattr(producto, 'total_vendido', 0) or 0
                    # Simular cantidad vendida esta semana
                    cantidad_semana = max(1, int(total_vendido * 0.15)) if total_vendido > 0 else 1
                    
                    recomendaciones.append({
                        'producto': producto,
                        'score': 5.0 + (total_vendido * 0.01),
                        'razon': f'Vendido esta semana ({cantidad_semana} unidades)',
                        'precio_final': precio_final,
                        'tiene_promocion': tiene_promocion,
                        'descuento_porcentaje': descuento_porcentaje
                    })
                    productos_excluidos.add(producto.id)
                    categorias_agregadas.add(producto.categoria_id)
            
            # Si aún no hay suficientes, agregar productos populares de cualquier categoría
            if len(recomendaciones) < limite:
                productos_populares = Producto.objects.filter(
                    activo=True
                ).exclude(
                    id__in=productos_excluidos
                ).annotate(
                    veces_vendido=Count('detallespedido__id')
                ).order_by('-veces_vendido', '-fecha_creacion')[:limite]
                
                for producto in productos_populares:
                    if len(recomendaciones) >= limite:
                        break
                    precio_final = producto.precio_con_descuento()
                    tiene_promocion = producto.tiene_promocion_activa()
                    descuento_porcentaje = None
                    if tiene_promocion:
                        promocion = producto.obtener_promocion_activa()
                        if promocion:
                            descuento_porcentaje = float(promocion.descuento_porcentaje)
                    
                    recomendaciones.append({
                        'producto': producto,
                        'score': 4.0,
                        'razon': 'Producto popular',
                        'precio_final': precio_final,
                        'tiene_promocion': tiene_promocion,
                        'descuento_porcentaje': descuento_porcentaje
                    })
                    productos_excluidos.add(producto.id)
        
        # Si el tipo es "personalizado" y hay usuario logueado, obtener recomendaciones personalizadas
        elif tipo == 'personalizado' and usuario_id:
            try:
                user = User.objects.get(id=usuario_id)
                cliente = Cliente.objects.get(user=user)
                
                # 1. Obtener productos comprados anteriormente por el usuario
                pedidos_usuario = Pedido.objects.filter(
                    cliente=cliente,
                    estado__in=['pagado', 'entregado']
                ).select_related('cliente')
                
                productos_comprados = DetallesPedido.objects.filter(
                    pedido__in=pedidos_usuario
                ).values('producto_id').annotate(
                    veces_comprado=Count('id'),
                    total_cantidad=Sum('cantidad')
                ).order_by('-veces_comprado')[:10]
                
                productos_comprados_ids = [p['producto_id'] for p in productos_comprados]
                productos_excluidos.update(productos_comprados_ids)
                
                # 2. Obtener categorías de productos comprados
                categorias_interes = Producto.objects.filter(
                    id__in=productos_comprados_ids
                ).values_list('categoria_id', flat=True).distinct()
                
                # 3. Productos de las mismas categorías (excluyendo ya comprados)
                productos_misma_categoria = Producto.objects.filter(
                    categoria_id__in=categorias_interes,
                    activo=True
                ).exclude(
                    id__in=productos_excluidos
                ).annotate(
                    veces_vendido=Count('detallespedido__id')
                ).order_by('-veces_vendido', '-fecha_creacion')[:limite]
                
                # Agregar a recomendaciones con score
                for producto in productos_misma_categoria:
                    precio_final = producto.precio_con_descuento()
                    tiene_promocion = producto.tiene_promocion_activa()
                    descuento_porcentaje = None
                    if tiene_promocion:
                        promocion = producto.obtener_promocion_activa()
                        if promocion:
                            descuento_porcentaje = float(promocion.descuento_porcentaje)
                    
                    recomendaciones.append({
                        'producto': producto,
                        'score': 3.0,  # Score base para misma categoría
                        'razon': 'Misma categoría que productos comprados',
                        'precio_final': precio_final,
                        'tiene_promocion': tiene_promocion,
                        'descuento_porcentaje': descuento_porcentaje
                    })
                
                # 4. Productos frecuentemente comprados juntos (cross-selling)
                # Buscar pedidos que contengan productos comprados por el usuario
                pedidos_con_productos_similares = Pedido.objects.filter(
                    detallespedido__producto_id__in=productos_comprados_ids
                ).exclude(cliente=cliente).distinct()
                
                productos_juntos = DetallesPedido.objects.filter(
                    pedido__in=pedidos_con_productos_similares
                ).exclude(
                    producto_id__in=productos_excluidos
                ).values('producto_id').annotate(
                    veces_comprado_junto=Count('id')
                ).order_by('-veces_comprado_junto')[:limite]
                
                productos_juntos_ids = [p['producto_id'] for p in productos_juntos]
                productos_juntos_objs = Producto.objects.filter(
                    id__in=productos_juntos_ids,
                    activo=True
                )
                
                for producto in productos_juntos_objs:
                    # Verificar si ya está en recomendaciones
                    ya_recomendado = any(r['producto'].id == producto.id for r in recomendaciones)
                    if not ya_recomendado:
                        precio_final = producto.precio_con_descuento()
                        tiene_promocion = producto.tiene_promocion_activa()
                        descuento_porcentaje = None
                        if tiene_promocion:
                            promocion = producto.obtener_promocion_activa()
                            if promocion:
                                descuento_porcentaje = float(promocion.descuento_porcentaje)
                        
                        veces_junto = next((p['veces_comprado_junto'] for p in productos_juntos if p['producto_id'] == producto.id), 0)
                        recomendaciones.append({
                            'producto': producto,
                            'score': 4.0 + (veces_junto * 0.1),  # Mayor score si se compra frecuentemente junto
                            'razon': 'Frecuentemente comprado junto con tus productos',
                            'precio_final': precio_final,
                            'tiene_promocion': tiene_promocion,
                            'descuento_porcentaje': descuento_porcentaje
                        })
                
                # 5. Productos más vendidos de categorías de interés
                productos_populares = Producto.objects.filter(
                    categoria_id__in=categorias_interes,
                    activo=True
                ).exclude(
                    id__in=productos_excluidos
                ).annotate(
                    total_vendido=Sum('detallespedido__cantidad')
                ).filter(
                    total_vendido__gt=0
                ).order_by('-total_vendido', '-fecha_creacion')[:limite]
                
                for producto in productos_populares:
                    ya_recomendado = any(r['producto'].id == producto.id for r in recomendaciones)
                    if not ya_recomendado:
                        precio_final = producto.precio_con_descuento()
                        tiene_promocion = producto.tiene_promocion_activa()
                        descuento_porcentaje = None
                        if tiene_promocion:
                            promocion = producto.obtener_promocion_activa()
                            if promocion:
                                descuento_porcentaje = float(promocion.descuento_porcentaje)
                        
                        recomendaciones.append({
                            'producto': producto,
                            'score': 2.0,
                            'razon': 'Popular en tus categorías de interés',
                            'precio_final': precio_final,
                            'tiene_promocion': tiene_promocion,
                            'descuento_porcentaje': descuento_porcentaje
                        })
                
            except (User.DoesNotExist, Cliente.DoesNotExist):
                # Si no hay usuario, continuar con recomendaciones generales
                pass
        
        # Si no hay suficientes recomendaciones (productos vendidos esta semana + personalizadas),
        # agregar productos más vendidos en general
        if len(recomendaciones) < limite:
            # Primero intentar productos más vendidos
            productos_generales = Producto.objects.filter(
                activo=True
            ).exclude(
                id__in=productos_excluidos
            ).annotate(
                total_vendido=Sum('detallespedido__cantidad')
            ).order_by('-total_vendido', '-fecha_creacion')[:limite * 2]
            
            for producto in productos_generales:
                ya_recomendado = any(r['producto'].id == producto.id for r in recomendaciones)
                if not ya_recomendado and len(recomendaciones) < limite:
                    precio_final = producto.precio_con_descuento()
                    tiene_promocion = producto.tiene_promocion_activa()
                    descuento_porcentaje = None
                    if tiene_promocion:
                        promocion = producto.obtener_promocion_activa()
                        if promocion:
                            descuento_porcentaje = float(promocion.descuento_porcentaje)
                    
                    recomendaciones.append({
                        'producto': producto,
                        'score': 1.0,
                        'razon': 'Producto popular',
                        'precio_final': precio_final,
                        'tiene_promocion': tiene_promocion,
                        'descuento_porcentaje': descuento_porcentaje
                    })
            
            # Si aún no hay suficientes, agregar cualquier producto activo
            if len(recomendaciones) < limite:
                productos_adicionales = Producto.objects.filter(
                    activo=True
                ).exclude(
                    id__in=[r['producto'].id for r in recomendaciones]
                ).order_by('-fecha_creacion')[:limite]
                
                for producto in productos_adicionales:
                    if len(recomendaciones) >= limite:
                        break
                    precio_final = producto.precio_con_descuento()
                    tiene_promocion = producto.tiene_promocion_activa()
                    descuento_porcentaje = None
                    if tiene_promocion:
                        promocion = producto.obtener_promocion_activa()
                        if promocion:
                            descuento_porcentaje = float(promocion.descuento_porcentaje)
                    
                    recomendaciones.append({
                        'producto': producto,
                        'score': 0.5,
                        'razon': 'Nuevo producto',
                        'precio_final': precio_final,
                        'tiene_promocion': tiene_promocion,
                        'descuento_porcentaje': descuento_porcentaje
                    })
        
        # Ordenar por score y limitar
        recomendaciones.sort(key=lambda x: x['score'], reverse=True)
        recomendaciones = recomendaciones[:limite]
        
        # Serializar productos
        from .serializers import ProductoSerializer
        productos_recomendados = []
        for rec in recomendaciones:
            producto_data = ProductoSerializer(rec['producto']).data
            producto_data['razon_recomendacion'] = rec['razon']
            productos_recomendados.append(producto_data)
        
        return Response({
            'success': True,
            'recomendaciones': productos_recomendados,
            'total': len(productos_recomendados)
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al obtener recomendaciones: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def productos_relacionados(request, producto_id):
    """Obtener productos relacionados a un producto específico"""
    usuario_id = request.query_params.get('usuario_id', None)
    limite = int(request.query_params.get('limite', 6))
    
    try:
        producto = Producto.objects.get(id=producto_id, activo=True)
        
        # 1. Productos de la misma categoría
        productos_categoria = Producto.objects.filter(
            categoria=producto.categoria,
            activo=True
        ).exclude(id=producto_id).annotate(
            veces_vendido=Count('detallespedido__id')
        ).order_by('-veces_vendido', '-fecha_creacion')[:limite]
        
        # 2. Productos frecuentemente comprados juntos
        pedidos_con_producto = Pedido.objects.filter(
            detallespedido__producto=producto
        ).distinct()
        
        productos_juntos = DetallesPedido.objects.filter(
            pedido__in=pedidos_con_producto
        ).exclude(
            producto=producto
        ).values('producto_id').annotate(
            veces_comprado_junto=Count('id')
        ).order_by('-veces_comprado_junto')[:limite]
        
        productos_juntos_ids = [p['producto_id'] for p in productos_juntos]
        productos_juntos_objs = Producto.objects.filter(
            id__in=productos_juntos_ids,
            activo=True
        )
        
        # Combinar y eliminar duplicados
        productos_relacionados = list(productos_categoria)
        for pj in productos_juntos_objs:
            if pj not in productos_relacionados:
                productos_relacionados.append(pj)
        
        # Limitar
        productos_relacionados = productos_relacionados[:limite]
        
        # Serializar
        from .serializers import ProductoSerializer
        productos_data = ProductoSerializer(productos_relacionados, many=True).data
        
        return Response({
            'success': True,
            'productos': productos_data,
            'total': len(productos_data)
        })
        
    except Producto.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Producto no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al obtener productos relacionados: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== HU 35 - GESTIÓN DE DIRECCIONES DE ENVÍO ====================

# Diccionario de comunas por región (Chile)
COMUNAS_POR_REGION = {
    'Arica y Parinacota': ['Arica', 'Camarones', 'Putre', 'General Lagos'],
    'Tarapacá': ['Iquique', 'Alto Hospicio', 'Pozo Almonte', 'Camiña', 'Colchane', 'Huara', 'Pica'],
    'Antofagasta': ['Antofagasta', 'Mejillones', 'Sierra Gorda', 'Taltal', 'Calama', 'Ollagüe', 'San Pedro de Atacama', 'Tocopilla', 'María Elena'],
    'Atacama': ['Copiapó', 'Caldera', 'Tierra Amarilla', 'Chañaral', 'Diego de Almagro', 'Vallenar', 'Alto del Carmen', 'Freirina', 'Huasco'],
    'Coquimbo': ['La Serena', 'Coquimbo', 'Andacollo', 'La Higuera', 'Paiguano', 'Vicuña', 'Illapel', 'Canela', 'Los Vilos', 'Salamanca', 'Ovalle', 'Combarbalá', 'Monte Patria', 'Punitaqui', 'Río Hurtado'],
    'Valparaíso': ['Valparaíso', 'Viña del Mar', 'Concón', 'Quilpué', 'Villa Alemana', 'Limache', 'Olmué', 'La Calera', 'Hijuelas', 'La Ligua', 'Cabildo', 'Zapallar', 'Papudo', 'Petorca', 'Los Andes', 'San Esteban', 'Calle Larga', 'Rinconada', 'San Felipe', 'Llaillay', 'Putaendo', 'Santa María', 'Catemu', 'Panquehue', 'Quillota', 'La Cruz', 'La Palma', 'Nogales', 'Hijuelas', 'San Antonio', 'Cartagena', 'El Quisco', 'El Tabo', 'Algarrobo', 'Santo Domingo', 'Isla de Pascua', 'Juan Fernández', 'Casablanca', 'Concón', 'Quintero', 'Puchuncaví'],
    'Metropolitana': ['Santiago', 'Cerrillos', 'Cerro Navia', 'Conchalí', 'El Bosque', 'Estación Central', 'Huechuraba', 'Independencia', 'La Cisterna', 'La Florida', 'La Granja', 'La Pintana', 'La Reina', 'Las Condes', 'Lo Barnechea', 'Lo Espejo', 'Lo Prado', 'Macul', 'Maipú', 'Ñuñoa', 'Pedro Aguirre Cerda', 'Peñalolén', 'Providencia', 'Pudahuel', 'Quilicura', 'Quinta Normal', 'Recoleta', 'Renca', 'San Joaquín', 'San Miguel', 'San Ramón', 'Vitacura', 'Puente Alto', 'Pirque', 'San José de Maipo', 'Colina', 'Lampa', 'Tiltil', 'San Bernardo', 'Buin', 'Calera de Tango', 'Paine', 'Melipilla', 'Alhué', 'Curacaví', 'María Pinto', 'San Pedro', 'Talagante', 'El Monte', 'Isla de Maipo', 'Padre Hurtado', 'Peñaflor'],
    "O'Higgins": ['Rancagua', 'Codegua', 'Coinco', 'Coltauco', 'Doñihue', 'Graneros', 'Las Cabras', 'Machalí', 'Malloa', 'Mostazal', 'Olivar', 'Peumo', 'Pichidegua', 'Quinta de Tilcoco', 'Rengo', 'Requínoa', 'San Vicente', 'Pichilemu', 'La Estrella', 'Litueche', 'Marchihue', 'Navidad', 'Paredones', 'San Fernando', 'Chépica', 'Chimbarongo', 'Lolol', 'Nancagua', 'Palmilla', 'Peralillo', 'Placilla', 'Pumanque', 'Santa Cruz'],
    'Maule': ['Talca', 'Constitución', 'Curepto', 'Empedrado', 'Maule', 'Pelarco', 'Pencahue', 'Río Claro', 'San Clemente', 'San Rafael', 'Cauquenes', 'Chanco', 'Pelluhue', 'Curicó', 'Hualañé', 'Licantén', 'Molina', 'Rauco', 'Romeral', 'Sagrada Familia', 'Teno', 'Vichuquén', 'Linares', 'Colbún', 'Longaví', 'Parral', 'Retiro', 'San Javier', 'Villa Alegre', 'Yerbas Buenas'],
    'Ñuble': ['Chillán', 'Bulnes', 'Chillán Viejo', 'El Carmen', 'Pemuco', 'Pinto', 'Quillón', 'San Ignacio', 'Yungay', 'Quirihue', 'Cobquecura', 'Coelemu', 'Ninhue', 'Portezuelo', 'Ránquil', 'Treguaco', 'San Carlos', 'Coihueco', 'Ñiquén', 'San Fabián', 'San Nicolás'],
    'Biobío': ['Concepción', 'Coronel', 'Chiguayante', 'Florida', 'Hualqui', 'Lota', 'Penco', 'San Pedro de la Paz', 'Santa Juana', 'Talcahuano', 'Tomé', 'Hualpén', 'Lebu', 'Arauco', 'Cañete', 'Contulmo', 'Curanilahue', 'Los Álamos', 'Tirúa', 'Los Ángeles', 'Antuco', 'Cabrero', 'Laja', 'Mulchén', 'Nacimiento', 'Negrete', 'Quilaco', 'Quilleco', 'San Rosendo', 'Santa Bárbara', 'Tucapel', 'Yumbel', 'Alto Biobío'],
    'Araucanía': ['Temuco', 'Carahue', 'Cunco', 'Curarrehue', 'Freire', 'Galvarino', 'Gorbea', 'Lautaro', 'Loncoche', 'Melipeuco', 'Nueva Imperial', 'Padre Las Casas', 'Perquenco', 'Pitrufquén', 'Pucón', 'Saavedra', 'Teodoro Schmidt', 'Toltén', 'Vilcún', 'Villarrica', 'Cholchol', 'Angol', 'Collipulli', 'Curacautín', 'Ercilla', 'Lonquimay', 'Los Sauces', 'Lumaco', 'Purén', 'Renaico', 'Traiguén', 'Victoria'],
    'Los Ríos': ['Valdivia', 'Corral', 'Lanco', 'Los Lagos', 'Máfil', 'Mariquina', 'Paillaco', 'Panguipulli', 'La Unión', 'Futrono', 'Lago Ranco', 'Río Bueno'],
    'Los Lagos': ['Puerto Montt', 'Calbuco', 'Cochamó', 'Fresia', 'Frutillar', 'Llanquihue', 'Los Muermos', 'Maullín', 'Puerto Varas', 'Castro', 'Ancud', 'Chonchi', 'Curaco de Vélez', 'Dalcahue', 'Puqueldón', 'Queilén', 'Quellón', 'Quemchi', 'Quinchao', 'Osorno', 'Puerto Octay', 'Purranque', 'Puyehue', 'Río Negro', 'San Juan de la Costa', 'San Pablo', 'Chaitén', 'Futaleufú', 'Hualaihué', 'Palena'],
    'Aysén': ['Coyhaique', 'Lago Verde', 'Aysén', 'Cisnes', 'Guaitecas', 'Cochrane', "O'Higgins", 'Tortel', 'Chile Chico', 'Río Ibáñez'],
    'Magallanes': ['Punta Arenas', 'Laguna Blanca', 'Río Verde', 'San Gregorio', 'Cabo de Hornos', 'Antártica', 'Porvenir', 'Primavera', 'Timaukel', 'Natales', 'Torres del Paine'],
}

@api_view(['GET', 'POST'])
def gestionar_direcciones(request):
    """Listar y crear direcciones de envío del cliente"""
    # Obtener usuario autenticado (por sesión o usuario_id)
    usuario = None
    
    # 1) Intentar autenticación por sesión
    if request.user and request.user.is_authenticated:
        usuario = request.user
    
    # 2) Como fallback, permitir usuario_id en body/query
    if not usuario:
        usuario_id = None
        if request.method == 'GET':
            usuario_id = request.query_params.get('usuario_id') if hasattr(request, 'query_params') else request.GET.get('usuario_id')
        else:
            usuario_id = request.data.get('usuario_id') if hasattr(request, 'data') else request.POST.get('usuario_id')
        
        if usuario_id:
            try:
                usuario = User.objects.get(id=usuario_id)
            except User.DoesNotExist:
                usuario = None
    
    if not usuario:
        return Response({
            'success': False,
            'message': 'Debe estar autenticado'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        cliente = Cliente.objects.get(user=usuario)
        if cliente.rol != 'cliente':
            return Response({
                'success': False,
                'message': 'Solo los clientes pueden gestionar direcciones'
            }, status=status.HTTP_403_FORBIDDEN)
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Cliente no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        direcciones = DireccionEnvio.objects.filter(cliente=cliente).order_by('-es_principal', '-fecha_creacion')
        from .serializers import DireccionEnvioSerializer
        serializer = DireccionEnvioSerializer(direcciones, many=True)
        return Response({
            'success': True,
            'direcciones': serializer.data
        })
    
    elif request.method == 'POST':
        from .serializers import DireccionEnvioSerializer
        from .models import REGIONES_CHILE
        
        try:
            # Preparar datos excluyendo campos que no deben venir del frontend
            data = request.data.copy()
            data.pop('cliente', None)  # No permitir que el cliente se asigne desde el frontend
            data.pop('usuario_id', None)  # Ya lo tenemos en la variable cliente
            
            serializer = DireccionEnvioSerializer(data=data)
            if serializer.is_valid():
                # Validar región y comuna
                region = serializer.validated_data.get('region')
                comuna = serializer.validated_data.get('comuna')
                
                if region not in dict(REGIONES_CHILE):
                    return Response({
                        'success': False,
                        'message': f'Región inválida. Regiones válidas: {", ".join([r[0] for r in REGIONES_CHILE])}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if region in COMUNAS_POR_REGION:
                    comunas_validas = COMUNAS_POR_REGION[region]
                    if comuna not in comunas_validas:
                        return Response({
                            'success': False,
                            'message': f'Comuna inválida para la región {region}. Comunas válidas: {", ".join(comunas_validas)}'
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                serializer.save(cliente=cliente)
                return Response({
                    'success': True,
                    'message': 'Dirección creada exitosamente',
                    'direccion': serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': 'Error al crear dirección',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error al crear dirección: {str(e)}")
            print(f"Traceback: {error_trace}")
            return Response({
                'success': False,
                'message': f'Error al crear dirección: {str(e)}',
                'error_detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
def gestionar_direccion(request, direccion_id):
    """Obtener, actualizar o eliminar una dirección específica"""
    # Obtener usuario autenticado (por sesión o usuario_id)
    usuario = None
    
    # 1) Intentar autenticación por sesión
    if request.user and request.user.is_authenticated:
        usuario = request.user
    
    # 2) Como fallback, permitir usuario_id en body/query
    if not usuario:
        usuario_id = None
        if request.method == 'GET':
            usuario_id = request.query_params.get('usuario_id') if hasattr(request, 'query_params') else request.GET.get('usuario_id')
        else:
            usuario_id = request.data.get('usuario_id') if hasattr(request, 'data') else request.POST.get('usuario_id')
        
        if usuario_id:
            try:
                usuario = User.objects.get(id=usuario_id)
            except User.DoesNotExist:
                usuario = None
    
    if not usuario:
        return Response({
            'success': False,
            'message': 'Debe estar autenticado'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        cliente = Cliente.objects.get(user=usuario)
        direccion = DireccionEnvio.objects.get(id=direccion_id, cliente=cliente)
    except Cliente.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Cliente no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except DireccionEnvio.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Dirección no encontrada'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        from .serializers import DireccionEnvioSerializer
        serializer = DireccionEnvioSerializer(direccion)
        return Response({
            'success': True,
            'direccion': serializer.data
        })
    
    elif request.method == 'PUT':
        from .serializers import DireccionEnvioSerializer
        serializer = DireccionEnvioSerializer(direccion, data=request.data, partial=True)
        if serializer.is_valid():
            # Validar región y comuna si se actualizan
            region = serializer.validated_data.get('region', direccion.region)
            comuna = serializer.validated_data.get('comuna', direccion.comuna)
            
            from .models import REGIONES_CHILE
            if region not in dict(REGIONES_CHILE):
                return Response({
                    'success': False,
                    'message': f'Región inválida'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if region in COMUNAS_POR_REGION:
                comunas_validas = COMUNAS_POR_REGION[region]
                if comuna not in comunas_validas:
                    return Response({
                        'success': False,
                        'message': f'Comuna inválida para la región {region}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return Response({
                'success': True,
                'message': 'Dirección actualizada exitosamente',
                'direccion': serializer.data
            })
        return Response({
            'success': False,
            'message': 'Error al actualizar dirección',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        direccion.delete()
        return Response({
            'success': True,
            'message': 'Dirección eliminada exitosamente'
        })


@api_view(['GET'])
def obtener_regiones_comunas(request):
    """Obtener lista de regiones y comunas de Chile"""
    try:
        from .models import REGIONES_CHILE
        # COMUNAS_POR_REGION está definido en este mismo archivo (views.py)
        regiones_list = [{'codigo': r[0], 'nombre': r[1]} for r in REGIONES_CHILE]
        print(f"DEBUG: Enviando {len(regiones_list)} regiones")
        return Response({
            'success': True,
            'regiones': regiones_list,
            'comunas_por_region': COMUNAS_POR_REGION
        })
    except Exception as e:
        import traceback
        print(f"Error en obtener_regiones_comunas: {str(e)}")
        print(traceback.format_exc())
        return Response({
            'success': False,
            'message': f'Error al obtener regiones: {str(e)}',
            'regiones': [],
            'comunas_por_region': {}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def calcular_costo_envio(request):
    """Calcular el costo de envío según región y método"""
    try:
        from .models import METODOS_ENVIO, COSTOS_ENVIO_BASE
        region = request.data.get('region')
        metodo_envio = request.data.get('metodo_envio', 'estandar')
        monto_compra = float(request.data.get('monto_compra', 0))
        
        if not region:
            return Response({
                'success': False,
                'message': 'Región es requerida'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar método de envío
        if metodo_envio not in dict(METODOS_ENVIO):
            return Response({
                'success': False,
                'message': 'Método de envío inválido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Retiro en tienda es gratis
        if metodo_envio == 'retiro_tienda':
            return Response({
                'success': True,
                'costo_envio': 0,
                'metodo_envio': metodo_envio,
                'metodo_envio_display': dict(METODOS_ENVIO)[metodo_envio],
                'tiempo_estimado': 'Inmediato',
                'mensaje': 'Retiro disponible en tienda física'
            })
        
        # Obtener costo base según región
        costo_base = COSTOS_ENVIO_BASE.get(region, {}).get(metodo_envio)
        
        if costo_base is None:
            # Si no hay costo definido para la región, usar promedio
            costos_regiones = [costos.get(metodo_envio, 0) for costos in COSTOS_ENVIO_BASE.values()]
            costo_base = sum(costos_regiones) / len(costos_regiones) if costos_regiones else 5000
        
        # Descuento por compras mayores a $50,000 (10% descuento en envío)
        descuento = 0
        if monto_compra >= 50000:
            descuento = costo_base * 0.1
        # Descuento por compras mayores a $100,000 (envío gratis estándar)
        elif monto_compra >= 100000 and metodo_envio == 'estandar':
            costo_base = 0
        
        costo_final = max(0, costo_base - descuento)
        
        # Tiempo estimado según método
        tiempos_estimados = {
            'estandar': '3-5 días hábiles',
            'express': '1-2 días hábiles'
        }
        
        return Response({
            'success': True,
            'costo_envio': costo_final,
            'costo_base': costo_base,
            'descuento': descuento,
            'metodo_envio': metodo_envio,
            'metodo_envio_display': dict(METODOS_ENVIO)[metodo_envio],
            'tiempo_estimado': tiempos_estimados.get(metodo_envio, '3-5 días'),
            'region': region
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al calcular costo de envío: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def obtener_metodos_envio(request):
    """Obtener lista de métodos de envío disponibles"""
    from .models import METODOS_ENVIO
    return Response({
        'success': True,
        'metodos': [{'codigo': m[0], 'nombre': m[1]} for m in METODOS_ENVIO]
    })
