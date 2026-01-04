from rest_framework import serializers
from .models import AuditLog, Cliente, Producto, Pedido, Categoria, SolicitudAutorizacion, LogSistema, EstadisticaVisita, Cupon, PromocionProducto, Reclamo, ComentarioReclamo, DireccionEnvio

class AuditLogSerializer(serializers.ModelSerializer):
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'fecha', 'usuario', 'usuario_email', 'usuario_username',
            'tipo_accion', 'modelo', 'id_objeto', 'datos_anteriores',
            'datos_nuevos', 'descripcion', 'ip_address', 'user_agent',
            'hash_integridad'
        ]
        read_only_fields = ['id', 'fecha', 'hash_integridad']

class ClienteSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    user_date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    gasto_total = serializers.SerializerMethodField()
    total_pedidos = serializers.SerializerMethodField()

    class Meta:
        model = Cliente
        fields = [
            'id', 'user', 'user_email', 'user_username', 'user_first_name',
            'user_last_name', 'rol', 'fecha_nacimiento', 'telefono', 'direccion',
            'comuna', 'email_confirmado', 'api_token', 'user_date_joined',
            'gasto_total', 'total_pedidos'
        ]
        read_only_fields = ['id', 'user_date_joined']

    def get_gasto_total(self, obj):
        return float(sum(pedido.total for pedido in obj.pedidos.all()))

    def get_total_pedidos(self, obj):
        return obj.pedidos.count()

class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    creador_username = serializers.CharField(source='creador.username', read_only=True)
    tiene_promocion = serializers.SerializerMethodField()
    precio_con_descuento = serializers.SerializerMethodField()
    descuento_porcentaje = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'descripcion', 'precio', 'precio_con_descuento', 'stock', 'stock_minimo',
            'categoria', 'categoria_nombre', 'activo', 'imagen_url', 'creador',
            'creador_username', 'fecha_creacion', 'tiene_promocion', 'descuento_porcentaje'
        ]
        read_only_fields = ['id', 'fecha_creacion']
    
    def get_tiene_promocion(self, obj):
        """Indica si el producto tiene una promoción activa"""
        return obj.tiene_promocion_activa()
    
    def get_precio_con_descuento(self, obj):
        """Retorna el precio con descuento si hay promoción"""
        return float(obj.precio_con_descuento())
    
    def get_descuento_porcentaje(self, obj):
        """Retorna el porcentaje de descuento si hay promoción activa"""
        promocion = obj.obtener_promocion_activa()
        if promocion:
            return float(promocion.descuento_porcentaje)
        return None

