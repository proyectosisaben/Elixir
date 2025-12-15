from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    # API endpoints
    path('home/', views.home, name='api_home'),
    path('catalogo/', views.catalogo, name='api_catalogo'),
    path('productos/sugerencias/', views.sugerencias_productos, name='api_sugerencias_productos'),
    path('producto/<int:producto_id>/', views.detalle_producto, name='api_detalle_producto'),
    path('checkout/', views.checkout, name='api_checkout'),
    path('productos/', views.api_productos, name='api_productos'),
    path('productos', views.api_productos, name='api_productos_root'),
    path('categorias/', views.api_categorias, name='api_categorias'),
    path('productos-lista/', views.api_productos_lista, name='api_productos_lista'),
    path('registro/', views.registro_cliente, name='api_registro_cliente'),
    path('login/', views.login_cliente, name='api_login_cliente'),
    
    # Endpoints de gestión de roles
    path('cambiar-rol/', views.cambiar_rol_cliente, name='api_cambiar_rol'),
    path('verificar-rol/', views.verificar_rol, name='api_verificar_rol'),
    path('listar-clientes/', views.listar_clientes, name='api_listar_clientes'),
    
    # Endpoints para pedidos y checkout
    path('crear-pedido/', views.crear_pedido, name='api_crear_pedido'),
    path('mis-pedidos/', views.mis_pedidos, name='api_mis_pedidos'),
    path('dashboard-admin/', views.dashboard_gerente, name='api_dashboard_admin'),
    path('mi-perfil/', views.mi_perfil, name='api_mi_perfil'),
    path('marcar-pagado/', views.marcar_pedido_pagado, name='api_marcar_pagado'),
    path('cambiar-estado-pedido/', views.cambiar_estado_pedido, name='api_cambiar_estado_pedido'),
    path('confirmar-envio/', views.confirmar_envio_pedido, name='api_confirmar_envio_pedido'),
    path('pedidos/gestion/', views.listar_pedidos_gestion, name='api_listar_pedidos_gestion'),
    
    # Endpoints para edición de productos y sliders
    path('productos/<int:producto_id>/actualizar/', views.actualizar_producto, name='api_actualizar_producto'),
    path('productos/crear/', views.crear_producto, name='api_crear_producto'),
    path('productos/<int:producto_id>/actualizar-stock/', views.actualizar_stock_producto, name='api_actualizar_stock'),
    path('productos/<int:producto_id>/', views.obtener_eliminar_producto, name='api_obtener_eliminar_producto'),
    path('sliders/', views.obtener_sliders, name='api_sliders'),
    
    # Endpoints de ventas y métricas
    path('ventas-totales/', views.obtener_ventas_totales, name='api_ventas_totales'),
    path('ventas/analiticas/', views.ventas_analiticas, name='api_ventas_analiticas'),
    path('ventas/exportar/', views.ventas_exportar, name='api_ventas_exportar'),
    path('ventas/filtradas-gerente/', views.ventas_filtradas_gerente, name='api_ventas_filtradas_gerente'),
    path('dashboard-admin/estadisticas/', views.dashboard_admin_estadisticas, name='api_dashboard_admin_stats'),

    # Endpoints de monitoreo del sistema - HU 40
    path('sistema/logs/', views.logs_sistema, name='api_logs_sistema'),
    path('sistema/estadisticas/', views.estadisticas_sistema, name='api_estadisticas_sistema'),
    path('sistema/registrar-visita/', views.registrar_visita_producto, name='api_registrar_visita'),
    
    # CRUD de catálogo - Admin
    path('admin/catalogo/productos/', views.catalogo_admin, name='api_catalogo_admin_list'),
    path('admin/catalogo/productos/<int:producto_id>/', views.detalle_catalogo_admin, name='api_catalogo_admin_detail'),
    
    # Endpoints de Auditoría y Trazabilidad (HU 20)
    path('auditoria/logs/', views.listar_audit_logs, name='api_audit_logs'),
    path('auditoria/logs/<int:log_id>/', views.detalle_audit_log, name='api_audit_log_detail'),
    path('auditoria/estadisticas/', views.estadisticas_auditoria, name='api_audit_stats'),
    path('auditoria/exportar/', views.exportar_audit_logs, name='api_audit_export'),

    # Endpoints de Autorizaciones de Inventario (HU 50)
    path('autorizaciones/solicitudes/', views.listar_solicitudes_autorizacion, name='api_listar_autorizaciones'),
    path('autorizaciones/crear/', views.crear_solicitud_autorizacion, name='api_crear_autorizacion'),
    path('autorizaciones/<int:solicitud_id>/gestionar/', views.gestionar_solicitud_autorizacion, name='api_gestionar_autorizacion'),
    path('autorizaciones/<int:solicitud_id>/test/', views.test_gestion_autorizacion, name='api_test_gestion_autorizacion'),
    path('autorizaciones/notificaciones/', views.notificaciones_autorizaciones, name='api_notificaciones_autorizaciones'),
    path('autorizaciones/test/', views.test_autorizaciones, name='api_test_autorizaciones'),
    path('autorizaciones/reparar/', views.reparar_autorizaciones, name='api_reparar_autorizaciones'),

    # Endpoints de clientes - HU 23
    path('clientes/buscar/', views.buscar_clientes, name='api_buscar_clientes'),
    path('clientes/<int:cliente_id>/', views.detalle_cliente, name='api_detalle_cliente'),

    # Endpoints de Reportes Financieros - HU 7
    path('reportes/generar/', views.generar_reporte_financiero, name='api_generar_reporte'),
    path('reportes/listar/', views.listar_reportes_financieros, name='api_listar_reportes'),
    path('reportes/<int:reporte_id>/eliminar/', views.eliminar_reporte, name='api_eliminar_reporte'),

    # Endpoints de Cupones y Promociones - HU 11
    path('cupones/', views.gestionar_cupones, name='api_gestionar_cupones'),
    path('cupones/<int:cupon_id>/', views.gestionar_cupon, name='api_gestionar_cupon'),
    path('cupones/validar/', views.validar_cupon, name='api_validar_cupon'),
    path('promociones/', views.gestionar_promociones, name='api_gestionar_promociones'),
    path('promociones/<int:promocion_id>/', views.gestionar_promocion, name='api_gestionar_promocion'),
    path('promociones/reportes/efectividad/', views.reportes_efectividad_promociones, name='api_reportes_efectividad'),

    # Endpoints de Reclamos y Quejas - HU 18
    path('reclamos/', views.gestionar_reclamos, name='api_gestionar_reclamos'),
    path('reclamos/<int:reclamo_id>/', views.gestionar_reclamo, name='api_gestionar_reclamo'),
    path('reclamos/<int:reclamo_id>/comentarios/', views.gestionar_comentarios_reclamo, name='api_gestionar_comentarios_reclamo'),
    path('reclamos/reportes/', views.reporte_reclamos, name='api_reporte_reclamos'),

    # Endpoints de POS (Punto de Venta) - HU 22
    path('pos/buscar-producto/', views.pos_buscar_producto, name='api_pos_buscar_producto'),
    path('pos/crear-venta/', views.pos_crear_venta, name='api_pos_crear_venta'),
    path('pos/cierre-caja/', views.pos_cierre_caja, name='api_pos_cierre_caja'),

    # Endpoints de Recomendaciones - HU 32
    path('recomendaciones/', views.obtener_recomendaciones, name='api_recomendaciones'),
    path('productos/<int:producto_id>/relacionados/', views.productos_relacionados, name='api_productos_relacionados'),

    # Endpoints de Direcciones de Envío - HU 35
    path('direcciones/', views.gestionar_direcciones, name='api_direcciones'),
    path('direcciones/<int:direccion_id>/', views.gestionar_direccion, name='api_direccion'),
    path('direcciones/regiones-comunas/', views.obtener_regiones_comunas, name='api_regiones_comunas'),
    path('envio/calcular-costo/', views.calcular_costo_envio, name='api_calcular_costo_envio'),
    path('envio/metodos/', views.obtener_metodos_envio, name='api_metodos_envio'),

    # Endpoint para poblar datos de prueba
    path('poblar-datos/', views.poblar_datos, name='api_poblar_datos'),

    # Legacy URLs (redirect to home)
    path('', views.home, name='index'),
]

