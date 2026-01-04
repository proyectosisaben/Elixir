from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import json
import hashlib

# Definición de roles
ROLES = (
    ('cliente', 'Cliente'),
    ('vendedor', 'Vendedor'),
    ('gerente', 'Gerente'),
    ('admin_sistema', 'Administrador Sistema'),
)

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='categorias/', blank=True, null=True)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

class Proveedor(models.Model):
    nombre = models.CharField(max_length=200)
    rut = models.CharField(max_length=12, unique=True)
    email = models.EmailField()
    telefono = models.CharField(max_length=15)
    direccion = models.TextField()
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=5)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    imagen_url = models.URLField(blank=True, null=True, help_text="URL de imagen externa (Imgur, Cloudinary, etc.)")
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos_creados')

    def __str__(self):
        return self.nombre

    @property
    def margen_ganancia(self):
        if self.costo > 0:
            return round(((self.precio - self.costo) / self.costo) * 100, 2)
        return 0

    @property
    def stock_bajo(self):
        return self.stock <= self.stock_minimo
    
    def tiene_promocion_activa(self):
        """Verifica si el producto tiene una promoción activa"""
        ahora = timezone.now()
        return self.promociones.filter(
            activa=True,
            fecha_inicio__lte=ahora,
            fecha_fin__gte=ahora
        ).exists()
    
    def obtener_promocion_activa(self):
        """Obtiene la promoción activa del producto si existe"""
        ahora = timezone.now()
        return self.promociones.filter(
            activa=True,
            fecha_inicio__lte=ahora,
            fecha_fin__gte=ahora
        ).first()
    
    def precio_con_descuento(self):
        """Retorna el precio con descuento si hay promoción activa, sino el precio normal"""
        promocion = self.obtener_promocion_activa()
        if promocion:
            return promocion.calcular_precio_con_descuento()
        return self.precio

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

class ProductoImagen(models.Model):
    producto = models.ForeignKey('Producto', related_name='imagenes', on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='productos/')
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['orden']

class Cliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    email_confirmado = models.BooleanField(default=False)
    rol = models.CharField(max_length=20, choices=ROLES, default='cliente')

    def __str__(self):
        return f"{self.user.email} ({self.get_rol_display()})"

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

# Regiones y comunas de Chile
REGIONES_CHILE = (
    ('Arica y Parinacota', 'Arica y Parinacota'),
    ('Tarapacá', 'Tarapacá'),
    ('Antofagasta', 'Antofagasta'),
    ('Atacama', 'Atacama'),
    ('Coquimbo', 'Coquimbo'),
    ('Valparaíso', 'Valparaíso'),
    ('Metropolitana', 'Región Metropolitana de Santiago'),
    ("O'Higgins", "O'Higgins"),
    ('Maule', 'Maule'),
    ('Ñuble', 'Ñuble'),
    ('Biobío', 'Biobío'),
    ('Araucanía', 'Araucanía'),
    ('Los Ríos', 'Los Ríos'),
    ('Los Lagos', 'Los Lagos'),
    ('Aysén', 'Aysén'),
    ('Magallanes', 'Magallanes y la Antártica Chilena'),
)

class DireccionEnvio(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='direcciones')
    nombre = models.CharField(max_length=100, help_text="Nombre descriptivo de la dirección (ej: Casa, Trabajo)")
    calle = models.CharField(max_length=200)
    numero = models.CharField(max_length=20)
    comuna = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    region = models.CharField(max_length=50, choices=REGIONES_CHILE)
    codigo_postal = models.CharField(max_length=10, blank=True, null=True)
    telefono = models.CharField(max_length=15)
    es_principal = models.BooleanField(default=False, help_text="Dirección principal del cliente")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} - {self.cliente.user.email}"

    def save(self, *args, **kwargs):
        # Si se marca como principal, desmarcar las demás direcciones del cliente
        if self.es_principal:
            DireccionEnvio.objects.filter(cliente=self.cliente, es_principal=True).exclude(pk=self.pk).update(es_principal=False)
        # Si es la primera dirección del cliente, marcarla como principal
        elif not DireccionEnvio.objects.filter(cliente=self.cliente, es_principal=True).exists():
            self.es_principal = True
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Dirección de Envío"
        verbose_name_plural = "Direcciones de Envío"
        ordering = ['-es_principal', '-fecha_creacion']

