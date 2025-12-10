from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
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

class Pedido(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pedidos')
    vendedor = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos_vendedor', limit_choices_to={'rol': 'vendedor'})
    numero_pedido = models.CharField(max_length=50, unique=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    impuesto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS_PEDIDO, default='pendiente')
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='transferencia')
    notas = models.TextField(blank=True, null=True)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    fecha_entrega_estimada = models.DateField(blank=True, null=True)
    fecha_entrega_real = models.DateField(blank=True, null=True)

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

class DetallesPedido(models.Model):
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
    prioridad = models.CharField(max_length=20, choices=PRIORIDAD_SOLICITUD, default='media')
    ip_solicitante = models.CharField(max_length=45, blank=True, null=True)
    user_agent_solicitante = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Solicitud {self.id} - {self.get_tipo_solicitud_display()} por {self.solicitante.username} ({self.get_estado_display()})"

    def aprobar(self, aprobador_usuario, comentario=""):
        if self.estado == 'pendiente':
            self.estado = 'aprobada'
            self.aprobador = aprobador_usuario
            self.fecha_respuesta = timezone.now()
            self.comentario_respuesta = comentario
            self.save()
            self._aplicar_cambios()
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
            self.aprobador = aprobador_usuario
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
        if solicitante.cliente.rol not in ['vendedor', 'gerente', 'admin_sistema']:
            raise ValueError("Solo vendedores, gerentes y administradores pueden crear solicitudes")

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
            user_agent_solicitante=user_agent
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