class PedidoSerializer(serializers.ModelSerializer):
    cliente_email = serializers.CharField(source='cliente.user.email', read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.user.first_name', read_only=True)
    vendedor_email = serializers.EmailField(source='vendedor.user.email', read_only=True, allow_null=True)
    detalles = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = [
            'id', 'cliente', 'cliente_email', 'cliente_nombre', 'vendedor',
            'vendedor_email', 'numero_pedido', 'total', 'subtotal', 'impuesto',
            'descuento', 'estado', 'metodo_pago', 'notas', 'fecha_pedido',
            'fecha_entrega_estimada', 'fecha_entrega_real', 'detalles'
        ]
        read_only_fields = ['id', 'numero_pedido', 'fecha_pedido']

    def get_detalles(self, obj):
        from django.db import connection
        detalles = []
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT dp.producto_id, p.nombre, dp.cantidad, dp.precio_unitario, dp.subtotal
                    FROM inventario_detallespedido dp
                    JOIN inventario_producto p ON dp.producto_id = p.id
                    WHERE dp.pedido_id = %s
                """, [obj.id])
                for row in cursor.fetchall():
                    detalles.append({
                        'producto_id': row[0],
                        'producto_nombre': row[1],
                        'cantidad': row[2],
                        'precio_unitario': float(row[3]),
                        'subtotal': float(row[4])
                    })
        except Exception:
            pass
        return detalles

class CategoriaSerializer(serializers.ModelSerializer):
    total_productos = serializers.SerializerMethodField()
    productos_activos = serializers.SerializerMethodField()

    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion', 'activo', 'total_productos', 'productos_activos']

    def get_total_productos(self, obj):
        return obj.productos.count()

    def get_productos_activos(self, obj):
        return obj.productos.filter(activo=True).count()

class SolicitudAutorizacionSerializer(serializers.ModelSerializer):
    solicitante_email = serializers.CharField(source='solicitante.user.email', read_only=True)
    aprobador_email = serializers.CharField(source='aprobador.user.email', read_only=True, allow_null=True)

    class Meta:
        model = SolicitudAutorizacion
        fields = [
            'id', 'tipo', 'descripcion', 'estado', 'solicitante',
            'solicitante_email', 'aprobador', 'aprobador_email',
            'fecha_solicitud', 'fecha_respuesta', 'respuesta'
        ]
        read_only_fields = ['id', 'fecha_solicitud', 'fecha_respuesta']


class LogSistemaSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)
    nivel_display = serializers.CharField(source='get_nivel_display', read_only=True)
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)

    class Meta:
        model = LogSistema
        fields = [
            'id', 'nivel', 'nivel_display', 'categoria', 'categoria_display',
            'mensaje', 'datos_extra', 'usuario', 'usuario_username', 'usuario_email',
            'ip_address', 'user_agent', 'fecha_creacion', 'modulo', 'funcion'
        ]
        read_only_fields = ['id', 'fecha_creacion']


class EstadisticaVisitaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)

    class Meta:
        model = EstadisticaVisita
        fields = [
            'id', 'producto', 'producto_nombre', 'usuario', 'usuario_username',
            'usuario_email', 'fecha_visita', 'tiempo_visualizacion', 'fuente',
            'ip_address', 'user_agent'
        ]
        read_only_fields = ['id', 'fecha_visita']


class CuponSerializer(serializers.ModelSerializer):
    creador_username = serializers.CharField(source='creado_por.username', read_only=True)
    es_valido = serializers.SerializerMethodField()
    
    class Meta:
        model = Cupon
        fields = [
            'id', 'codigo', 'tipo_descuento', 'descuento_porcentaje', 'descuento_monto',
            'fecha_inicio', 'fecha_fin', 'usos_maximos', 'usos_actuales', 'activo',
            'descripcion', 'monto_minimo', 'creado_por', 'creador_username', 'fecha_creacion', 'es_valido'
        ]
        read_only_fields = ['id', 'usos_actuales', 'fecha_creacion', 'creado_por']
    
    def get_es_valido(self, obj):
        """Indica si el cupón es válido"""
        return obj.es_valido()


class PromocionProductoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    creador_username = serializers.CharField(source='creado_por.username', read_only=True)
    esta_vigente = serializers.SerializerMethodField()
    precio_original = serializers.DecimalField(source='producto.precio', max_digits=10, decimal_places=2, read_only=True)
    precio_con_descuento = serializers.SerializerMethodField()
    
    class Meta:
        model = PromocionProducto
        fields = [
            'id', 'producto', 'producto_nombre', 'descuento_porcentaje', 'fecha_inicio',
            'fecha_fin', 'activa', 'descripcion', 'creado_por', 'creador_username',
            'fecha_creacion', 'esta_vigente', 'precio_original', 'precio_con_descuento'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'creado_por']
    
    def get_esta_vigente(self, obj):
        """Indica si la promoción está vigente"""
        return obj.esta_vigente()
    
    def get_precio_con_descuento(self, obj):
        """Retorna el precio con descuento"""
        return float(obj.calcular_precio_con_descuento())


class ComentarioReclamoSerializer(serializers.ModelSerializer):
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)
    
    class Meta:
        model = ComentarioReclamo
        fields = [
            'id', 'reclamo', 'usuario', 'usuario_email', 'usuario_nombre',
            'comentario', 'es_interno', 'fecha_creacion', 'archivo_adjunto'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'usuario']


class ReclamoSerializer(serializers.ModelSerializer):
    cliente_email = serializers.CharField(source='cliente.user.email', read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.user.get_full_name', read_only=True)
    asignado_a_email = serializers.CharField(source='asignado_a.email', read_only=True, allow_null=True)
    asignado_a_nombre = serializers.CharField(source='asignado_a.get_full_name', read_only=True, allow_null=True)
    pedido_numero = serializers.CharField(source='pedido_relacionado.numero_pedido', read_only=True, allow_null=True)
    comentarios = ComentarioReclamoSerializer(many=True, read_only=True)
    tiempo_resolucion_horas = serializers.SerializerMethodField()
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    prioridad_display = serializers.CharField(source='get_prioridad_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Reclamo
        fields = [
            'id', 'cliente', 'cliente_email', 'cliente_nombre', 'tipo', 'tipo_display',
            'prioridad', 'prioridad_display', 'titulo', 'descripcion', 'estado', 'estado_display',
            'fecha_creacion', 'fecha_resolucion', 'fecha_actualizacion', 'asignado_a',
            'asignado_a_email', 'asignado_a_nombre', 'resolucion', 'satisfaccion_cliente',
            'pedido_relacionado', 'pedido_numero', 'comentarios', 'tiempo_resolucion_horas'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']
    
    def get_tiempo_resolucion_horas(self, obj):
        """Retorna el tiempo de resolución en horas"""
        return obj.tiempo_resolucion_horas()


class DireccionEnvioSerializer(serializers.ModelSerializer):
    cliente_email = serializers.CharField(source='cliente.user.email', read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.user.get_full_name', read_only=True)
    region_display = serializers.CharField(source='get_region_display', read_only=True)
    direccion_completa = serializers.SerializerMethodField()
    
    class Meta:
        model = DireccionEnvio
        fields = [
            'id', 'cliente', 'cliente_email', 'cliente_nombre', 'nombre', 'calle', 'numero',
            'comuna', 'ciudad', 'region', 'region_display', 'codigo_postal', 'telefono',
            'es_principal', 'fecha_creacion', 'fecha_actualizacion', 'direccion_completa'
        ]
        read_only_fields = ['id', 'cliente', 'fecha_creacion', 'fecha_actualizacion']
    
    def get_direccion_completa(self, obj):
        """Retorna la dirección completa formateada"""
        return f"{obj.calle} {obj.numero}, {obj.comuna}, {obj.ciudad}, {obj.get_region_display()}"
