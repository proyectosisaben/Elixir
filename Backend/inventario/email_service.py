"""
Servicio de correos electrónicos para notificaciones de pedidos
Elixir - Sistema de Botillería
Usa MailerSend para envío de emails
"""
import os
import json
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Configuración de MailerSend
MAILERSEND_API_KEY = os.environ.get('MAILERSEND_API_KEY', '')
MAILERSEND_API_URL = 'https://api.mailersend.com/v1/email'
MAILERSEND_TEMPLATE_CONFIRMACION = 'pr9084z6y1mlw63d'
MAILERSEND_FROM_EMAIL = 'info@trial-3z0vklo7zo0g7qrx.mlsender.net'  # Dominio de prueba de MailerSend
MAILERSEND_FROM_NAME = 'Elixir Botillería'


class EmailPedidoService:
    """Servicio para enviar notificaciones por email relacionadas con pedidos usando MailerSend"""
    
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://elixir-frontend-web.onrender.com')
    
    @staticmethod
    def _generar_codigo_seguimiento(pedido):
        """Genera un código de seguimiento basado en el número de pedido"""
        return f"SEG-{pedido.numero_pedido.replace('PED-', '')}"
    
    @staticmethod
    def _get_url_seguimiento(pedido):
        """Obtiene la URL de seguimiento del pedido"""
        codigo = EmailPedidoService._generar_codigo_seguimiento(pedido)
        return f"{EmailPedidoService.FRONTEND_URL}/seguimiento/{codigo}"
    
    @staticmethod
    def _obtener_detalles_pedido(pedido):
        """Obtiene los detalles del pedido para el email"""
        from .models import DetallesPedido
        return DetallesPedido.objects.filter(pedido=pedido).select_related('producto')
    
    @staticmethod
    def _enviar_email_mailersend(to_email, to_name, template_id, personalization_data):
        """
        Envía un email usando la API de MailerSend
        """
        if not MAILERSEND_API_KEY:
            logger.warning("MAILERSEND_API_KEY no configurada, email no enviado")
            return False
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {MAILERSEND_API_KEY}',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        payload = {
            'from': {
                'email': MAILERSEND_FROM_EMAIL,
                'name': MAILERSEND_FROM_NAME
            },
            'to': [
                {
                    'email': to_email,
                    'name': to_name
                }
            ],
            'template_id': template_id,
            'personalization': [
                {
                    'email': to_email,
                    'data': personalization_data
                }
            ]
        }
        
        try:
            response = requests.post(
                MAILERSEND_API_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email enviado exitosamente a {to_email}")
                return True
            else:
                logger.error(f"Error enviando email: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Excepción enviando email a {to_email}: {str(e)}")
            return False
    
    @staticmethod
    def enviar_confirmacion_pedido(pedido):
        """
        Envía email de confirmación cuando el cliente realiza un pedido.
        Se envía inmediatamente después de crear el pedido.
        """
        try:
            cliente = pedido.cliente
            user = cliente.user
            detalles = EmailPedidoService._obtener_detalles_pedido(pedido)
            
            # Construir lista de productos en formato texto
            productos_texto = ""
            for detalle in detalles:
                productos_texto += f"• {detalle.producto.nombre} x{detalle.cantidad} - ${detalle.subtotal}\n"
            
            if not productos_texto:
                productos_texto = "Sin productos"
            
            # Obtener dirección
            direccion_texto = "Retiro en tienda"
            if hasattr(pedido, 'direccion_envio') and pedido.direccion_envio:
                direccion = pedido.direccion_envio
                direccion_texto = f"{direccion.calle} {direccion.numero}, {direccion.comuna}, {direccion.region}"
            
            # Datos para personalización del template
            personalization_data = {
                'to_name': user.get_full_name() or user.username or user.email.split('@')[0],
                'numero_pedido': pedido.numero_pedido,
                'fecha_pedido': pedido.fecha_pedido.strftime('%d/%m/%Y a las %H:%M'),
                'productos': productos_texto,
                'subtotal': f"${pedido.subtotal:,.0f}".replace(',', '.'),
                'costo_envio': f"${pedido.costo_envio:,.0f}".replace(',', '.') if pedido.costo_envio else "Gratis",
                'total': f"${pedido.total:,.0f}".replace(',', '.'),
                'metodo_pago': pedido.get_metodo_pago_display() if hasattr(pedido, 'get_metodo_pago_display') else pedido.metodo_pago,
                'direccion': direccion_texto
            }
            
            to_name = personalization_data['to_name']
            
            result = EmailPedidoService._enviar_email_mailersend(
                to_email=user.email,
                to_name=to_name,
                template_id=MAILERSEND_TEMPLATE_CONFIRMACION,
                personalization_data=personalization_data
            )
            
            if result:
                logger.info(f"Email de confirmación enviado para pedido {pedido.numero_pedido} a {user.email}")
            return result
            
        except Exception as e:
            logger.error(f"Error enviando email de confirmación para pedido {pedido.numero_pedido}: {str(e)}")
            return False
    
    @staticmethod
    def enviar_notificacion_pago_confirmado(pedido):
        """Envía email cuando el vendedor confirma el pago del pedido."""
        # Por ahora solo usamos el template de confirmación
        return EmailPedidoService.enviar_confirmacion_pedido(pedido)
    
    @staticmethod
    def enviar_notificacion_en_preparacion(pedido):
        """Envía email cuando el pedido entra en preparación."""
        return EmailPedidoService.enviar_confirmacion_pedido(pedido)
    
    @staticmethod
    def enviar_notificacion_enviado(pedido):
        """Envía email cuando el vendedor confirma el envío del pedido."""
        return EmailPedidoService.enviar_confirmacion_pedido(pedido)
    
    @staticmethod
    def enviar_notificacion_entregado(pedido):
        """Envía email cuando el pedido es marcado como entregado."""
        return EmailPedidoService.enviar_confirmacion_pedido(pedido)
    
    @staticmethod
    def enviar_notificacion_por_estado(pedido, estado_anterior, estado_nuevo):
        """
        Método principal que determina qué email enviar basado en el cambio de estado.
        """
        emails_enviados = []
        
        if estado_nuevo == 'pagado' and estado_anterior == 'pendiente':
            if EmailPedidoService.enviar_notificacion_pago_confirmado(pedido):
                emails_enviados.append('pago_confirmado')
                
        elif estado_nuevo == 'en_preparacion':
            if EmailPedidoService.enviar_notificacion_en_preparacion(pedido):
                emails_enviados.append('en_preparacion')
                
        elif estado_nuevo == 'enviado':
            if EmailPedidoService.enviar_notificacion_enviado(pedido):
                emails_enviados.append('enviado')
                
        elif estado_nuevo == 'entregado':
            if EmailPedidoService.enviar_notificacion_entregado(pedido):
                emails_enviados.append('entregado')
        
        return emails_enviados
