"""
Servicios para generación de reportes financieros en PDF
"""
from io import BytesIO
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Q
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from .models import Producto, Pedido, DetallesPedido, Categoria, ReporteFinanciero


class GeneradorReporteFinanciero:
    """Clase para generar reportes financieros en PDF"""
    
    def __init__(self, fecha_inicio, fecha_fin, tipo_reporte='resumen_completo', categoria=None):
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.tipo_reporte = tipo_reporte
        self.categoria = categoria
        self.buffer = BytesIO()
        
    def generar_pdf(self):
        """Genera el PDF del reporte y retorna el buffer"""
        doc = SimpleDocTemplate(self.buffer, pagesize=letter)
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        
        # Título
        titulo = Paragraph("REPORTE FINANCIERO ELIXIR", title_style)
        elements.append(titulo)
        
        # Información del período
        periodo_text = f"Período: {self.fecha_inicio.strftime('%d/%m/%Y')} - {self.fecha_fin.strftime('%d/%m/%Y')}"
        elements.append(Paragraph(periodo_text, styles['Normal']))
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Obtener datos
        pedidos = self._obtener_pedidos_filtrados()
        
        # Generar secciones según tipo de reporte
        if self.tipo_reporte in ['ventas_general', 'resumen_completo']:
            elements.extend(self._generar_seccion_ventas(styles, heading_style, pedidos))
            elements.append(Spacer(1, 20))
        
        if self.tipo_reporte in ['productos_top', 'resumen_completo']:
            elements.extend(self._generar_seccion_productos_top(styles, heading_style, pedidos))
            elements.append(Spacer(1, 20))
        
        if self.tipo_reporte in ['ingresos_categoria', 'resumen_completo']:
            elements.extend(self._generar_seccion_ingresos_categoria(styles, heading_style, pedidos))
            elements.append(Spacer(1, 20))
        
        if self.tipo_reporte == 'resumen_completo':
            elements.append(PageBreak())
            elements.extend(self._generar_seccion_analisis(styles, heading_style, pedidos))
        
        # Construir PDF
        doc.build(elements)
        self.buffer.seek(0)
        return self.buffer
    
    def _obtener_pedidos_filtrados(self):
        """Obtiene los pedidos filtrados por período y categoría"""
        pedidos = Pedido.objects.filter(
            fecha_pedido__date__gte=self.fecha_inicio,
            fecha_pedido__date__lte=self.fecha_fin,
            estado__in=['pagado', 'entregado']
        )
        
        if self.categoria:
            pedidos = pedidos.filter(
                detallespedido__producto__categoria=self.categoria
            ).distinct()
        
        return pedidos
    
    def _generar_seccion_ventas(self, styles, heading_style, pedidos):
        """Genera la sección de ventas generales"""
        elements = []
        elements.append(Paragraph("Ventas Generales", heading_style))
        
        # Calcular totales
        total_pedidos = pedidos.count()
        total_ventas = pedidos.aggregate(Sum('total'))['total__sum'] or Decimal('0')
        total_itemsvendidos = DetallesPedido.objects.filter(
            pedido__in=pedidos
        ).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
        
        ticket_promedio = total_ventas / total_pedidos if total_pedidos > 0 else Decimal('0')
        
        # Tabla de resumen
        datos_tabla = [
            ['Métrica', 'Valor'],
            ['Total de Pedidos', str(total_pedidos)],
            ['Total de Ventas', f"${total_ventas:,.2f}"],
            ['Ticket Promedio', f"${ticket_promedio:,.2f}"],
            ['Items Vendidos', str(total_itemsvendidos)],
        ]
        
        tabla = Table(datos_tabla, colWidths=[3*inch, 3*inch])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(tabla)
        return elements
    
    def _generar_seccion_productos_top(self, styles, heading_style, pedidos):
        """Genera la sección de productos más vendidos"""
        elements = []
        elements.append(Paragraph("Top 10 Productos Más Vendidos", heading_style))
        
        # Obtener productos más vendidos
        productos_top = DetallesPedido.objects.filter(
            pedido__in=pedidos
        ).values('producto__nombre', 'producto__sku').annotate(
            cantidad_total=Sum('cantidad'),
            ingresos_total=Sum('subtotal')
        ).order_by('-cantidad_total')[:10]
        
        if productos_top:
            datos_tabla = [
                ['Posición', 'Producto', 'SKU', 'Cantidad', 'Ingresos'],
            ]
            
            for idx, prod in enumerate(productos_top, 1):
                datos_tabla.append([
                    str(idx),
                    prod['producto__nombre'][:30],
                    prod['producto__sku'],
                    str(prod['cantidad_total']),
                    f"${prod['ingresos_total']:,.2f}"
                ])
            
            tabla = Table(datos_tabla, colWidths=[0.8*inch, 2.5*inch, 1*inch, 1*inch, 1.7*inch])
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(tabla)
        else:
            elements.append(Paragraph("No hay datos disponibles", styles['Normal']))
        
        return elements
    
    def _generar_seccion_ingresos_categoria(self, styles, heading_style, pedidos):
        """Genera la sección de ingresos por categoría"""
        elements = []
        elements.append(Paragraph("Ingresos por Categoría", heading_style))
        
        # Obtener ingresos por categoría
        categorias_ingresos = DetallesPedido.objects.filter(
            pedido__in=pedidos
        ).values('producto__categoria__nombre').annotate(
            total_ingresos=Sum('subtotal'),
            cantidad=Sum('cantidad')
        ).order_by('-total_ingresos')
        
        if categorias_ingresos:
            total_general = sum(cat['total_ingresos'] for cat in categorias_ingresos)
            
            datos_tabla = [
                ['Categoría', 'Ingresos', '%', 'Cantidad Items'],
            ]
            
            for cat in categorias_ingresos:
                porcentaje = (cat['total_ingresos'] / total_general * 100) if total_general > 0 else 0
                datos_tabla.append([
                    cat['producto__categoria__nombre'],
                    f"${cat['total_ingresos']:,.2f}",
                    f"{porcentaje:.1f}%",
                    str(cat['cantidad'])
                ])
            
            # Fila de total
            datos_tabla.append([
                'TOTAL',
                f"${total_general:,.2f}",
                '100.0%',
                str(sum(cat['cantidad'] for cat in categorias_ingresos))
            ])
            
            tabla = Table(datos_tabla, colWidths=[2.5*inch, 1.8*inch, 1*inch, 1.7*inch])
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d3d3d3')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -2), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(tabla)
        else:
            elements.append(Paragraph("No hay datos disponibles", styles['Normal']))
        
        return elements
    
    def _generar_seccion_analisis(self, styles, heading_style, pedidos):
        """Genera la sección de análisis y conclusiones"""
        elements = []
        elements.append(Paragraph("Análisis y Conclusiones", heading_style))
        
        # Estadísticas
        total_pedidos = pedidos.count()
        total_ventas = pedidos.aggregate(Sum('total'))['total__sum'] or Decimal('0')
        
        # Días del período
        dias_periodo = (self.fecha_fin - self.fecha_inicio).days + 1
        ventas_diarias_promedio = total_ventas / dias_periodo if dias_periodo > 0 else Decimal('0')
        
        # Métodos de pago
        metodos_pago = pedidos.values('metodo_pago').annotate(
            cantidad=Count('id'),
            total=Sum('total')
        ).order_by('-total')
        
        elementos_analisis = [
            f"<b>Período de análisis:</b> {dias_periodo} días",
            f"<b>Total de pedidos procesados:</b> {total_pedidos} pedidos",
            f"<b>Total de ventas:</b> ${total_ventas:,.2f}",
            f"<b>Venta diaria promedio:</b> ${ventas_diarias_promedio:,.2f}",
            f"<b>Ticket promedio:</b> ${(total_ventas/total_pedidos if total_pedidos > 0 else 0):,.2f}",
        ]
        
        for item in elementos_analisis:
            elements.append(Paragraph(item, styles['Normal']))
            elements.append(Spacer(1, 8))
        
        # Métodos de pago
        if metodos_pago:
            elements.append(Spacer(1, 15))
            elements.append(Paragraph("Desglose por Método de Pago:", heading_style))
            
            datos_metodos = [['Método', 'Cantidad', 'Total']]
            for metodo in metodos_pago:
                datos_metodos.append([
                    str(metodo['metodo_pago']),
                    str(metodo['cantidad']),
                    f"${metodo['total']:,.2f}"
                ])
            
            tabla_metodos = Table(datos_metodos, colWidths=[2.5*inch, 1.5*inch, 2*inch])
            tabla_metodos.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(tabla_metodos)
        
        return elements


