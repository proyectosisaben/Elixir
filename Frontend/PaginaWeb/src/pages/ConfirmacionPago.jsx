import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import '../styles/globals.css';

export default function ConfirmacionPago() {
  const navigate = useNavigate();
  const location = useLocation();
  const [pedido, setPedido] = useState(null);
  const [usuario, setUsuario] = useState(null);
  const [metodoPago, setMetodoPago] = useState('qr');
  const [mostrandoQR, setMostrandoQR] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Obtener datos del pedido desde la redirección
    const pedidoData = location.state?.pedido;
    const usuarioData = location.state?.usuario;

    if (!pedidoData || !usuarioData) {
      // Si no hay datos, redirigir
      navigate('/');
      return;
    }

    setPedido(pedidoData);
    setUsuario(usuarioData);
    setLoading(false);
  }, [navigate, location]);

  const handleContinuarCompra = () => {
    navigate('/catalogo');
  };

  const handleVerPedido = () => {
    navigate('/perfil?tab=pedidos');
  };

  const handleDescargarRecibo = () => {
    // Implementar descarga de recibo PDF
    alert('Descargando recibo...');
  };

  if (loading) {
    return (
      <div className="confirmacion-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando información del pedido...</p>
        </div>
      </div>
    );
  }

  if (!pedido) {
    return (
      <div className="confirmacion-container">
        <div className="error-message">
          <h2>⚠️ Error</h2>
          <p>No se encontró información del pedido</p>
          <button onClick={() => navigate('/')} className="btn btn-primary">
            Volver al inicio
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="confirmacion-container">
      {/* Header de éxito */}
      <div className="confirmacion-header success">
        <div className="success-icon">
          <i className="fas fa-check-circle"></i>
        </div>
        <h1>¡Pedido Realizado Exitosamente!</h1>
        <p>Tu compra ha sido registrada en nuestro sistema</p>
      </div>

      <div className="confirmacion-content">
        {/* Tarjeta de resumen del pedido */}
        <div className="pedido-resumen">
          <h2>📋 Resumen del Pedido</h2>
          
          <div className="resumen-grid">
            <div className="resumen-item">
              <span className="label">Número de Pedido</span>
              <span className="value pedido-numero">{pedido.numero_pedido}</span>
            </div>
            <div className="resumen-item">
              <span className="label">Fecha</span>
              <span className="value">{new Date().toLocaleDateString('es-ES')}</span>
            </div>
            <div className="resumen-item">
              <span className="label">Total</span>
              <span className="value total-amount">${pedido.total?.toFixed(2)}</span>
            </div>
            <div className="resumen-item">
              <span className="label">Estado</span>
              <span className="value estado-badge pendiente">Pendiente de Pago</span>
            </div>
          </div>

          {/* Detalles del cliente */}
          <div className="cliente-info">
            <h3>👤 Información del Cliente</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">Email</span>
                <span className="info-value">{usuario?.email}</span>
              </div>
              <div className="info-item">
                <span className="info-label">Nombre</span>
                <span className="info-value">{usuario?.nombre || 'No registrado'}</span>
              </div>
            </div>
          </div>

          {/* Productos comprados */}
          {pedido.detalles && pedido.detalles.length > 0 && (
            <div className="productos-comprados">
              <h3>📦 Productos</h3>
              <div className="productos-table">
                <div className="table-header">
                  <div className="col">Producto</div>
                  <div className="col">Cantidad</div>
                  <div className="col">Precio Unitario</div>
                  <div className="col">Subtotal</div>
                </div>
                {pedido.detalles.map((item, idx) => (
                  <div key={idx} className="table-row">
                    <div className="col">{item.nombre || 'Producto'}</div>
                    <div className="col">{item.cantidad}</div>
                    <div className="col">${item.precio_unitario?.toFixed(2)}</div>
                    <div className="col">${(item.cantidad * item.precio_unitario)?.toFixed(2)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sección de selección de método de pago */}
        <div className="pago-seccion">
          <h2>💳 Método de Pago</h2>
          <p className="pago-aviso">Selecciona cómo deseas completar tu pago:</p>

          <div className="pago-opciones">
            {/* Opción QR */}
            <div className={`pago-card ${metodoPago === 'qr' ? 'active' : ''}`}>
              <input
                type="radio"
                id="metodo-qr"
                name="metodoPago"
                value="qr"
                checked={metodoPago === 'qr'}
                onChange={(e) => {
                  setMetodoPago(e.target.value);
                  setMostrandoQR(false);
                }}
              />
              <label htmlFor="metodo-qr" className="pago-label">
                <span className="pago-icono">📱</span>
                <span className="pago-titulo">Transferencia por QR</span>
                <span className="pago-desc">Escanea el código QR con tu aplicación bancaria</span>
              </label>
            </div>

            {/* Opción Transferencia Bancaria */}
            <div className={`pago-card ${metodoPago === 'transferencia' ? 'active' : ''}`}>
              <input
                type="radio"
                id="metodo-transferencia"
                name="metodoPago"
                value="transferencia"
                checked={metodoPago === 'transferencia'}
                onChange={(e) => {
                  setMetodoPago(e.target.value);
                  setMostrandoQR(false);
                }}
              />
              <label htmlFor="metodo-transferencia" className="pago-label">
                <span className="pago-icono">🏦</span>
                <span className="pago-titulo">Transferencia Bancaria</span>
                <span className="pago-desc">Realiza una transferencia manualmente a nuestra cuenta</span>
              </label>
            </div>
          </div>

          {/* Contenido según método seleccionado */}
          <div className="pago-contenido">
            {metodoPago === 'qr' && (
              <div className="qr-section">
                <h3>📱 Escanea este código QR</h3>
                <div className="qr-container">
                  <img
                    src="http://localhost:8000/media/productos/QR%20TRANSFERENCIAS.jpeg"
                    alt="QR de transferencia"
                    className="qr-image"
                    onError={(e) => {
                      e.target.src = 'https://via.placeholder.com/300?text=QR+No+Disponible';
                    }}
                  />
                </div>
                <div className="qr-instrucciones">
                  <h4>Instrucciones:</h4>
                  <ol>
                    <li>Abre tu aplicación bancaria</li>
                    <li>Selecciona "Escanear código QR"</li>
                    <li>Apunta la cámara hacia el código QR</li>
                    <li>Confirma la transferencia</li>
                    <li>¡Listo! Tu pedido será procesado en 24 horas</li>
                  </ol>
                </div>
                <div className="qr-monto">
                  <p className="monto-label">Monto a transferir:</p>
                  <p className="monto-valor">${pedido.total?.toFixed(2)}</p>
                </div>
              </div>
            )}

            {metodoPago === 'transferencia' && (
              <div className="transferencia-section">
                <h3>🏦 Datos Bancarios</h3>
                <div className="datos-bancarios">
                  <div className="dato-item">
                    <span className="dato-label">🏛️ Banco</span>
                    <span className="dato-valor">Banco Ejemplo SpA</span>
                  </div>
                  <div className="dato-item">
                    <span className="dato-label">👤 Titular de la Cuenta</span>
                    <span className="dato-valor">Empresa Elixir S.A.</span>
                  </div>
                  <div className="dato-item">
                    <span className="dato-label">🏦 Tipo de Cuenta</span>
                    <span className="dato-valor">Cuenta Corriente</span>
                  </div>
                  <div className="dato-item">
                    <span className="dato-label">💳 Número de Cuenta</span>
                    <span className="dato-valor">12345678901234</span>
                  </div>
                  <div className="dato-item">
                    <span className="dato-label">🔀 Código de Banco</span>
                    <span className="dato-valor">001</span>
                  </div>
                  <div className="dato-item dato-importante">
                    <span className="dato-label">📝 Referencia de Pago</span>
                    <span className="dato-valor">{pedido.numero_pedido}</span>
                  </div>
                </div>

                <div className="transferencia-instrucciones">
                  <h4>⚠️ Importante:</h4>
                  <ul>
                    <li>
                      <strong>Referencia:</strong> Utiliza el número de pedido{' '}
                      <code>{pedido.numero_pedido}</code> como referencia
                    </li>
                    <li>
                      <strong>Monto exacto:</strong> ${pedido.total?.toFixed(2)} (sin variaciones)
                    </li>
                    <li>
                      <strong>Comprobante:</strong> Guarda el comprobante de tu transferencia
                    </li>
                    <li>
                      <strong>Confirmación:</strong> Recibirás un email de confirmación en 24 horas
                    </li>
                  </ul>
                </div>

                <div className="transferencia-monto">
                  <p className="monto-label">Monto a transferir:</p>
                  <p className="monto-valor">${pedido.total?.toFixed(2)}</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Tarjeta de información */}
        <div className="info-importante">
          <h3>ℹ️ Información Importante</h3>
          <div className="info-items">
            <div className="info-item-box">
              <span className="info-icono">⏱️</span>
              <div className="info-texto">
                <p className="info-titulo">Procesamiento</p>
                <p className="info-desc">Tu pedido será procesado dentro de 24 horas después de verificar el pago</p>
              </div>
            </div>
            <div className="info-item-box">
              <span className="info-icono">📧</span>
              <div className="info-texto">
                <p className="info-titulo">Confirmación por Email</p>
                <p className="info-desc">Recibirás un email de confirmación con el número de pedido y los detalles</p>
              </div>
            </div>
            <div className="info-item-box">
              <span className="info-icono">🚚</span>
              <div className="info-texto">
                <p className="info-titulo">Seguimiento</p>
                <p className="info-desc">Podrás ver el estado de tu pedido en tu perfil en cualquier momento</p>
              </div>
            </div>
            <div className="info-item-box">
              <span className="info-icono">💬</span>
              <div className="info-texto">
                <p className="info-titulo">Soporte</p>
                <p className="info-desc">Si tienes dudas, contáctanos a través de nuestro chat de soporte 24/7</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Botones de acción */}
      <div className="confirmacion-acciones">
        <button onClick={handleVerPedido} className="btn btn-primary btn-lg">
          <i className="fas fa-receipt"></i> Ver Mi Pedido
        </button>
        <button onClick={handleDescargarRecibo} className="btn btn-secondary btn-lg">
          <i className="fas fa-download"></i> Descargar Recibo
        </button>
        <button onClick={handleContinuarCompra} className="btn btn-outline-secondary btn-lg">
          <i className="fas fa-shopping-cart"></i> Continuar Comprando
        </button>
      </div>
    </div>
  );
}
