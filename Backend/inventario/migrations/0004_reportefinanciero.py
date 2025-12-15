# Generated manually for HU 7 - Financial Reports

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0003_producto_creador_producto_imagen_url_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ReporteFinanciero',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_reporte', models.CharField(choices=[('ventas_general', 'Ventas Generales'), ('productos_top', 'Productos Más Vendidos'), ('ingresos_categoria', 'Ingresos por Categoría'), ('comparativa_periodos', 'Comparativa entre Períodos'), ('resumen_completo', 'Resumen Completo')], default='resumen_completo', max_length=20)),
                ('fecha_inicio', models.DateField()),
                ('fecha_fin', models.DateField()),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('archivo_pdf', models.FileField(blank=True, null=True, upload_to='reportes/')),
                ('datos_json', models.JSONField(blank=True, default=dict)),
                ('estado', models.CharField(choices=[('pendiente', 'Pendiente'), ('procesando', 'Procesando'), ('generado', 'Generado'), ('enviado_email', 'Enviado por Email'), ('error', 'Error')], default='generado', max_length=20)),
                ('emails_destino', models.TextField(blank=True, help_text='Emails separados por comas o JSON array')),
                ('frecuencia_automatica', models.CharField(choices=[('unico', 'Único'), ('diario', 'Diario'), ('semanal', 'Semanal'), ('mensual', 'Mensual')], default='unico', max_length=20)),
                ('activo', models.BooleanField(default=False, help_text='¿Generar automáticamente?')),
                ('categoria', models.ForeignKey(blank=True, help_text='Categoría opcional para filtrar', null=True, on_delete=django.db.models.deletion.SET_NULL, to='inventario.categoria')),
                ('generador', models.ForeignKey(help_text='Usuario que generó el reporte', on_delete=django.db.models.deletion.PROTECT, related_name='reportes_generados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Reporte Financiero',
                'verbose_name_plural': 'Reportes Financieros',
                'ordering': ['-fecha_creacion'],
                'permissions': [('puede_generar_reportes', 'Puede generar reportes'), ('puede_ver_reportes', 'Puede ver reportes')],
            },
        ),
    ]