class GeneradorExportacionAnalisisVentas:
    """Clase para generar reportes profesionales de análisis de ventas en PDF"""
    
    def __init__(self, series_data, by_category, by_product, compare_data=None, period='monthly'):
        self.series_data = series_data
        self.by_category = by_category
        self.by_product = by_product
        self.compare_data = compare_data
        self.period = period
        self.buffer = BytesIO()
        
    def generar_pdf(self):
        """Genera el PDF del análisis de ventas y retorna el buffer"""
        doc = SimpleDocTemplate(self.buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
        elements = []
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#555555'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        # Encabezado
        titulo = Paragraph("ANÁLISIS DE VENTAS - REPORTE EXPORTADO", title_style)
        elements.append(titulo)
        
        fecha_generacion = f"Generado: {datetime.now().strftime('%d de %B de %Y - %H:%M:%S')}"
        periodo_texto = f"Período: {self._get_period_label()}"
        elementos_info = [fecha_generacion, periodo_texto]
        elements.append(Paragraph(" | ".join(elementos_info), subtitle_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Métricas principales
        elements.extend(self._generar_metricas_principales(styles, heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Series por período
        if self.series_data:
            elements.extend(self._generar_seccion_series(styles, heading_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # Ventas por categoría
        if self.by_category:
            elements.extend(self._generar_seccion_categoria(styles, heading_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # Productos más vendidos
        if self.by_product:
            elements.extend(self._generar_seccion_productos(styles, heading_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # Comparativa si aplica
        if self.compare_data:
            elements.extend(self._generar_seccion_comparativa(styles, heading_style))
        
        # Construir PDF
        doc.build(elements)
        self.buffer.seek(0)
        return self.buffer
    
    def _get_period_label(self):
        """Retorna etiqueta del período"""
        labels = {
            'daily': 'Diario',
            'weekly': 'Semanal',
            'monthly': 'Mensual',
            'yearly': 'Anual'
        }
        return labels.get(self.period, 'Período desconocido')
    
    def _generar_metricas_principales(self, styles, heading_style):
        """Genera sección de métricas principales"""
        elements = []
        
        total_ventas = sum(item['total'] for item in self.series_data) if self.series_data else 0
        cantidad_registros = len(self.series_data) if self.series_data else 0
        
        # Tabla de métricas
        datos_metricas = [
            ['MÉTRICA', 'VALOR'],
            ['Total de Ventas', f'${total_ventas:,.2f}'],
            ['Cantidad de Registros', str(cantidad_registros)],
            ['Promedio por Período', f'${total_ventas / cantidad_registros:,.2f}' if cantidad_registros > 0 else '$0.00']
        ]
        
        if self.compare_data:
            datos_metricas.append(['Ventas Período Actual', f"${self.compare_data['current']:,.2f}"])
            datos_metricas.append(['Ventas Período Anterior', f"${self.compare_data['previous']:,.2f}"])
            if self.compare_data['previous'] > 0:
                crecimiento = ((self.compare_data['current'] - self.compare_data['previous']) / self.compare_data['previous'] * 100)
                datos_metricas.append(['Crecimiento %', f'{crecimiento:+.2f}%'])
        
        tabla_metricas = Table(datos_metricas, colWidths=[3*inch, 3*inch])
        tabla_metricas.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f0f0')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
        ]))
        
        elements.append(tabla_metricas)
        return elements
    
    def _generar_seccion_series(self, styles, heading_style):
        """Genera sección de datos por período"""
        elements = []
        elements.append(Paragraph(f"Ventas por {self._get_period_label()}", heading_style))
        
        # Preparar datos para tabla (máximo 15 registros para no saturar)
        datos_series = [['Período', 'Total Ventas']]
        for item in self.series_data[-15:]:
            periodo_str = item['period'].split('T')[0] if isinstance(item['period'], str) else str(item['period'])
            datos_series.append([periodo_str, f"${item['total']:,.2f}"])
        
        tabla_series = Table(datos_series, colWidths=[3*inch, 3*inch])
        tabla_series.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f0f0')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
        ]))
        
        elements.append(tabla_series)
        return elements
    
    def _generar_seccion_categoria(self, styles, heading_style):
        """Genera sección de ventas por categoría"""
        elements = []
        elements.append(Paragraph("Ventas por Categoría", heading_style))
        
        # Calcular total para porcentajes
        total_categoria = sum(item['total'] for item in self.by_category)
        
        # Preparar datos
        datos_categoria = [['Categoría', 'Total Ventas', 'Porcentaje']]
        for item in self.by_category:
            porcentaje = (item['total'] / total_categoria * 100) if total_categoria > 0 else 0
            datos_categoria.append([
                item['categoria'],
                f"${item['total']:,.2f}",
                f"{porcentaje:.1f}%"
            ])
        
        tabla_categoria = Table(datos_categoria, colWidths=[2.5*inch, 2*inch, 1.5*inch])
        tabla_categoria.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f0f0')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
        ]))
        
        elements.append(tabla_categoria)
        return elements
    
    def _generar_seccion_productos(self, styles, heading_style):
        """Genera sección de productos más vendidos"""
        elements = []
        elements.append(Paragraph("Productos Más Vendidos", heading_style))
        
        # Calcular total para porcentajes
        total_productos = sum(item['total'] for item in self.by_product)
        
        # Preparar datos (máximo 15)
        datos_productos = [['Producto', 'Total Ventas', 'Porcentaje']]
        for item in self.by_product[:15]:
            porcentaje = (item['total'] / total_productos * 100) if total_productos > 0 else 0
            datos_productos.append([
                item['producto'][:50],  # Truncar nombre si es muy largo
                f"${item['total']:,.2f}",
                f"{porcentaje:.1f}%"
            ])
        
        tabla_productos = Table(datos_productos, colWidths=[2.5*inch, 2*inch, 1.5*inch])
        tabla_productos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f0f0')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
        ]))
        
        elements.append(tabla_productos)
        return elements
    
    def _generar_seccion_comparativa(self, styles, heading_style):
        """Genera sección de comparativa entre períodos"""
        elements = []
        elements.append(Paragraph("Comparativa de Períodos", heading_style))
        
        current = self.compare_data['current']
        previous = self.compare_data['previous']
        diferencia = current - previous
        crecimiento_pct = (diferencia / previous * 100) if previous > 0 else 0
        
        datos_comparativa = [
            ['Métrica', 'Período Actual', 'Período Anterior', 'Diferencia'],
            [
                'Ventas Totales',
                f'${current:,.2f}',
                f'${previous:,.2f}',
                f'${diferencia:+,.2f} ({crecimiento_pct:+.1f}%)'
            ]
        ]
        
        tabla_comparativa = Table(datos_comparativa, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        tabla_comparativa.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f0f0')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc'))
        ]))
        
        elements.append(tabla_comparativa)
        return elements