# Definición de estados de pedido
ESTADOS_PEDIDO = (
    ('pendiente', 'Pendiente de pago'),
    ('pagado', 'Pagado'),
    ('en_preparacion', 'En preparación'),
    ('enviado', 'Enviado'),
    ('entregado', 'Entregado'),
    ('cancelado', 'Cancelado'),
)

# Definición de métodos de pago
METODOS_PAGO = (
    ('transferencia', 'Transferencia bancaria'),
    ('tarjeta', 'Tarjeta de crédito'),
    ('efectivo', 'Efectivo'),
)

# Definición de métodos de envío
METODOS_ENVIO = (
    ('estandar', 'Envío Estándar (3-5 días)'),
    ('express', 'Envío Express (1-2 días)'),
    ('retiro_tienda', 'Retiro en Tienda (Gratis)'),
)

# Costos base de envío por región (en CLP)
COSTOS_ENVIO_BASE = {
    'Arica y Parinacota': {'estandar': 8000, 'express': 12000},
    'Tarapacá': {'estandar': 7500, 'express': 11000},
    'Antofagasta': {'estandar': 7000, 'express': 10000},
    'Atacama': {'estandar': 6500, 'express': 9500},
    'Coquimbo': {'estandar': 6000, 'express': 9000},
    'Valparaíso': {'estandar': 5000, 'express': 7500},
    'Metropolitana': {'estandar': 3000, 'express': 5000},
    "O'Higgins": {'estandar': 5500, 'express': 8000},
    'Maule': {'estandar': 6000, 'express': 8500},
    'Ñuble': {'estandar': 6500, 'express': 9000},
    'Biobío': {'estandar': 7000, 'express': 10000},
    'Araucanía': {'estandar': 7500, 'express': 11000},
    'Los Ríos': {'estandar': 8000, 'express': 12000},
    'Los Lagos': {'estandar': 8500, 'express': 13000},
    'Aysén': {'estandar': 12000, 'express': 18000},
    'Magallanes': {'estandar': 15000, 'express': 22000},
}

