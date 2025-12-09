# Generated migration - Allow null fecha_nacimiento

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0003_pedido_detallespedido'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cliente',
            name='fecha_nacimiento',
            field=models.DateField(blank=True, null=True),
        ),
    ]
