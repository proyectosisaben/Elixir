# 📦 Guía: Edición de Productos en el Catálogo

## 🎯 ¿Qué es esto?

Los **vendedores y admins** ahora pueden editar directamente la información de los productos en el catálogo sin tocar código. Simplemente haz clic en el ícono de editar y cambia lo que necesites.

---

## 🚀 Cómo editar productos

### Paso 1: Inicia sesión
- Ve a `/login`
- Entra con una cuenta de **vendedor** o **admin_sistema**

### Paso 2: Ve al catálogo
- Haz clic en "Catálogo" en el navbar
- O ve a `/catalogo`

### Paso 3: Busca el producto
- Selecciona la categoría deseada
- Busca el producto que quieres editar

### Paso 4: Haz clic en el ícono de editar
- En la esquina **superior derecha** de cada tarjeta de producto, verás un ícono **✏️**
- **Solo los vendedores y admins ven este ícono**
- Haz clic para abrir el modal de edición

### Paso 5: Modifica los datos
En el modal puedes cambiar:

| Campo | Descripción | Requerido |
|-------|-------------|-----------|
| **Nombre** | Nombre del producto | ✅ Sí |
| **Descripción** | Descripción detallada | ❌ Opcional |
| **Precio** | Precio en CLP | ✅ Sí |
| **Stock** | Cantidad disponible | ❌ Opcional |
| **URL de Imagen** | Link a la foto del producto | ❌ Opcional |

### Paso 6: Guarda los cambios
- Haz clic en el botón **"Guardar Cambios"**
- Se mostrará un mensaje confirmando la actualización
- Los cambios se aplicarán inmediatamente en la página

---

## 🖼️ Cómo cambiar la imagen del producto

### Opción A: URL pública (Recomendado)
1. Sube tu imagen a un servicio como:
   - **Imgur**: https://imgur.com
   - **Cloudinary**: https://cloudinary.com
   - **Hosting personal**: Tu servidor web

2. Copia la URL completa (debe terminar en `.jpg`, `.png`, etc.)

3. Pega la URL en el campo **"URL de Imagen"** del formulario

4. Ejemplo de URL válida:
```
https://ejemplo.com/productos/vino-carmenere-2020.jpg
```

### Opción B: Base de datos (Requiere backend)
Si quieres subir imágenes directamente:
- Contacta al equipo de desarrollo
- Se necesita implementar un endpoint para subida de archivos

---

## 💾 ¿Dónde se guardan los cambios?

### Actualmente: localStorage
- Los cambios se guardan en el navegador local
- Se conservan entre sesiones en **este navegador**
- Si cambias de navegador o limpias cache, se pierden

### Permanentemente: Base de datos
Para guardar cambios permanentemente en la BD:

1. Abre `src/pages/CatalogoPorCategoria.jsx`
2. En la función `handleGuardarProducto()`, reemplaza:
```javascript
localStorage.setItem('productosEditados', JSON.stringify(productosActualizados));
```

Por una llamada a tu API:
```javascript
await fetch(`http://localhost:8000/api/productos/${productoEditado.id}/`, {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify(formData)
});
```

---

## 🔒 ¿Quién puede editar?

**Solo estos roles pueden ver el ícono de editar:**
- ✅ `vendedor`
- ✅ `admin_sistema`

**No pueden editar:**
- ❌ `cliente`
- ❌ `gerente`

---

## ✅ Validaciones

Cuando intentas guardar, el sistema valida:

| Validación | Estado |
|-----------|--------|
| Campo "Nombre" no vacío | ✅ Obligatorio |
| Campo "Precio" no vacío | ✅ Obligatorio |
| Precio es un número válido | ✅ Automático |
| Stock es un número entero | ✅ Automático |
| URL de imagen válida | ❌ Sin validación |

---

## 🎨 Apariencia del producto editado

Después de guardar, el producto se actualiza:
- La tarjeta refleja los nuevos valores
- La imagen se carga si la URL es válida
- El precio y stock se actualizan inmediatamente

---

## 🐛 Troubleshooting

### No veo el ícono de editar
**Solución:**
- Verifica que estés logueado como **vendedor** o **admin**
- Recarga la página (Ctrl+F5)
- Limpia el cache del navegador

### El modal no se abre
**Solución:**
- Revisa la consola del navegador (F12 → Console)
- Busca errores de JavaScript
- Intenta en otro navegador

### Los cambios no se guardan
**Solución:**
- Verifica que el campo "Nombre" y "Precio" no estén vacíos
- Recarga la página para ver si persisten
- Abre DevTools y revisa localStorage

### La imagen no carga
**Solución:**
- Verifica que la URL sea correcta
- Asegúrate que la imagen sea accesible públicamente
- Intenta con otra URL de imagen

---

## 📝 Ejemplo: Editar un Vino Carménère

**Original:**
```
Nombre: Vino Carménère 2020
Descripción: Vino tinto chileno de excelente calidad
Precio: $12,000
Stock: 50
Imagen: https://ejemplo.com/carmenerere-2020.jpg
```

**Después de editar:**
```
Nombre: Vino Carménère 2021 Premium
Descripción: Vino tinto chileno de excelente calidad. Nuevo vintage!
Precio: $14,500
Stock: 35
Imagen: https://ejemplo.com/carmenerere-2021-premium.jpg
```

---

## 🚀 Próximos pasos

1. ✅ **Ya implementado:** Editar información de productos
2. ✅ **Ya implementado:** Cambiar imágenes
3. 🔄 **Por hacer:** Upload de archivos (requiere backend)
4. 🔄 **Por hacer:** Historial de cambios
5. 🔄 **Por hacer:** Cambios en lote (múltiples productos)

---

## 📚 Archivos relacionados

```
src/pages/
  └── CatalogoPorCategoria.jsx  ← Edición de productos
  
src/styles/
  └── globals.css              ← Estilos y colores
```

---

**¿Preguntas?** Consulta la documentación del sistema o contacta al equipo de desarrollo.