class Pedido(models.Model):
    # Modelo que coincide con la estructura REAL de inventario_pedido en Railway
    numero_pedido = models.CharField(max_length=50, unique=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    impuesto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=[
        ('pendiente', 'Pendiente de pago'),
        ('pagado', 'Pagado'),
        ('en_preparacion', 'En preparación'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ], default='pendiente')
    metodo_pago = models.CharField(max_length=20, choices=[
        ('transferencia', 'Transferencia bancaria'),
        ('tarjeta', 'Tarjeta de crédito'),
        ('efectivo', 'Efectivo'),
    ], default='transferencia')
    notas = models.TextField(blank=True, null=True)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    fecha_entrega_estimada = models.DateField(blank=True, null=True)
    fecha_entrega_real = models.DateField(blank=True, null=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pedidos')
    vendedor = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos_vendedor', limit_choices_to={'rol': 'vendedor'})
    direccion_envio = models.ForeignKey(DireccionEnvio, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos')
    metodo_envio = models.CharField(max_length=20, choices=METODOS_ENVIO, blank=True, null=True)
    costo_envio = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Pedido {self.numero_pedido} - {self.cliente.user.email}"

    def marcar_como_pagado(self):
        self.estado = 'pagado'
        self.save()

    def marcar_como_enviado(self):
        self.estado = 'enviado'
        self.save()

    def marcar_como_entregado(self):
        self.estado = 'entregado'
        self.fecha_entrega_real = models.functions.Now()
        self.save()

    class Meta:
        ordering = ['-fecha_pedido']
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"

    def marcar_como_pagado(self):
        self.estado = 'pagado'
        self.save()

    def marcar_como_enviado(self):
        self.estado = 'enviado'
        self.save()

    def marcar_como_entregado(self):
        self.estado = 'entregado'
        self.fecha_entrega_real = models.functions.Now()
        self.save()

    class Meta:
        ordering = ['-fecha_pedido']
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"

class DetallesPedido(models.Model):
    # Modelo que coincide con la tabla inventario_detallespedido existente en Railway
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.producto.nombre} en {self.pedido.numero_pedido}"

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Detalle de Pedido"
        verbose_name_plural = "Detalles de Pedidos"

# Modelo para Auditoría del Sistema (HU 20)
class AuditLog(models.Model):
    ACCIONES = (
        ('crear', 'Crear'),
        ('modificar', 'Modificar'),
        ('eliminar', 'Eliminar'),
        ('login', 'Inicio de Sesión'),
        ('logout', 'Cierre de Sesión'),
        ('APROBACION_SOLICITUD', 'Aprobación de Solicitud'),
        ('RECHAZO_SOLICITUD', 'Rechazo de Solicitud'),
        ('CREACION_SOLICITUD', 'Creación de Solicitud'),
        ('ACTUALIZACION_STOCK_AUTOMATICA', 'Actualización Automática de Stock'),
    )

    MODELOS = (
        ('Producto', 'Producto'),
        ('Categoria', 'Categoría'),
        ('Cliente', 'Cliente'),
        ('Pedido', 'Pedido'),
        ('AuditLog', 'Log de Auditoría'),
        ('SolicitudAutorizacion', 'Solicitud de Autorización'),
    )

    fecha = models.DateTimeField(auto_now_add=True, db_index=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    tipo_accion = models.CharField(max_length=50, choices=ACCIONES, db_index=True)
    modelo = models.CharField(max_length=50, choices=MODELOS, db_index=True)
    id_objeto = models.CharField(max_length=255, db_index=True)
    datos_anteriores = models.JSONField(default=dict, blank=True, null=True)
    datos_nuevos = models.JSONField(default=dict, blank=True, null=True)
    descripcion = models.TextField()
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    hash_integridad = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return f"[{self.get_tipo_accion_display()}] {self.fecha.strftime('%Y-%m-%d %H:%M:%S')} - {self.usuario.username if self.usuario else 'Sistema'} - {self.descripcion[:50]}"

    def generar_hash_integridad(self):
        # Asegurarse de que self.fecha no sea None antes de llamar a isoformat()
        fecha_str = self.fecha.isoformat() if self.fecha else ""
        contenido = f"{self.usuario_id}|{fecha_str}|{self.tipo_accion}|{self.modelo}|{self.id_objeto}|{json.dumps(self.datos_anteriores, sort_keys=True)}|{json.dumps(self.datos_nuevos, sort_keys=True)}"
        return hashlib.sha256(contenido.encode('utf-8')).hexdigest()

    def save(self, *args, **kwargs):
        if not self.hash_integridad:
            self.hash_integridad = self.generar_hash_integridad()
        super().save(*args, **kwargs)

    @staticmethod
    def registrar_cambio(usuario=None, tipo_accion='', modelo='', id_objeto='', datos_anteriores=None, datos_nuevos=None, descripcion='', ip_address='', user_agent=''):
        """
        Método estático para registrar un cambio en el sistema de auditoría
        """
        try:
            if datos_anteriores is None:
                datos_anteriores = {}
            if datos_nuevos is None:
                datos_nuevos = {}

            log = AuditLog.objects.create(
                usuario=usuario,
                tipo_accion=tipo_accion,
                modelo=modelo,
                id_objeto=str(id_objeto),
                datos_anteriores=datos_anteriores,
                datos_nuevos=datos_nuevos,
                descripcion=descripcion,
                ip_address=ip_address,
                user_agent=user_agent
            )
            return log
        except Exception as e:
            print(f"Error registrando auditoría: {e}")
            return None

    class Meta:
        verbose_name = "Log de Auditoría"
        verbose_name_plural = "Logs de Auditoría"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['tipo_accion']),
            models.Index(fields=['modelo']),
            models.Index(fields=['usuario']),
        ]

# Modelo para Solicitudes de Autorización (HU 50)
class SolicitudAutorizacion(models.Model):
    ESTADO_SOLICITUD = (
        ('pendiente', 'Pendiente'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('cancelada', 'Cancelada'),
    )

    TIPO_SOLICITUD = (
        ('cambio_stock', 'Cambio de Stock'),
        ('nuevo_producto', 'Nuevo Producto'),
        ('modificar_precio', 'Modificar Precio'),
        ('eliminar_producto', 'Eliminar Producto'),
    )

    PRIORIDAD_SOLICITUD = (
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    )

    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solicitudes_enviadas')
    aprobador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes_aprobadas')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_SOLICITUD, default='pendiente', db_index=True)
    tipo_solicitud = models.CharField(max_length=50, choices=TIPO_SOLICITUD, db_index=True)
    modelo_afectado = models.CharField(max_length=100)  # Ej: 'Producto', 'Categoria'
    id_objeto_afectado = models.CharField(max_length=255, null=True, blank=True)  # ID del objeto afectado
    producto_afectado = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True, related_name='solicitudes')
    datos_anteriores = models.JSONField(default=dict, blank=True, null=True)
    datos_nuevos = models.JSONField(default=dict, blank=True, null=True)
    motivo = models.TextField()
    comentario_respuesta = models.TextField(blank=True, null=True)
    comentario_revision = models.TextField(blank=True, null=True)  # Campo adicional que existe en BD
    prioridad = models.CharField(max_length=20, choices=PRIORIDAD_SOLICITUD, default='media')
    ip_solicitante = models.CharField(max_length=45, blank=True, null=True)
    user_agent_solicitante = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Solicitud {self.id} - {self.get_tipo_solicitud_display()} por {self.solicitante.username} ({self.get_estado_display()})"

    def aprobar(self, aprobador_usuario, comentario=""):
        if self.estado == 'pendiente':
            self.estado = 'aprobada'
            # self.aprobador = aprobador_usuario  # Deshabilitado por problema de migración
            self.fecha_respuesta = timezone.now()
            self.comentario_respuesta = comentario
            self.save()
            # self._aplicar_cambios()  # Deshabilitado temporalmente
            AuditLog.registrar_cambio(
                usuario=aprobador_usuario,
                tipo_accion='APROBACION_SOLICITUD',
                modelo='SolicitudAutorizacion',
                id_objeto=self.id,
                datos_anteriores={'estado': 'pendiente'},
                datos_nuevos={'estado': 'aprobada', 'comentario': comentario},
                descripcion=f"Solicitud {self.id} ({self.get_tipo_solicitud_display()}) aprobada por {aprobador_usuario.username}"
            )
        else:
            raise ValueError("Solo solicitudes pendientes pueden ser aprobadas.")

    def rechazar(self, aprobador_usuario, comentario=""):
        if self.estado == 'pendiente':
            self.estado = 'rechazada'
            # self.aprobador = aprobador_usuario  # Deshabilitado por problema de migración
            self.fecha_respuesta = timezone.now()
            self.comentario_respuesta = comentario
            self.save()
            AuditLog.registrar_cambio(
                usuario=aprobador_usuario,
                tipo_accion='RECHAZO_SOLICITUD',
                modelo='SolicitudAutorizacion',
                id_objeto=self.id,
                datos_anteriores={'estado': 'pendiente'},
                datos_nuevos={'estado': 'rechazada', 'comentario': comentario},
                descripcion=f"Solicitud {self.id} ({self.get_tipo_solicitud_display()}) rechazada por {aprobador_usuario.username}"
            )
        else:
            raise ValueError("Solo solicitudes pendientes pueden ser rechazadas.")

    def _aplicar_cambios(self):
        if self.tipo_solicitud == 'cambio_stock' and self.producto_afectado:
            producto = self.producto_afectado
            nuevo_stock = self.datos_nuevos.get('stock')
            if nuevo_stock is not None:
                old_stock = producto.stock
                producto.stock = nuevo_stock
                producto.save()
                AuditLog.registrar_cambio(
                    usuario=self.aprobador,
                    tipo_accion='ACTUALIZACION_STOCK_AUTOMATICA',
                    modelo='Producto',
                    id_objeto=producto.id,
                    datos_anteriores={'stock': old_stock},
                    datos_nuevos={'stock': nuevo_stock},
                    descripcion=f"Stock de {producto.nombre} actualizado automáticamente por aprobación de solicitud {self.id}"
                )

    @staticmethod
    def crear_solicitud(solicitante, tipo_solicitud, modelo_afectado, id_objeto_afectado,
                       datos_anteriores, datos_nuevos, motivo, prioridad='media',
                       ip_address="", user_agent=""):
        """
        Método estático para crear una nueva solicitud de autorización.
        """
        # Validar que el solicitante tenga permisos
        try:
            if solicitante.cliente.rol not in ['vendedor', 'gerente', 'admin_sistema']:
                raise ValueError("Solo vendedores, gerentes y administradores pueden crear solicitudes")
        except Cliente.DoesNotExist:
            raise ValueError("El usuario no tiene un cliente asociado")

        # Crear solicitud sin el campo aprobador por problema de migración
        solicitud = SolicitudAutorizacion.objects.create(
            solicitante=solicitante,
            tipo_solicitud=tipo_solicitud,
            modelo_afectado=modelo_afectado,
            id_objeto_afectado=str(id_objeto_afectado),
            datos_anteriores=datos_anteriores,
            datos_nuevos=datos_nuevos,
            motivo=motivo,
            prioridad=prioridad,
            ip_solicitante=ip_address,
            user_agent_solicitante=user_agent,
            comentario_revision='',  # Valor por defecto
            # aprobador=None  # Deshabilitado por problema de migración
        )

        # Intentar asociar producto si es una solicitud de producto
        if modelo_afectado == 'Producto':
            try:
                solicitud.producto_afectado = Producto.objects.get(id=id_objeto_afectado)
                solicitud.save()
            except Producto.DoesNotExist:
                pass  # El producto podría no existir aún si es una solicitud de "nuevo_producto"

        # Registrar en AuditLog
        AuditLog.registrar_cambio(
            usuario=solicitante,
            tipo_accion='CREACION_SOLICITUD',
            modelo='SolicitudAutorizacion',
            id_objeto=solicitud.id,
            datos_anteriores={},
            datos_nuevos={'tipo_solicitud': tipo_solicitud, 'modelo_afectado': modelo_afectado, 'id_objeto_afectado': id_objeto_afectado, 'motivo': motivo},
            descripcion=f"Solicitud de {tipo_solicitud} creada por {solicitante.username}"
        )

        return solicitud

    class Meta:
        verbose_name = "Solicitud de Autorización"
        verbose_name_plural = "Solicitudes de Autorización"
        ordering = ['-fecha_solicitud']
        indexes = [
            models.Index(fields=['estado', '-fecha_solicitud']),
            models.Index(fields=['solicitante', '-fecha_solicitud']),
            models.Index(fields=['tipo_solicitud', 'estado']),
        ]


class LogSistema(models.Model):
    """
    Modelo para registrar logs del sistema - HU 40
    """
    NIVEL_CHOICES = (
        ('info', 'Información'),
        ('warning', 'Advertencia'),
        ('error', 'Error'),
        ('critical', 'Crítico'),
    )

    CATEGORIA_CHOICES = (
        ('sistema', 'Sistema'),
        ('seguridad', 'Seguridad'),
        ('usuario', 'Usuario'),
        ('venta', 'Venta'),
        ('inventario', 'Inventario'),
        ('api', 'API'),
        ('base_datos', 'Base de Datos'),
    )

    nivel = models.CharField(max_length=20, choices=NIVEL_CHOICES, default='info')
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='sistema')
    mensaje = models.TextField()
    datos_extra = models.JSONField(default=dict, blank=True, null=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs_sistema')
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    modulo = models.CharField(max_length=100, blank=True, null=True)  # Ej: 'views.login', 'models.producto'
    funcion = models.CharField(max_length=100, blank=True, null=True)  # Ej: 'login_cliente', 'save'

    def __str__(self):
        return f"[{self.get_nivel_display()}] {self.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S')} - {self.mensaje[:50]}"

    @staticmethod
    def registrar_evento(nivel, categoria, mensaje, usuario=None, datos_extra=None, ip_address='', user_agent='', modulo='', funcion=''):
        """
        Método estático para registrar un evento en el sistema de logs
        """
        try:
            if datos_extra is None:
                datos_extra = {}

            LogSistema.objects.create(
                nivel=nivel,
                categoria=categoria,
                mensaje=mensaje,
                datos_extra=datos_extra,
                usuario=usuario,
                ip_address=ip_address,
                user_agent=user_agent,
                modulo=modulo,
                funcion=funcion
            )
        except Exception as e:
            # Si falla el registro del log, al menos imprimir en consola
            print(f"ERROR registrando log del sistema: {e}")

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = "Log del Sistema"
        verbose_name_plural = "Logs del Sistema"
        indexes = [
            models.Index(fields=['nivel', 'categoria']),
            models.Index(fields=['fecha_creacion']),
            models.Index(fields=['usuario']),
        ]


class EstadisticaVisita(models.Model):
    """
    Modelo para tracking de visitas a productos - HU 40
    """
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='estadisticas_visita')
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='visitas_productos')
    fecha_visita = models.DateTimeField(auto_now_add=True)
    tiempo_visualizacion = models.PositiveIntegerField(default=0, help_text="Tiempo en segundos que el usuario vio el producto")
    fuente = models.CharField(max_length=50, default='catalogo', help_text="Origen de la visita (catalogo, busqueda, recomendado, etc.)")
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"{self.producto.nombre} - {self.fecha_visita.strftime('%Y-%m-%d %H:%M')} - {self.usuario.username if self.usuario else 'Anónimo'}"

    class Meta:
        ordering = ['-fecha_visita']
        verbose_name = "Estadística de Visita"
        verbose_name_plural = "Estadísticas de Visitas"
        indexes = [
            models.Index(fields=['producto', 'fecha_visita']),
            models.Index(fields=['usuario', 'fecha_visita']),
            models.Index(fields=['fecha_visita']),
        ]

