/**
 * Servicio de Email
 * Elixir - Sistema de Botillería
 * 
 * NOTA: Los emails ahora se envían desde el backend usando MailerSend.
 * Este servicio solo existe para mantener compatibilidad con el código existente.
 */

/**
 * Envía email de confirmación cuando el cliente hace un pedido
 * (El backend ya envía este email con MailerSend)
 */
export const enviarEmailConfirmacionPedido = async (datosPedido) => {
  console.log('📧 Email de confirmación será enviado por el backend (MailerSend)');
  return { success: true, message: 'Email enviado por backend' };
};

/**
 * Envía email cuando el pedido es entregado
 * (El backend ya envía este email con MailerSend)
 */
export const enviarEmailPedidoEntregado = async (datosPedido) => {
  console.log('📧 Email de entrega será enviado por el backend (MailerSend)');
  return { success: true, message: 'Email enviado por backend' };
};

export default {
  enviarEmailConfirmacionPedido,
  enviarEmailPedidoEntregado
};
