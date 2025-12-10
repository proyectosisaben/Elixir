from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    # API endpoints
    path('home/', views.home, name='api_home'),
    path('catalogo/', views.catalogo, name='api_catalogo'),
    path('producto/<int:producto_id>/', views.detalle_producto, name='api_detalle_producto'),
    path('checkout/', views.checkout, name='api_checkout'),
    path('productos/', views.api_productos, name='api_productos'),
    path('productos', views.api_productos, name='api_productos_root'),
    path('registro/', views.registro_cliente, name='api_registro_cliente'),
    path('login/', views.login_cliente, name='api_login_cliente'),
    
    # Endpoints de gestión de roles
    path('cambiar-rol/', views.cambiar_rol_cliente, name='api_cambiar_rol'),
    path('verificar-rol/', views.verificar_rol, name='api_verificar_rol'),
    path('listar-clientes/', views.listar_clientes, name='api_listar_clientes'),
    
    # Endpoints para pedidos y checkout
    path('crear-pedido/', views.crear_pedido, name='api_crear_pedido'),
    path('mis-pedidos/', views.mis_pedidos, name='api_mis_pedidos'),
    path('dashboard-gerente/', views.dashboard_gerente, name='api_dashboard_gerente'),
    path('mi-perfil/', views.mi_perfil, name='api_mi_perfil'),
    path('marcar-pagado/', views.marcar_pedido_pagado, name='api_marcar_pagado'),
    
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
    path('dashboard-admin/estadisticas/', views.dashboard_admin_estadisticas, name='api_dashboard_admin_stats'),
    
    # CRUD de catálogo - Admin
    path('admin/catalogo/productos/', views.catalogo_admin, name='api_catalogo_admin_list'),
    path('admin/catalogo/productos/<int:producto_id>/', views.detalle_catalogo_admin, name='api_catalogo_admin_detail'),
    
    # Endpoints de Auditoría y Trazabilidad (HU 20)
    path('auditoria/logs/', views.listar_audit_logs, name='api_audit_logs'),
    path('auditoria/logs/<int:log_id>/', views.detalle_audit_log, name='api_audit_log_detail'),
    path('auditoria/estadisticas/', views.estadisticas_auditoria, name='api_audit_stats'),
    path('auditoria/exportar/', views.exportar_audit_logs, name='api_audit_export'),
    
    # Legacy URLs (redirect to home)
    path('', views.home, name='index'),
]

