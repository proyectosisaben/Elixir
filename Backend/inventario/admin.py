from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import Categoria, Proveedor, Producto, ProductoImagen, Cliente, Cupon, PromocionProducto, Reclamo, ComentarioReclamo, DireccionEnvio, Pedido, DetallesPedido

admin.site.register(Categoria)
admin.site.register(Proveedor)
admin.site.register(Producto)
admin.site.register(ProductoImagen)
admin.site.register(Cliente)
admin.site.register(DetallesPedido)


class DetallesPedidoInline(admin.TabularInline):
    """Inline para mostrar detalles de pedido en el admin"""
    model = DetallesPedido
    extra = 0
    readonly_fields = ['subtotal']
    fields = ['producto', 'cantidad', 'precio_unitario', 'subtotal']


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['numero_pedido', 'cliente_display', 'total', 'estado', 'metodo_pago', 'fecha_pedido', 'vendedor_display']
    list_filter = ['estado', 'metodo_pago', 'fecha_pedido', 'metodo_envio']
    search_fields = ['numero_pedido', 'cliente__user__email', 'cliente__user__username']
    readonly_fields = ['numero_pedido', 'fecha_pedido', 'fecha_entrega_estimada']
    fieldsets = (
        ('Información Básica', {
            'fields': ('numero_pedido', 'cliente', 'vendedor', 'fecha_pedido')
        }),
        ('Estado y Pagos', {
            'fields': ('estado', 'metodo_pago', 'fecha_entrega_estimada', 'fecha_entrega_real')
        }),
        ('Montos', {
            'fields': ('subtotal', 'impuesto', 'descuento', 'total', 'costo_envio')
        }),
        ('Envío', {
            'fields': ('metodo_envio', 'direccion_envio')
        }),
        ('Notas', {
            'fields': ('notas',),
            'classes': ('collapse',)
        }),
    )
    inlines = [DetallesPedidoInline]
    actions = ['marcar_como_pagado', 'marcar_como_en_preparacion', 'marcar_como_enviado', 'marcar_como_entregado', 'marcar_como_cancelado']

    def cliente_display(self, obj):
        """Muestra el email del cliente"""
        return obj.cliente.user.email
    cliente_display.short_description = 'Cliente'

    def vendedor_display(self, obj):
        """Muestra el email del vendedor si existe"""
        if obj.vendedor:
            return obj.vendedor.user.email
        return "Sin asignar"
    vendedor_display.short_description = 'Vendedor'

    def marcar_como_pagado(self, request, queryset):
        """Marcar pedidos seleccionados como pagados"""
        updated = 0
        for pedido in queryset:
            if pedido.estado == 'pendiente':
                pedido.marcar_como_pagado()
                updated += 1
        self.message_user(request, f'{updated} pedido(s) marcado(s) como pagado(s).')
    marcar_como_pagado.short_description = 'Marcar como pagado'

    def marcar_como_en_preparacion(self, request, queryset):
        """Marcar pedidos seleccionados como en preparación"""
        updated = 0
        for pedido in queryset:
            if pedido.estado in ['pendiente', 'pagado']:
                pedido.estado = 'en_preparacion'
                pedido.save()
                updated += 1
        self.message_user(request, f'{updated} pedido(s) marcado(s) como en preparación.')
    marcar_como_en_preparacion.short_description = 'Marcar como en preparación'

    def marcar_como_enviado(self, request, queryset):
        """Marcar pedidos seleccionados como enviados"""
        updated = 0
        for pedido in queryset:
            if pedido.estado in ['pagado', 'en_preparacion']:
                pedido.marcar_como_enviado()
                updated += 1
        self.message_user(request, f'{updated} pedido(s) marcado(s) como enviado(s).')
    marcar_como_enviado.short_description = 'Marcar como enviado'

    def marcar_como_entregado(self, request, queryset):
        """Marcar pedidos seleccionados como entregados"""
        updated = 0
        for pedido in queryset:
            if pedido.estado == 'enviado':
                pedido.marcar_como_entregado()
                updated += 1
        self.message_user(request, f'{updated} pedido(s) marcado(s) como entregado(s).')
    marcar_como_entregado.short_description = 'Marcar como entregado'

    def marcar_como_cancelado(self, request, queryset):
        """Marcar pedidos seleccionados como cancelados"""
        updated = 0
        for pedido in queryset:
            if pedido.estado != 'entregado':
                pedido.estado = 'cancelado'
                pedido.save()
                updated += 1
        self.message_user(request, f'{updated} pedido(s) marcado(s) como cancelado(s).')
    marcar_como_cancelado.short_description = 'Marcar como cancelado'

    def has_add_permission(self, request):
        """Solo gerentes y admins pueden crear pedidos manualmente"""
        if request.user.is_authenticated:
            try:
                cliente = request.user.cliente
                return cliente.rol in ['gerente', 'admin_sistema']
            except:
                return request.user.is_superuser
        return False

    def has_change_permission(self, request, obj=None):
        """Vendedores, gerentes y admins pueden modificar pedidos"""
        if request.user.is_authenticated:
            try:
                cliente = request.user.cliente
                return cliente.rol in ['vendedor', 'gerente', 'admin_sistema']
            except:
                return request.user.is_superuser
        return False

    def has_delete_permission(self, request, obj=None):
        """Solo gerentes y admins pueden eliminar pedidos"""
        if request.user.is_authenticated:
            try:
                cliente = request.user.cliente
                return cliente.rol in ['gerente', 'admin_sistema']
            except:
                return request.user.is_superuser
        return False