# Modelo para Reportes Financieros (HU 7)
class ReporteFinanciero(models.Model):
    TIPO_REPORTE = (
        ('ventas_general', 'Ventas Generales'),
        ('productos_top', 'Productos Más Vendidos'),
        ('ingresos_categoria', 'Ingresos por Categoría'),
        ('comparativa_periodos', 'Comparativa entre Períodos'),
        ('resumen_completo', 'Resumen Completo'),
    )
    
    FRECUENCIA = (
        ('unico', 'Único'),
        ('diario', 'Diario'),
        ('semanal', 'Semanal'),
        ('mensual', 'Mensual'),
    )

    generador = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reportes_generados', help_text="Usuario que generó el reporte")
    tipo_reporte = models.CharField(max_length=20, choices=TIPO_REPORTE, default='resumen_completo')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, help_text="Categoría opcional para filtrar")
    
    # Metadata del reporte
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    titulo = models.CharField(max_length=200, blank=True)
    descripcion = models.TextField(blank=True)
    
    # Archivo PDF
    archivo_pdf = models.FileField(upload_to='reportes/', blank=True, null=True)
    
    # Datos del reporte (JSON para almacenar resultados)
    datos_json = models.JSONField(default=dict, blank=True)
    
    # Control
    estado = models.CharField(max_length=20, default='completado', choices=[
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('completado', 'Completado'),
        ('error', 'Error'),
    ])
    
    enviado_por_email = models.BooleanField(default=False)
    emails_destino = models.TextField(blank=True, help_text="Emails separados por comas")
    fecha_envio = models.DateTimeField(null=True, blank=True)
    
    # Programación automática
    frecuencia_automatica = models.CharField(max_length=20, choices=FRECUENCIA, default='unico')
    activo = models.BooleanField(default=False, help_text="¿Generar automáticamente?")
    
    def __str__(self):
        return f"{self.get_tipo_reporte_display()} - {self.fecha_creacion.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = "Reporte Financiero"
        verbose_name_plural = "Reportes Financieros"
        permissions = [
            ("puede_generar_reportes", "Puede generar reportes"),
            ("puede_ver_reportes", "Puede ver reportes"),
        ]


