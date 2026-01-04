"""
Servicio de correos electrónicos para notificaciones de pedidos
Elixir - Sistema de Botillería
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class EmailPedidoService:
    """Servicio para enviar notificaciones por email relacionadas con pedidos"""
    
    FRONTEND_URL = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
    
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
    def enviar_confirmacion_pedido(pedido):
        """
        Envía email de confirmación cuando el cliente realiza un pedido.
        Se envía inmediatamente después de crear el pedido.
        """
        try:
            cliente = pedido.cliente
            user = cliente.user
            detalles = EmailPedidoService._obtener_detalles_pedido(pedido)
            
            contexto = {
                'cliente_nombre': user.get_full_name() or user.username or user.email,
                'numero_pedido': pedido.numero_pedido,
                'codigo_seguimiento': EmailPedidoService._generar_codigo_seguimiento(pedido),
                'detalles': detalles,
                'total': pedido.total,
                'subtotal': pedido.subtotal,
                'descuento': pedido.descuento,
                'costo_envio': pedido.costo_envio,
                'fecha_pedido': pedido.fecha_pedido.strftime('%d/%m/%Y a las %H:%M'),
                'url_seguimiento': EmailPedidoService._get_url_seguimiento(pedido),
                'metodo_pago': pedido.get_metodo_pago_display(),
            }
            
            # Agregar dirección si existe
            if pedido.direccion_envio:
                direccion = pedido.direccion_envio
                contexto['direccion_envio'] = f"{direccion.calle} {direccion.numero}, {direccion.comuna}, {direccion.region}"
            
            # Renderizar template HTML
            html_content = render_to_string('emails/confirmacion_pedido.html', contexto)
            
            # Crear mensaje de texto plano alternativo
            texto_plano = f"""
Hola {contexto['cliente_nombre']},

¡Gracias por tu compra en Elixir!

Tu pedido {pedido.numero_pedido} ha sido recibido correctamente.

Código de seguimiento: {contexto['codigo_seguimiento']}

Total: ${pedido.total}

Puedes hacer seguimiento de tu pedido en: {contexto['url_seguimiento']}

Gracias por confiar en nosotros.

Equipo Elixir
            """
            
            # Enviar email
            email = EmailMultiAlternatives(
                subject=f'✅ Pedido {pedido.numero_pedido} Confirmado - Elixir',
                body=texto_plano,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            logger.info(f"Email de confirmación enviado para pedido {pedido.numero_pedido} a {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email de confirmación para pedido {pedido.numero_pedido}: {str(e)}")
            return False
    
    @staticmethod
    def enviar_notificacion_pago_confirmado(pedido):
        """
        Envía email cuando el vendedor confirma el pago del pedido.
        """
        try:
            cliente = pedido.cliente
            user = cliente.user
            
            contexto = {
                'cliente_nombre': user.get_full_name() or user.username or user.email,
                'numero_pedido': pedido.numero_pedido,
                'codigo_seguimiento': EmailPedidoService._generar_codigo_seguimiento(pedido),
                'total': pedido.total,
                'url_seguimiento': EmailPedidoService._get_url_seguimiento(pedido),
            }
            
            html_content = render_to_string('emails/pedido_pagado.html', contexto)
            
            texto_plano = f"""
Hola {contexto['cliente_nombre']},

¡Excelente noticia! El pago de tu pedido {pedido.numero_pedido} ha sido confirmado.

Pronto comenzaremos a preparar tu pedido.

Puedes hacer seguimiento en: {contexto['url_seguimiento']}

Equipo Elixir
            """
            
            email = EmailMultiAlternatives(
                subject=f'💳 Pago Confirmado - Pedido {pedido.numero_pedido} - Elixir',
                body=texto_plano,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            logger.info(f"Email de pago confirmado enviado para pedido {pedido.numero_pedido} a {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email de pago confirmado para pedido {pedido.numero_pedido}: {str(e)}")
            return False
    
    @staticmethod
    def enviar_notificacion_en_preparacion(pedido):
        """
        Envía email cuando el pedido entra en preparación.
        """
        try:
            cliente = pedido.cliente
            user = cliente.user
            
            contexto = {
                'cliente_nombre': user.get_full_name() or user.username or user.email,
                'numero_pedido': pedido.numero_pedido,
                'codigo_seguimiento': EmailPedidoService._generar_codigo_seguimiento(pedido),
                'url_seguimiento': EmailPedidoService._get_url_seguimiento(pedido),
            }
            
            html_content = render_to_string('emails/pedido_en_preparacion.html', contexto)
            
            texto_plano = f"""
