# 📧 Configuración de EmailJS para Elixir

## Paso 1: Crear cuenta en EmailJS

1. Ve a [https://www.emailjs.com/](https://www.emailjs.com/)
2. Crea una cuenta gratuita (200 emails/mes gratis)

---

## Paso 2: Conectar servicio de email (Gmail SMTP)

1. En el dashboard, ve a **Email Services** → **Add New Service**
2. Selecciona **Gmail** (o "Personal Email Service" para SMTP manual)
3. Para Gmail SMTP:
   - **SMTP Server:** `smtp.gmail.com`
   - **Port:** `587`
   - **Username:** tu-correo@gmail.com
   - **Password:** [Contraseña de Aplicación de Google]

### Crear Contraseña de Aplicación de Google:
1. Ve a [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Selecciona "Correo" → "Otro (nombre personalizado)" → Escribe "EmailJS"
3. Copia la contraseña de 16 caracteres generada

4. **Guarda el Service ID** (ej: `service_abc123`)

---

## Paso 3: Crear los Templates

Ve a **Email Templates** → **Create New Template** para cada uno:

### Template 1: Confirmación de Pedido
- **Name:** `Confirmación de Pedido`
- **Template ID:** `template_confirmacion_pedido`
- Copia el contenido de `template_confirmacion_pedido.html`
- En el editor, pega el HTML en modo "Code"

### Template 2: Pedido Enviado
- **Name:** `Pedido Enviado`
- **Template ID:** `template_pedido_enviado`
- Copia el contenido de `template_pedido_enviado.html`

### Template 3: Pedido Entregado
- **Name:** `Pedido Entregado`
- **Template ID:** `template_pedido_entregado`
- Copia el contenido de `template_pedido_entregado.html`

---

## Paso 4: Obtener la Public Key

1. Ve a **Account** → **API Keys**
2. Copia tu **Public Key**

---

## Paso 5: Configurar en el proyecto

Edita el archivo `src/services/emailService.js` con tus credenciales:

```javascript
const EMAILJS_CONFIG = {
  serviceId: 'service_XXXXXX',      // Tu Service ID
  publicKey: 'XXXXXXXXXXXXXXXX',     // Tu Public Key
  templates: {
    confirmacionPedido: 'template_confirmacion_pedido',
    pedidoEnviado: 'template_pedido_enviado',
    pedidoEntregado: 'template_pedido_entregado'
  }
};
```

---

## Variables de cada Template

### template_confirmacion_pedido
| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `to_email` | Email del cliente | cliente@email.com |
| `to_name` | Nombre del cliente | Juan Pérez |
| `numero_pedido` | Número del pedido | PED-20251214-ABC123 |
| `productos` | Lista de productos | "2x Vino Tinto - $15.000\n1x Whisky - $25.000" |
| `subtotal` | Subtotal | 40.000 |
| `costo_envio` | Costo de envío | 3.000 |
| `total` | Total | 43.000 |
| `metodo_pago` | Método de pago | Transferencia |
| `direccion` | Dirección completa | Av. Principal 123, Santiago |
| `fecha_pedido` | Fecha del pedido | 14/12/2025 |

### template_pedido_enviado
| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `to_email` | Email del cliente | cliente@email.com |
| `to_name` | Nombre del cliente | Juan Pérez |
| `numero_pedido` | Número del pedido | PED-20251214-ABC123 |
| `fecha_envio` | Fecha de envío | 14/12/2025 |
| `fecha_estimada` | Fecha estimada entrega | 17/12/2025 |
| `direccion` | Dirección de entrega | Av. Principal 123, Santiago |
| `productos` | Resumen de productos | "2x Vino Tinto\n1x Whisky" |

### template_pedido_entregado
| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `to_email` | Email del cliente | cliente@email.com |
| `to_name` | Nombre del cliente | Juan Pérez |
| `numero_pedido` | Número del pedido | PED-20251214-ABC123 |
| `fecha_entrega` | Fecha de entrega | 17/12/2025 |

---

## Previsualización

Puedes previsualizar los templates abriendo los archivos `.html` directamente en tu navegador.

---

## Límites del Plan Gratuito

- 200 emails por mes
- 2 templates
- Para más, considera el plan de pago

---

## ¿Problemas?

- **Error 412 Gmail API:** Usa Gmail SMTP en vez de Gmail API
- **Emails no llegan:** Revisa la carpeta de spam
- **Error de autenticación:** Verifica que la contraseña de aplicación sea correcta