@admin.register(Cupon)
class CuponAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'tipo_descuento', 'descuento_display', 'fecha_inicio', 'fecha_fin', 'usos_actuales', 'usos_maximos', 'activo', 'es_valido_display']
    list_filter = ['activo', 'tipo_descuento', 'fecha_inicio', 'fecha_fin']
    search_fields = ['codigo', 'descripcion']
    readonly_fields = ['usos_actuales', 'fecha_creacion', 'creado_por', 'preview_cupon']
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'descripcion', 'activo', 'preview_cupon')
        }),
        ('Descuento', {
            'fields': ('tipo_descuento', 'descuento_porcentaje', 'descuento_monto', 'monto_minimo'),
            'description': 'Elija porcentaje o monto fijo. Si elige porcentaje, complete descuento_porcentaje. Si elige monto, complete descuento_monto.'
        }),
        ('Vigencia', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Límites de Uso', {
            'fields': ('usos_maximos', 'usos_actuales')
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'fecha_creacion'),
            'classes': ('collapse',)
        }),
    )
    
    def descuento_display(self, obj):
        """Muestra el descuento de forma legible"""
        if obj.tipo_descuento == 'porcentaje' and obj.descuento_porcentaje:
            return f"{obj.descuento_porcentaje}%"
        elif obj.tipo_descuento == 'monto' and obj.descuento_monto:
            return f"${obj.descuento_monto}"
        return "-"
    descuento_display.short_description = 'Descuento'
    
    def es_valido_display(self, obj):
        """Muestra si el cupón es válido"""
        if obj.es_valido():
            return "✅ Válido"
        return "❌ Inválido"
    es_valido_display.short_description = 'Estado'
    
    def preview_cupon(self, obj):
        """Muestra una vista previa del cupón"""
        if obj.pk:  # Solo si el objeto ya existe
            if obj.es_valido():
                estado = "✅ VÁLIDO"
                color = "green"
            else:
                estado = "❌ INVÁLIDO"
                color = "red"
            
            descuento_texto = ""
            if obj.tipo_descuento == 'porcentaje' and obj.descuento_porcentaje:
                descuento_texto = f"{obj.descuento_porcentaje}% de descuento"
            elif obj.tipo_descuento == 'monto' and obj.descuento_monto:
                descuento_texto = f"${obj.descuento_monto} de descuento"
            
            return format_html(
                '<div style="padding: 10px; border: 2px solid {}; border-radius: 5px; background-color: #f9f9f9;">'
                '<h3 style="margin: 0; color: {};">{}</h3>'
                '<p style="margin: 5px 0;"><strong>Código:</strong> {}</p>'
                '<p style="margin: 5px 0;"><strong>Descuento:</strong> {}</p>'
                '<p style="margin: 5px 0;"><strong>Usos:</strong> {} / {}</p>'
                '<p style="margin: 5px 0;"><strong>Monto mínimo:</strong> ${}</p>'
                '</div>',
                color, color, estado, obj.codigo, descuento_texto, 
                obj.usos_actuales, obj.usos_maximos, obj.monto_minimo
            )
        return "Guarde el cupón para ver la vista previa"
    preview_cupon.short_description = 'Vista Previa del Cupón'
    
    def save_model(self, request, obj, form, change):
        """Asigna el usuario que crea el cupón"""
        if not change:  # Solo al crear
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
    
    class Media:
        css = {
            'all': ('admin/css/cupon_admin.css',)
        }
    
    def has_add_permission(self, request):
        """Solo gerentes y admins pueden crear cupones"""
        if request.user.is_authenticated:
            try:
                cliente = request.user.cliente
                return cliente.rol in ['gerente', 'admin_sistema']
            except:
                return request.user.is_superuser
        return False
    
    def has_change_permission(self, request, obj=None):
        """Solo gerentes y admins pueden modificar cupones"""
        if request.user.is_authenticated:
            try:
                cliente = request.user.cliente
                return cliente.rol in ['gerente', 'admin_sistema']
            except:
                return request.user.is_superuser
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Solo gerentes y admins pueden eliminar cupones"""
        if request.user.is_authenticated:
            try:
                cliente = request.user.cliente
                return cliente.rol in ['gerente', 'admin_sistema']
            except:
                return request.user.is_superuser
        return False


@admin.register(PromocionProducto)
class PromocionProductoAdmin(admin.ModelAdmin):
    list_display = ['producto', 'descuento_porcentaje', 'fecha_inicio', 'fecha_fin', 'activa', 'esta_vigente_display']
    list_filter = ['activa', 'fecha_inicio', 'fecha_fin']
    search_fields = ['producto__nombre', 'descripcion']
    readonly_fields = ['fecha_creacion', 'creado_por']
    fieldsets = (
        ('Información Básica', {
            'fields': ('producto', 'descripcion', 'activa')
        }),
        ('Descuento', {
            'fields': ('descuento_porcentaje',)
        }),
        ('Vigencia', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Auditoría', {
            'fields': ('creado_por', 'fecha_creacion'),
            'classes': ('collapse',)
        }),
    )
    
    def esta_vigente_display(self, obj):
        """Muestra si la promoción está vigente"""
        if obj.esta_vigente():
            return "✅ Vigente"
        return "❌ No vigente"
    esta_vigente_display.short_description = 'Estado'
    
    def save_model(self, request, obj, form, change):
        """Asigna el usuario que crea la promoción"""
        if not change:  # Solo al crear
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)
    
    def has_add_permission(self, request):
        """Solo gerentes y admins pueden crear promociones"""
        if request.user.is_authenticated:
            try:
                cliente = request.user.cliente
                return cliente.rol in ['gerente', 'admin_sistema']
            except:
                return request.user.is_superuser
        return False
    
    def has_change_permission(self, request, obj=None):
        """Solo gerentes y admins pueden modificar promociones"""
        if request.user.is_authenticated:
            try:
                cliente = request.user.cliente
                return cliente.rol in ['gerente', 'admin_sistema']
            except:
                return request.user.is_superuser
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Solo gerentes y admins pueden eliminar promociones"""
        if request.user.is_authenticated:
            try:
                cliente = request.user.cliente
                return cliente.rol in ['gerente', 'admin_sistema']
            except:
                return request.user.is_superuser
        return False


