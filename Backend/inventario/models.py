from django.db import models
from django.contrib.auth.models import User

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
