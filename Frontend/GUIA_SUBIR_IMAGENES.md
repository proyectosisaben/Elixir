# 🖼️ Guía: Subir Fotos en el Directorio del Proyecto

## 📁 ¿Dónde puedo guardar fotos?

Tienes **dos opciones principales**:

---

## Opción A: Carpeta `public/` del Proyecto (Recomendada para principiantes)

### ¿Cómo funciona?
- Las archivos en `public/` se sirven **directamente desde el servidor**
- Puedes acceder a ellos con URLs simples como: `http://localhost:5173/imagenes/mi-foto.jpg`

### Pasos:

#### 1️⃣ Crea la carpeta de imágenes
```powershell
# En PowerShell
cd C:\Users\basti\Downloads\Elixir\Frontend\PaginaWeb
New-Item -ItemType Directory -Path "public\imagenes" -Force
New-Item -ItemType Directory -Path "public\imagenes\productos" -Force
New-Item -ItemType Directory -Path "public\imagenes\sliders" -Force
```

Estructura resultante:
```
public/
  ├── imagenes/
  │   ├── productos/      ← Fotos de productos
  │   └── sliders/        ← Fotos del carrusel
```

#### 2️⃣ Copia tus imágenes
- Copia las fotos a:
  - `public/imagenes/productos/` - para productos del catálogo
  - `public/imagenes/sliders/` - para el carrusel principal

Ejemplo:
```
public/imagenes/productos/
  ├── vino-carmenerere.jpg
  ├── cerveza-kunstmann.jpg
  └── pisco-premium.jpg
```

#### 3️⃣ Usa las URLs en la aplicación

**Para productos en el catálogo:**
```javascript
// En CatalogoPorCategoria.jsx - al editar
imagen: "/imagenes/productos/vino-carmenerere.jpg"
```

**Para sliders:**
```javascript
// En Slider.jsx
slides = [
  {
    id: 1,
    title: "🍷 Vinos Premium",
    description: "...",
    color: "var(--primary-color)",
    imagen: "/imagenes/sliders/banner-vinos.jpg"  // NUEVO
  }
]
```

#### 4️⃣ Ventajas
✅ Fácil y rápido
✅ No requiere servidor externo
✅ Las imágenes se cargan localmente
✅ Funciona en desarrollo y producción

#### 5️⃣ Desventajas
❌ Las imágenes aumentan el tamaño del proyecto
❌ Si el servidor cae, las imágenes no se cargan
❌ Más lento con muchas imágenes grandes

---

## Opción B: Servicio en la Nube (Recomendado para producción)

### Servicios recomendados:

| Servicio | Ventajas | Desventajas | Costo |
|----------|----------|-------------|-------|
| **Imgur** | Simple, gratis | Comparte imágenes públicamente | Gratis |
| **Cloudinary** | CDN, optimización | Requiere cuenta | Gratis (10GB) |
| **Google Drive** | Integración | URLs complejas | Gratis |
| **AWS S3** | Profesional, escalable | Requiere configuración | Pago |

### Ejemplo con Imgur:

1. Ve a https://imgur.com
2. Sube tu imagen (no requiere cuenta)
3. Copia el enlace directo
4. Ejemplo de URL:
```
https://i.imgur.com/xAbC1234.jpg
```

5. Usa en tu formulario de edición:
```javascript
// En CatalogoPorCategoria.jsx
formData.imagen = "https://i.imgur.com/xAbC1234.jpg"
```

---

## Opción C: Backend Django (La mejor solución profesional)

### ¿Cómo funciona?
- Subir fotos **directamente desde el navegador** al servidor
- Las imágenes se guardan en `Backend/media/`
- Se sirven automáticamente en producción

### Implementación:

#### 1️⃣ Backend ya está listo!
En `Backend/settings.py`:
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

Estructura:
```
Backend/media/
  └── productos/
```

#### 2️⃣ Crear endpoint en Django para subida
En `Backend/inventario/views.py`:
```python
from django.core.files.storage import default_storage
from django.http import JsonResponse

@csrf_exempt
def subir_imagen(request):
    if request.method == 'POST' and request.FILES:
        archivo = request.FILES['imagen']
        
        # Guardar en media/productos/
        ruta = default_storage.save(
            f'productos/{archivo.name}',
            archivo
        )
        
        return JsonResponse({
            'success': True,
            'url': f'http://localhost:8000/media/{ruta}'
        })
    
    return JsonResponse({'success': False})
```

