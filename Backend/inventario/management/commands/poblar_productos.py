from django.core.management.base import BaseCommand
from inventario.models import Categoria, Proveedor, Producto
from django.db import connection

class Command(BaseCommand):
    help = 'Poblar base de datos con productos chilenos reales'

    def handle(self, *args, **options):
        # Limpiar datos existentes usando SQL directo para evitar problemas de foreign keys
        with connection.cursor() as cursor:
            cursor.execute('SET FOREIGN_KEY_CHECKS=0')
            #cursor.execute('TRUNCATE TABLE inventario_carritoitem')
            cursor.execute('TRUNCATE TABLE inventario_producto')
            cursor.execute('TRUNCATE TABLE inventario_productoimagen')
            cursor.execute('TRUNCATE TABLE inventario_categoria')
            cursor.execute('TRUNCATE TABLE inventario_proveedor')
            cursor.execute('SET FOREIGN_KEY_CHECKS=1')

        # Crear Categorías
        vinos = Categoria.objects.create(
            nombre="Vinos",
            descripcion="Vinos tintos, blancos y rosé de valles chilenos",
            activa=True
        )
        
        cervezas = Categoria.objects.create(
            nombre="Cervezas",
            descripcion="Cervezas nacionales e importadas",
            activa=True
        )
        
        piscos = Categoria.objects.create(
            nombre="Piscos",
            descripcion="Piscos chilenos premium y reservados",
            activa=True
        )
        
        whiskys = Categoria.objects.create(
            nombre="Whiskys",
            descripcion="Whiskys escoceses, americanos y premium",
            activa=True
        )
        
        rones = Categoria.objects.create(
            nombre="Ron",
            descripcion="Rones añejos, blancos y especiales",
            activa=True
        )

        # Crear Proveedores
        vinos_del_sur = Proveedor.objects.create(
            nombre="Viñas Chilenas SA",
            rut="76543210-9",
            email="ventas@vinaschilenas.cl",
            telefono="+56912345678",
            direccion="Santiago, Chile",
            activo=True
        )
        
        distribuidora_licores = Proveedor.objects.create(
            nombre="Distribuidora Licores Premium",
            rut="87654321-0", 
            email="contacto@licores.cl",
            telefono="+56987654321",
            direccion="Valparaíso, Chile",
            activo=True
        )
        
        pisquera_nacional = Proveedor.objects.create(
            nombre="Pisquera Nacional Chile",
            rut="98765432-1",
            email="ventas@pisqueranacional.cl", 
            telefono="+56976543210",
            direccion="La Serena, Chile",
            activo=True
        )

        # ==========================================
        # VINOS CHILENOS (Precios reales 2024)
        # ==========================================
        
        productos_vinos = [
            {
                'nombre': 'Vino Santa Rita 120 Cabernet Sauvignon',
                'sku': 'VIN-001',
                'precio': 4990,
                'costo': 3500,
                'stock': 45,
                'descripcion': 'Vino tinto reserva de uvas Cabernet Sauvignon del Valle Central. Color rojo intenso con aromas frutales.',
                'categoria': vinos,
                'proveedor': vinos_del_sur,
                'activo': True
            },
            {
                'nombre': 'Vino Casillero del Diablo Carmenere',
                'sku': 'VIN-002', 
                'precio': 5990,
                'costo': 4200,
                'stock': 32,
                'descripcion': 'Vino tinto premium con notas especiadas y frutales. Cepa emblema de Chile.',
                'categoria': vinos,
                'proveedor': vinos_del_sur,
                'activo': True
            },
            {
                'nombre': 'Vino Concha y Toro Frontera Merlot',
                'sku': 'VIN-003',
                'precio': 3790,
                'costo': 2650,
                'stock': 68,
                'descripcion': 'Vino tinto suave y frutal, ideal para acompañar carnes rojas.',
                'categoria': vinos,
                'proveedor': vinos_del_sur,
                'activo': True
            },
            {
                'nombre': 'Vino Alma de Chile Reserva Especial',
                'sku': 'VIN-004',
                'precio': 9990,
                'costo': 7000,
                'stock': 25,
                'descripcion': 'Vino premium edicion limitada, blend de cepas seleccionadas.',
                'categoria': vinos,
                'proveedor': vinos_del_sur,
                'activo': True
            },
            {
                'nombre': 'Vino Sol de Chile Sauvignon Blanc',
                'sku': 'VIN-005', 
                'precio': 5390,
                'costo': 3770,
                'stock': 38,
                'descripcion': 'Vino blanco fresco y citrico del Valle de Casablanca.',
                'categoria': vinos,
                'proveedor': vinos_del_sur,
                'activo': True
            }
        ]

        # ==========================================
        # CERVEZAS CHILENAS (Precios reales 2024)
        # ==========================================
        
        productos_cervezas = [
            {
                'nombre': 'Cerveza Cristal Lata 350ml',
                'sku': 'CER-001',
                'precio': 1200,
                'costo': 850,
                'stock': 180,
                'descripcion': 'Cerveza lager chilena clasica, refrescante y equilibrada.',
                'categoria': cervezas,
                'proveedor': distribuidora_licores,
                'activo': True
            },
            {
                'nombre': 'Cerveza Escudo Botella 330ml',
                'sku': 'CER-002',
                'precio': 1350,
                'costo': 950,
                'stock': 150,
                'descripcion': 'Cerveza lager premium chilena con malta seleccionada.',
                'categoria': cervezas,
                'proveedor': distribuidora_licores,
                'activo': True
            },
            {
                'nombre': 'Cerveza Kunstmann Valdivia Pale Lager',
                'sku': 'CER-003',
                'precio': 2190,
                'costo': 1530,
                'stock': 95,
                'descripcion': 'Cerveza artesanal alemana elaborada en Chile desde 1851.',
                'categoria': cervezas,
                'proveedor': distribuidora_licores,
                'activo': True
            },
            {
                'nombre': 'Cerveza Heineken Lata 500ml',
                'sku': 'CER-004',
                'precio': 1890,
                'costo': 1320,
                'stock': 120,
                'descripcion': 'Cerveza premium importada, sabor unico y refrescante.',
                'categoria': cervezas,
                'proveedor': distribuidora_licores,
                'activo': True
            },
            {
                'nombre': 'Cerveza Bear Beer Pack 12 Latas',
                'sku': 'CER-005',
                'precio': 7990,
                'costo': 5600,
                'stock': 45,
                'descripcion': 'Pack familiar de cerveza lager 5 grados, ideal para compartir.',
                'categoria': cervezas,
                'proveedor': distribuidora_licores,
                'activo': True
            }
        ]

        # ==========================================
        # PISCOS CHILENOS (Precios reales 2024)
        # ==========================================
        
        productos_piscos = [
            {
                'nombre': 'Pisco Capel 35 grados Botella 750ml',
                'sku': 'PIS-001',
                'precio': 7500,
                'costo': 5250,
                'stock': 75,
                'descripcion': 'Pisco tradicional chileno del Valle del Elqui, suave y aromatico.',
                'categoria': piscos,
                'proveedor': pisquera_nacional,
                'activo': True
            },
            {
                'nombre': 'Pisco Alto del Carmen 40 grados 750ml',
                'sku': 'PIS-002',
                'precio': 11990,
                'costo': 8400,
                'stock': 42,
                'descripcion': 'Pisco premium transparente con notas florales y frutales.',
                'categoria': piscos,
                'proveedor': pisquera_nacional,
                'activo': True
            },
            {
                'nombre': 'Pisco Mistral Especial 35 grados 750ml',
                'sku': 'PIS-003',
                'precio': 8990,
                'costo': 6300,
                'stock': 58,
                'descripcion': 'Pisco de uvas moscatel, ideal para pisco sour y cocteles.',
                'categoria': piscos,
                'proveedor': pisquera_nacional,
                'activo': True
            },
            {
                'nombre': 'Pisco Bou Barroeta Cofradia 40 grados',
                'sku': 'PIS-004',
                'precio': 33790,
                'costo': 23650,
                'stock': 18,
                'descripcion': 'Pisco ultra premium, ganador mejor pisco del mundo 2024.',
                'categoria': piscos,
                'proveedor': pisquera_nacional,
                'activo': True
            },
            {
                'nombre': 'Pisco Tres Erres 40 grados 1 Litro',
                'sku': 'PIS-005',
                'precio': 5990,
                'costo': 4200,
                'stock': 85,
                'descripcion': 'Pisco familiar de excelente relacion precio-calidad.',
                'categoria': piscos,
                'proveedor': pisquera_nacional,
                'activo': True
            }
        ]

        # ==========================================
        # WHISKYS (Precios reales 2024)
        # ==========================================
        
        productos_whiskys = [
            {
                'nombre': 'Whisky Johnnie Walker Red Label',
                'sku': 'WHI-001',
                'precio': 18900,
                'costo': 13230,
                'stock': 32,
                'descripcion': 'Whisky escoces blend, el mas vendido del mundo.',
                'categoria': whiskys,
                'proveedor': distribuidora_licores,
                'activo': True
            },
            {
                'nombre': 'Whisky Johnnie Walker Black Label',
                'sku': 'WHI-002',
                'precio': 25990,
                'costo': 18200,
                'stock': 28,
                'descripcion': 'Whisky escoces premium 12 años, sabor complejo y suave.',
                'categoria': whiskys,
                'proveedor': distribuidora_licores,
                'activo': True
            },
            {
                'nombre': 'Whisky Jack Daniels Old No.7',
                'sku': 'WHI-003',
                'precio': 24990,
                'costo': 17500,
                'stock': 24,
                'descripcion': 'Whisky Tennessee americano, suave y caracteristico.',
                'categoria': whiskys,
                'proveedor': distribuidora_licores,
                'activo': True
            },
            {
                'nombre': 'Whisky Ballantines Finest',
                'sku': 'WHI-004',
                'precio': 9990,
                'costo': 7000,
                'stock': 45,
                'descripcion': 'Whisky escoces blend accesible y de calidad.',
                'categoria': whiskys,
                'proveedor': distribuidora_licores,
                'activo': True
            },
            {
                'nombre': 'Whisky Chivas Regal 12 Años',
                'sku': 'WHI-005',
                'precio': 49900,
                'costo': 35000,
                'stock': 16,
                'descripcion': 'Whisky escoces premium luxury, añejado 12 años.',
                'categoria': whiskys,
                'proveedor': distribuidora_licores,
                'activo': True
            }
        ]

        # ==========================================
        # RONES (Precios reales 2024)
        # ==========================================
        
        productos_rones = [
            {
                'nombre': 'Ron Bacardi Carta Blanca 750ml',
                'sku': 'RON-001',
                'precio': 7790,
                'costo': 5450,
                'stock': 65,
                'descripcion': 'Ron blanco premium, ideal para mojitos y cocteles.',
                'categoria': rones,
                'proveedor': distribuidora_licores,
                'activo': True
            },
            {
                'nombre': 'Ron Cabo Viejo Dorado 750ml',
                'sku': 'RON-002',
                'precio': 5490,
                'costo': 3840,
                'stock': 78,
                'descripcion': 'Ron añejo chileno suave y aromatico.',
                'categoria': rones,
                'proveedor': distribuidora_licores,
                'activo': True
            },
            {
                'nombre': 'Ron Havana Club Añejo Blanco',
                'sku': 'RON-003',
                'precio': 8990,
                'costo': 6300,
                'stock': 42,
                'descripcion': 'Ron cubano autentico, tradicion y calidad.',
                'categoria': rones,
                'proveedor': distribuidora_licores,
                'activo': True
            },
            {
                'nombre': 'Ron Matusalem 7 Años 700ml',
                'sku': 'RON-004',
                'precio': 14990,
                'costo': 10500,
                'stock': 28,
                'descripcion': 'Ron premium añejado 7 años, sabor complejo.',
                'categoria': rones,
                'proveedor': distribuidora_licores,
                'activo': True
            },
            {
                'nombre': 'Ron Maddero Blanco 750ml',
                'sku': 'RON-005',
                'precio': 4990,
                'costo': 3500,
                'stock': 95,
                'descripcion': 'Ron blanco chileno, excelente relacion precio-calidad.',
                'categoria': rones,
                'proveedor': distribuidora_licores,
                'activo': True
            }
        ]

        # Crear productos en la base de datos
        todos_productos = productos_vinos + productos_cervezas + productos_piscos + productos_whiskys + productos_rones

        for producto_data in todos_productos:
            Producto.objects.create(**producto_data)

        self.stdout.write(
            self.style.SUCCESS(
                f'¡Éxito! Se crearon {len(todos_productos)} productos chilenos con precios reales 2024'
            )
        )