class ComentarioReclamoInline(admin.TabularInline):
    """Inline para mostrar comentarios en el admin de reclamos"""
    model = ComentarioReclamo
    extra = 0
    readonly_fields = ['usuario', 'fecha_creacion']
    fields = ['usuario', 'comentario', 'es_interno', 'fecha_creacion']
    can_delete = False


@admin.register(Reclamo)
class ReclamoAdmin(admin.ModelAdmin):
    list_display = ['id', 'titulo', 'cliente_display', 'tipo', 'prioridad', 'estado', 'asignado_a_display', 'fecha_creacion', 'tiempo_resolucion_display']
    list_filter = ['estado', 'tipo', 'prioridad', 'fecha_creacion']
    search_fields = ['titulo', 'descripcion', 'cliente__user__email']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 'tiempo_resolucion_display']
    fieldsets = (
        ('Información Básica', {
            'fields': ('cliente', 'titulo', 'descripcion', 'pedido_relacionado')
        }),
        ('Clasificación', {
            'fields': ('tipo', 'prioridad', 'estado')
        }),
        ('Asignación', {
            'fields': ('asignado_a',)
        }),
        ('Resolución', {
            'fields': ('resolucion', 'fecha_resolucion', 'satisfaccion_cliente'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion', 'tiempo_resolucion_display'),
            'classes': ('collapse',)
        }),
    )
    inlines = [ComentarioReclamoInline]
    
    def cliente_display(self, obj):
        """Muestra el email del cliente"""
        return obj.cliente.user.email
    cliente_display.short_description = 'Cliente'
    
    def asignado_a_display(self, obj):
        """Muestra a quién está asignado el reclamo"""
        if obj.asignado_a:
            return obj.asignado_a.email
        return "Sin asignar"
    asignado_a_display.short_description = 'Asignado a'
    
    def tiempo_resolucion_display(self, obj):
        """Muestra el tiempo de resolución"""
        tiempo = obj.tiempo_resolucion_horas()
        if tiempo:
            if tiempo < 24:
                return f"{tiempo} horas"
            else:
                dias = tiempo / 24
                return f"{dias:.1f} días"
        return "Pendiente"
    tiempo_resolucion_display.short_description = 'Tiempo de Resolución'
    
    def has_add_permission(self, request):
        """Clientes, vendedores, gerentes y admins pueden crear reclamos"""
        if request.user.is_authenticated:
            try:
                cliente = request.user.cliente
                return cliente.rol in ['cliente', 'vendedor', 'gerente', 'admin_sistema']
            except:
                return request.user.is_superuser
        return False
    
    def has_change_permission(self, request, obj=None):
        """Solo vendedores, gerentes y admins pueden modificar reclamos"""
        if request.user.is_authenticated:
            try:
                cliente = request.user.cliente
                return cliente.rol in ['vendedor', 'gerente', 'admin_sistema']
            except:
                return request.user.is_superuser
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Solo gerentes y admins pueden eliminar reclamos"""
        if request.user.is_authenticated:
            try:
                cliente = request.user.cliente
                return cliente.rol in ['gerente', 'admin_sistema']
            except:
                return request.user.is_superuser
        return False


@admin.register(ComentarioReclamo)
class ComentarioReclamoAdmin(admin.ModelAdmin):
    list_display = ['id', 'reclamo', 'usuario', 'es_interno', 'fecha_creacion', 'comentario_preview']
    list_filter = ['es_interno', 'fecha_creacion']
    search_fields = ['comentario', 'reclamo__titulo']
    readonly_fields = ['fecha_creacion']
    
    def comentario_preview(self, obj):
        """Vista previa del comentario"""
        return obj.comentario[:50] + "..." if len(obj.comentario) > 50 else obj.comentario
    comentario_preview.short_description = 'Comentario'


@admin.register(DireccionEnvio)
class DireccionEnvioAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente_display', 'nombre', 'direccion_completa', 'region', 'es_principal', 'fecha_creacion']
    list_filter = ['region', 'es_principal', 'fecha_creacion']
    search_fields = ['cliente__user__email', 'nombre', 'calle', 'comuna', 'ciudad']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    fieldsets = (
        ('Información Básica', {
            'fields': ('cliente', 'nombre', 'es_principal')
        }),
        ('Dirección', {
            'fields': ('calle', 'numero', 'comuna', 'ciudad', 'region', 'codigo_postal')
        }),
        ('Contacto', {
            'fields': ('telefono',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def cliente_display(self, obj):
        """Muestra el email del cliente"""
        return obj.cliente.user.email
    cliente_display.short_description = 'Cliente'
    
    def direccion_completa(self, obj):
        """Muestra la dirección completa"""
        return f"{obj.calle} {obj.numero}, {obj.comuna}, {obj.ciudad}"
    direccion_completa.short_description = 'Dirección'
    
    def has_add_permission(self, request):
        """Solo clientes pueden crear direcciones"""
        if request.user.is_authenticated:
            try:
                cliente = request.user.cliente
                return cliente.rol == 'cliente'
            except:
                return False
        return False
    
    def has_change_permission(self, request, obj=None):
        """Solo el cliente dueño puede modificar su dirección"""
        if request.user.is_authenticated:
            try:
                cliente = request.user.cliente
                if cliente.rol == 'cliente':
                    if obj:
                        return obj.cliente == cliente
                    return True
                return cliente.rol in ['gerente', 'admin_sistema']
            except:
                return request.user.is_superuser
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Solo el cliente dueño puede eliminar su dirección"""
        if request.user.is_authenticated:
            try:
                cliente = request.user.cliente
                if cliente.rol == 'cliente':
                    if obj:
                        return obj.cliente == cliente
                    return True
                return cliente.rol in ['gerente', 'admin_sistema']
            except:
                return request.user.is_superuser
        return False