# Modelos para Promociones y Descuentos (HU 11)
class Cupon(models.Model):
    TIPO_DESCUENTO = (
        ('porcentaje', 'Porcentaje'),
        ('monto', 'Monto Fijo'),
    )
    
    codigo = models.CharField(max_length=50, unique=True, help_text="Código único del cupón")
    tipo_descuento = models.CharField(max_length=20, choices=TIPO_DESCUENTO, default='porcentaje')
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Descuento en porcentaje (0-100)")
    descuento_monto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Descuento en monto fijo")
    fecha_inicio = models.DateTimeField(help_text="Fecha y hora de inicio de vigencia")
    fecha_fin = models.DateTimeField(help_text="Fecha y hora de fin de vigencia")
    usos_maximos = models.PositiveIntegerField(default=1, help_text="Número máximo de veces que se puede usar")
    usos_actuales = models.PositiveIntegerField(default=0, help_text="Número de veces que se ha usado")
    activo = models.BooleanField(default=True, help_text="Si el cupón está activo")
    descripcion = models.TextField(blank=True, help_text="Descripción del cupón")
    monto_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Monto mínimo de compra para aplicar el cupón")
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cupones_creados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.get_tipo_descuento_display()}"
    
    def es_valido(self):
        """Verifica si el cupón es válido para usar"""
        ahora = timezone.now()
        return (
            self.activo and
            self.fecha_inicio <= ahora <= self.fecha_fin and
            self.usos_actuales < self.usos_maximos
        )
    
    def calcular_descuento(self, monto_total):
        """Calcula el descuento a aplicar sobre un monto"""
        from decimal import Decimal
        
        # Convertir monto_total a Decimal para operaciones consistentes
        monto_total_decimal = Decimal(str(monto_total))
        monto_minimo_decimal = self.monto_minimo
        
        if not self.es_valido() or monto_total_decimal < monto_minimo_decimal:
            return Decimal('0')
        
        if self.tipo_descuento == 'porcentaje' and self.descuento_porcentaje:
            descuento = (monto_total_decimal * self.descuento_porcentaje) / Decimal('100')
            return min(descuento, monto_total_decimal)  # No puede ser mayor al monto total
        elif self.tipo_descuento == 'monto' and self.descuento_monto:
            return min(self.descuento_monto, monto_total_decimal)  # No puede ser mayor al monto total
        
        return Decimal('0')
    
    def usar(self):
        """Incrementa el contador de usos"""
        if self.usos_actuales < self.usos_maximos:
            self.usos_actuales += 1
            self.save()
            return True
        return False
    
    class Meta:
        verbose_name = "Cupón"
        verbose_name_plural = "Cupones"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['codigo']),
            models.Index(fields=['activo', 'fecha_inicio', 'fecha_fin']),
        ]


class PromocionProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='promociones')
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, help_text="Descuento en porcentaje (0-100)")
    fecha_inicio = models.DateTimeField(help_text="Fecha y hora de inicio de la promoción")
    fecha_fin = models.DateTimeField(help_text="Fecha y hora de fin de la promoción")
    activa = models.BooleanField(default=True, help_text="Si la promoción está activa")
    descripcion = models.TextField(blank=True, help_text="Descripción de la promoción")
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='promociones_creadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.descuento_porcentaje}% OFF"
    
    def esta_vigente(self):
        """Verifica si la promoción está vigente"""
        ahora = timezone.now()
        return self.activa and self.fecha_inicio <= ahora <= self.fecha_fin
    
    def calcular_precio_con_descuento(self):
        """Calcula el precio del producto con el descuento aplicado"""
        from decimal import Decimal
        
        if not self.esta_vigente():
            return self.producto.precio
        
        descuento = (self.producto.precio * self.descuento_porcentaje) / Decimal('100')
        precio_final = self.producto.precio - descuento
        return max(precio_final, Decimal('0'))  # No puede ser negativo
    
    class Meta:
        verbose_name = "Promoción de Producto"
        verbose_name_plural = "Promociones de Productos"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['producto', 'activa', 'fecha_inicio', 'fecha_fin']),
        ]


