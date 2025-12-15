/**
 * Servicio de Email usando EmailJS
 * Elixir - Sistema de Botillería
 */

import emailjs from '@emailjs/browser';

// ============================================
// CONFIGURACIÓN EMAILJS
// ============================================
const EMAILJS_CONFIG = {
  serviceId: 'service_oj2wozf',
  publicKey: 'JZe-HKZ479Ob-CFDH',
  templates: {
    confirmacionPedido: 'template_confirmacion_pedido',
    pedidoEntregado: 'template_pedido_entregado'
  }
};

// Inicializar EmailJS
emailjs.init(EMAILJS_CONFIG.publicKey);

/**
 * Formatea los productos para el email
 */
const formatearProductos = (items) => {
  if (!items || !Array.isArray(items)) return 'Ver detalles en tu cuenta';
  return items.map(item => 
    `• ${item.cantidad}x ${item.nombre} - $${(item.precio_unitario || item.precio || 0).toLocaleString('es-CL')}`
  ).join('\n');
};

/**
 * Formatea una fecha a formato chileno
 */
const formatearFecha = (fecha) => {
  const date = fecha ? new Date(fecha) : new Date();
  return date.toLocaleDateString('es-CL', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
};

/**
 * Envía email de confirmación cuando el cliente hace un pedido
 */
export const enviarEmailConfirmacionPedido = async (datosPedido) => {
  try {
    const {
      clienteEmail,
      clienteNombre,
      numeroPedido,
      items,
      subtotal,
      costoEnvio,
      total,
      metodoPago,
      direccion,
      fechaPedido
    } = datosPedido;

    const templateParams = {
      to_email: clienteEmail,
      to_name: clienteNombre || clienteEmail.split('@')[0],
      numero_pedido: numeroPedido,
      productos: formatearProductos(items),
      subtotal: (subtotal || 0).toLocaleString('es-CL'),
      costo_envio: (costoEnvio || 0).toLocaleString('es-CL'),
      total: (total || 0).toLocaleString('es-CL'),
      metodo_pago: metodoPago || 'Transferencia',
      direccion: direccion || 'Por confirmar',
      fecha_pedido: formatearFecha(fechaPedido)
    };

    const response = await emailjs.send(
      EMAILJS_CONFIG.serviceId,
      EMAILJS_CONFIG.templates.confirmacionPedido,
      templateParams
    );

    console.log('✅ Email de confirmación enviado:', response);
    return { success: true, response };
  } catch (error) {
    console.error('❌ Error enviando email de confirmación:', error);
    return { success: false, error };
  }
};

/**
 * Envía email cuando el pedido es entregado
 */
export const enviarEmailPedidoEntregado = async (datosPedido) => {
  try {
    const {
      clienteEmail,
      clienteNombre,
      numeroPedido,
      fechaEntrega
    } = datosPedido;

    const templateParams = {
      to_email: clienteEmail,
      to_name: clienteNombre || clienteEmail.split('@')[0],
      numero_pedido: numeroPedido,
      fecha_entrega: formatearFecha(fechaEntrega || new Date())
    };

    const response = await emailjs.send(
      EMAILJS_CONFIG.serviceId,
      EMAILJS_CONFIG.templates.pedidoEntregado,
      templateParams
    );

    console.log('✅ Email de entrega enviado:', response);
    return { success: true, response };
  } catch (error) {
    console.error('❌ Error enviando email de entrega:', error);
    return { success: false, error };
  }
};

export default {
  enviarEmailConfirmacionPedido,
  enviarEmailPedidoEntregado
};

