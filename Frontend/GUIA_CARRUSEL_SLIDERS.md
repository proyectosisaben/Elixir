# 📸 Guía: Cómo Editar y Subir Fotos en el Carrusel

## 🎯 ¿Qué hemos implementado?

Ahora **vendedores y admin** pueden editar el contenido y las imágenes del carrusel directamente desde la página principal sin modificar código.

---

## 🚀 Cómo editar los Sliders (Carrusel)

### Paso 1: Inicia sesión como Vendedor o Admin
- Ve a `/login` y entra con una cuenta de **vendedor** o **admin_sistema**

### Paso 2: Ve a la página principal
- Haz clic en el logo "Elixir" o ve a `/`

### Paso 3: Edita los slides
- Verás que los **3 slides** del carrusel ahora son **clickeables**
- Cada slide mostrará: *"✏️ Haz clic para editar"*
- Haz clic en cualquier slide para abrir el modal de edición

### Paso 4: Edita el contenido
En el modal puedes cambiar:
- **Título**: Ejemplo: "🍷 Los Mejores Vinos Chilenos"
- **Descripción**: El texto descriptivo del slide

---

## 🖼️ ¿Cómo cambiar la imagen del carrusel?

### Opción A: Usar una URL de imagen (Recomendado)
1. En el formulario de edición del slide, **NO hay campo de imagen**
2. Los colores de fondo están predefinidos:
   - Slide 1: Azul (Vinos) - `var(--primary-color): #1a365d`
   - Slide 2: Verde (Cervezas) - `var(--success-color): #48bb78`
   - Slide 3: Rojo (Piscos) - `var(--danger-color): #f56565`

> **Nota**: Los slides funcionan con **colores sólidos**, no con imágenes. Si necesitas cambiar los colores, contacta a tu desarrollador.

---

## 📝 Estructura de almacenamiento

Los cambios se guardan en **localStorage** del navegador:
- Clave: `sliderElixir`
- Datos guardados: Array de objetos con título, descripción y color

### Ejemplo de datos guardados:
```json
[
  {
    "id": 1,
    "title": "🍷 Los Mejores Vinos Chilenos",
    "description": "Selección premium de los valles más reconocidos de Chile.",
    "color": "var(--primary-color)"
  }
]
```

---

## 🎨 Personalización avanzada

### Si quieres cambiar los colores del carrusel:

Los colores están definidos en `src/styles/globals.css`:

```css
:root {
    --primary-color: #1a365d;      /* Azul oscuro */
    --secondary-color: #d69e2e;    /* Naranja */
    --success-color: #48bb78;      /* Verde */
    --danger-color: #f56565;       /* Rojo */
    --warning-color: #b7791f;      /* Marrón */
}
```

**Para cambiar los colores del carrusel:**
1. Abre `src/components/Slider.jsx`
2. Busca el array de `slides` inicial
3. Cambia el valor de `color` para cada slide
4. Guarda y ejecuta `npm run build`

---

## 🔒 ¿Quién puede editar?

**Solo estos roles pueden editar:**
- ✅ `vendedor`
- ✅ `admin_sistema`

**No pueden editar:**
- ❌ `cliente`
- ❌ `gerente`

---

## 💾 Guardar cambios permanentemente (Base de datos)

Actualmente, los cambios se guardan en **localStorage** (solo en este navegador).

**Para guardar en la base de datos permanentemente:**

1. Abre `src/components/Slider.jsx`
2. En la función `handleGuardar()`, reemplaza:
```javascript
localStorage.setItem('sliderElixir', JSON.stringify(slidesActualizados));
```

Por una llamada a tu API:
```javascript
await fetch('http://localhost:8000/api/sliders/', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(slidesActualizados)
});
```

3. En el Backend, crea un endpoint para guardar los sliders

---

## 🐛 Troubleshooting

### Los cambios no se guardan
- Verifica que estés logueado como **vendedor** o **admin**
- Abre la consola del navegador (F12) y busca errores

### No puedo ver el botón de editar
- Asegúrate de estar logueado con la cuenta correcta
- Recarga la página (Ctrl+F5)

### Los colores se ven diferentes
- Verifica que `globals.css` esté cargando correctamente
- Abre DevTools y confirma que se aplican los estilos

---

## 📚 Archivos modificados

```
src/components/
  ├── Slider.jsx         ← Editable ahora, con modal
  └── Footer.jsx         ← Actualizado con colores CSS variables

src/pages/
  └── CatalogoPorCategoria.jsx  ← Vendedores pueden editar productos
```

---

## 🎓 Próximos pasos

Puedes también:
1. ✅ Editar **productos en el catálogo** (haz clic en el ícono ✏️ en cada producto)
2. ✅ El **footer** ahora usa la paleta de colores centralizada
3. Subir imágenes directamente (requiere backend adicional)

---

**¿Necesitas ayuda?** Contacta al equipo de desarrollo.