# Modelos para Quejas y Reclamos (HU 18)
class Reclamo(models.Model):
    TIPO_RECLAMO = (
        ('producto', 'Producto'),
        ('entrega', 'Entrega'),
        ('servicio', 'Servicio'),
        ('pago', 'Pago'),
        ('otro', 'Otro'),
    )
    
    PRIORIDAD = (
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    )
    
    ESTADO = (
        ('abierto', 'Abierto'),
        ('en_proceso', 'En Proceso'),
        ('resuelto', 'Resuelto'),
        ('cerrado', 'Cerrado'),
    )
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='reclamos')
    tipo = models.CharField(max_length=20, choices=TIPO_RECLAMO, default='otro')
    prioridad = models.CharField(max_length=20, choices=PRIORIDAD, default='media')
    titulo = models.CharField(max_length=200, help_text="Título breve del reclamo")
    descripcion = models.TextField(help_text="Descripción detallada del reclamo")
    estado = models.CharField(max_length=20, choices=ESTADO, default='abierto', db_index=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    asignado_a = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reclamos_asignados', help_text="Usuario asignado para resolver el reclamo")
    resolucion = models.TextField(blank=True, help_text="Descripción de la resolución del reclamo")
    satisfaccion_cliente = models.IntegerField(null=True, blank=True, help_text="Calificación de satisfacción (1-5)", validators=[MinValueValidator(1), MaxValueValidator(5)])
    pedido_relacionado = models.ForeignKey(Pedido, on_delete=models.SET_NULL, null=True, blank=True, related_name='reclamos', help_text="Pedido relacionado si aplica")
    
    def __str__(self):
        return f"Reclamo #{self.id} - {self.titulo} ({self.get_estado_display()})"
    
    def marcar_como_resuelto(self, resolucion_texto="", usuario_resolutor=None):
        """Marca el reclamo como resuelto"""
        self.estado = 'resuelto'
        self.fecha_resolucion = timezone.now()
        if resolucion_texto:
            self.resolucion = resolucion_texto
        if usuario_resolutor:
            self.asignado_a = usuario_resolutor
        self.save()
    
    def cerrar(self):
        """Cierra el reclamo"""
        self.estado = 'cerrado'
        if not self.fecha_resolucion:
            self.fecha_resolucion = timezone.now()
        self.save()
    
    def tiempo_resolucion_horas(self):
        """Calcula el tiempo de resolución en horas"""
        if self.fecha_resolucion and self.fecha_creacion:
            delta = self.fecha_resolucion - self.fecha_creacion
            return round(delta.total_seconds() / 3600, 2)
        return None
    
    class Meta:
        verbose_name = "Reclamo"
        verbose_name_plural = "Reclamos"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['estado', '-fecha_creacion']),
            models.Index(fields=['cliente', '-fecha_creacion']),
            models.Index(fields=['tipo', 'prioridad']),
            models.Index(fields=['asignado_a', 'estado']),
        ]


class ComentarioReclamo(models.Model):
    reclamo = models.ForeignKey(Reclamo, on_delete=models.CASCADE, related_name='comentarios')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comentarios_reclamos')
    comentario = models.TextField()
    es_interno = models.BooleanField(default=False, help_text="Si es True, solo lo ven staff. Si es False, lo ve el cliente también")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    archivo_adjunto = models.FileField(upload_to='reclamos/adjuntos/', blank=True, null=True, help_text="Archivo adjunto al comentario")
    
    def __str__(self):
        tipo = "Interno" if self.es_interno else "Público"
        return f"Comentario {tipo} - Reclamo #{self.reclamo.id} - {self.fecha_creacion.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        verbose_name = "Comentario de Reclamo"
        verbose_name_plural = "Comentarios de Reclamos"
        ordering = ['fecha_creacion']
        indexes = [
            models.Index(fields=['reclamo', 'fecha_creacion']),
        ]