Hola {contexto['cliente_nombre']},

¡Tu pedido {pedido.numero_pedido} está siendo preparado!

Nuestro equipo está trabajando para que tu pedido esté listo lo antes posible.

Puedes hacer seguimiento en: {contexto['url_seguimiento']}

Equipo Elixir
            """
            
            email = EmailMultiAlternatives(
                subject=f'📦 Tu Pedido Está en Preparación - {pedido.numero_pedido} - Elixir',
                body=texto_plano,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            logger.info(f"Email de preparación enviado para pedido {pedido.numero_pedido} a {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email de preparación para pedido {pedido.numero_pedido}: {str(e)}")
            return False
    
    @staticmethod
    def enviar_notificacion_enviado(pedido):
        """
        Envía email cuando el vendedor confirma el envío del pedido.
        Este es el email principal que se envía cuando el vendedor confirma el despacho.
        """
        try:
            cliente = pedido.cliente
            user = cliente.user
            
            # Calcular fecha estimada de entrega (3-5 días hábiles para envío estándar)
            from datetime import timedelta
            dias_estimados = 5 if pedido.metodo_envio == 'estandar' else 2
            fecha_estimada = timezone.now() + timedelta(days=dias_estimados)
            
            contexto = {
                'cliente_nombre': user.get_full_name() or user.username or user.email,
                'numero_pedido': pedido.numero_pedido,
                'codigo_seguimiento': EmailPedidoService._generar_codigo_seguimiento(pedido),
                'fecha_estimada': fecha_estimada.strftime('%d/%m/%Y'),
                'url_seguimiento': EmailPedidoService._get_url_seguimiento(pedido),
            }
            
            # Agregar dirección de envío
            if pedido.direccion_envio:
                direccion = pedido.direccion_envio
                contexto['direccion_envio'] = f"{direccion.calle} {direccion.numero}, {direccion.comuna}, {direccion.region}"
            
            html_content = render_to_string('emails/pedido_enviado.html', contexto)
            
            texto_plano = f"""
Hola {contexto['cliente_nombre']},

¡Excelente noticia! Tu pedido {pedido.numero_pedido} ha sido enviado y está en camino hacia ti.

Código de seguimiento: {contexto['codigo_seguimiento']}
Fecha estimada de entrega: {contexto['fecha_estimada']}

Puedes rastrear tu pedido en tiempo real aquí: {contexto['url_seguimiento']}

Te pedimos que estés atento a tu teléfono y correo para cualquier actualización sobre el delivery.

Equipo Elixir
            """
            
            email = EmailMultiAlternatives(
                subject=f'🚚 ¡Tu Pedido Está en Camino! - {pedido.numero_pedido} - Elixir',
                body=texto_plano,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            logger.info(f"Email de envío enviado para pedido {pedido.numero_pedido} a {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email de envío para pedido {pedido.numero_pedido}: {str(e)}")
            return False
    
    @staticmethod
    def enviar_notificacion_entregado(pedido):
        """
        Envía email cuando el pedido es marcado como entregado.
        """
        try:
            cliente = pedido.cliente
            user = cliente.user
            
            contexto = {
                'cliente_nombre': user.get_full_name() or user.username or user.email,
                'numero_pedido': pedido.numero_pedido,
                'url_seguimiento': EmailPedidoService._get_url_seguimiento(pedido),
            }
            
            html_content = render_to_string('emails/pedido_entregado.html', contexto)
            
            texto_plano = f"""
Hola {contexto['cliente_nombre']},

¡Tu pedido {pedido.numero_pedido} ha sido entregado exitosamente!

Esperamos que disfrutes de tu compra. Si tienes algún problema o consulta, no dudes en contactarnos.

¡Gracias por elegir Elixir!

Equipo Elixir
            """
            
            email = EmailMultiAlternatives(
                subject=f'✅ Pedido Entregado - {pedido.numero_pedido} - Elixir',
                body=texto_plano,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            logger.info(f"Email de entrega enviado para pedido {pedido.numero_pedido} a {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email de entrega para pedido {pedido.numero_pedido}: {str(e)}")
            return False
    
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