#### 3️⃣ Configurar URLs en Django
En `Backend/inventario/urls.py`:
```python
urlpatterns = [
    # ... otros paths
    path('subir-imagen/', subir_imagen, name='subir_imagen'),
]
```

#### 4️⃣ Actualizar el Frontend
En `src/pages/CatalogoPorCategoria.jsx`:
```javascript
const subirImagen = async (archivo) => {
  const formData = new FormData();
  formData.append('imagen', archivo);
  
  const response = await fetch('http://localhost:8000/api/subir-imagen/', {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  return data.url;
};
```

#### 5️⃣ Ventajas
✅ Subida directa desde el navegador
✅ Las imágenes se guardan en el servidor
✅ Escalable
✅ Profesional

#### 6️⃣ Desventajas
❌ Requiere configuración backend
❌ Requiere manejo de archivos
❌ Necesita espacio en disco

---

## 🎯 Recomendación: ¿Cuál uso?

### Para comenzar (desarrollo):
**→ Opción A (Carpeta public/)** 

Rápido, sin complicaciones.

### Para producción pequeña:
**→ Opción B (Imgur/Cloudinary)**

Fácil, escalable, sin mantenimiento.

### Para producción grande:
**→ Opción C (Backend + Media)**

Profesional, control total, integrado.

---

## 📝 Paso a paso: Subir imagen a `public/`

### 1. Crear carpeta en Windows:

```powershell
# Abrir PowerShell y ejecutar:
cd "C:\Users\basti\Downloads\Elixir\Frontend\PaginaWeb"
New-Item -ItemType Directory -Path "public\imagenes\productos"
New-Item -ItemType Directory -Path "public\imagenes\sliders"
```

### 2. Copiar tus imágenes
- Copia tus archivos `.jpg` o `.png` a:
  ```
  C:\Users\basti\Downloads\Elixir\Frontend\PaginaWeb\public\imagenes\productos\
  ```

### 3. Usar en la aplicación
Cuando edites un producto, usa:
```
/imagenes/productos/nombre-del-archivo.jpg
```

Ejemplo completo:
```javascript
// En modal de edición de CatalogoPorCategoria.jsx
formData.imagen = "/imagenes/productos/vino-2024.jpg"
```

### 4. Verificar en desarrollo
- Abre: `http://localhost:5173/imagenes/productos/vino-2024.jpg`
- Si ves la imagen, ¡está funcionando!

---

## 🚀 Comandos útiles

### Ver estructura actual:
```powershell
tree "C:\Users\basti\Downloads\Elixir\Frontend\PaginaWeb\public" /A
```

### Crear todas las carpetas de golpe:
```powershell
$carpetas = @(
    "public\imagenes\productos",
    "public\imagenes\sliders",
    "public\imagenes\categorias"
)
foreach ($carpeta in $carpetas) {
    New-Item -ItemType Directory -Path $carpeta -Force
}
```

---

## 🔍 Verificar que funciona

1. Coloca una imagen en `public/imagenes/productos/test.jpg`
2. Abre en el navegador:
```
http://localhost:5173/imagenes/productos/test.jpg
```
3. Si ves la imagen, ¡listo! Ya puedes usar esa URL en la aplicación

---

## 📚 Estructura final recomendada

```
Frontend/PaginaWeb/
├── public/
│   └── imagenes/
│       ├── productos/          ← Fotos de productos (1-2MB cada una)
│       │   ├── vino-1.jpg
│       │   ├── cerveza-1.jpg
│       │   └── pisco-1.jpg
│       ├── sliders/            ← Fotos del carrusel (2-3MB)
│       │   ├── slider-1.jpg
│       │   └── slider-2.jpg
│       └── categorias/         ← Iconos de categorías (100-500KB)
│           ├── vinos.jpg
│           └── cervezas.jpg
├── src/
│   ├── components/
│   ├── pages/
│   └── styles/
└── ...
```

---

## 💡 Tips

1. **Optimizar imágenes:** Usa [TinyPNG.com](https://tinypng.com) para reducir tamaño
2. **Nombres simples:** Evita caracteres especiales: `vino-blanco-2024.jpg` ✅
3. **Tamaño:** Máximo 3-5MB por imagen
4. **Formatos:** Usa `.jpg` o `.png`

---

**¿Necesitas ayuda?** Contacta al equipo de desarrollo o revisa la documentación oficial de Vite.
