import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import '../styles/globals.css';

export default function ConfirmacionPagoDetalle() {
  const location = useLocation();
  const navigate = useNavigate();
  const [pedidoData, setPedidoData] = useState(null);
  const [metodoPago, setMetodoPago] = useState('qr');
  const [copiado, setCopiado] = useState(false);

  useEffect(() => {
    if (!location.state) {
      navigate('/');
      return;
    }

    setPedidoData(location.state.pedidoData);
    setMetodoPago(location.state.metodoPago || 'qr');
  }, [location.state, navigate]);

  const copiarAlPortapapeles = (texto) => {
    navigator.clipboard.writeText(texto);
    setCopiado(true);
    setTimeout(() => setCopiado(false), 2000);
  };

  if (!pedidoData) {
    return (
      <div className="confirmacion-container">
        <div className="loading">Cargando información del pedido...</div>
      </div>
    );
  }

  const numeroPedido = pedidoData.numero_pedido;
  const total = pedidoData.total;

  return (
    <div className="confirmacion-container">
      <div className="confirmacion-header">
        <div className="confirmacion-icon-success">
          <svg width="60" height="60" viewBox="0 0 60 60" fill="none">
            <circle cx="30" cy="30" r="29" stroke="var(--success-color)" strokeWidth="2" />
            <path
              d="M18 31L26 39L42 23"
              stroke="var(--success-color)"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
            />
          </svg>
        </div>
        <h1>¡Pedido Confirmado!</h1>
        <p className="pedido-numero">Número de Pedido: <strong>#{numeroPedido}</strong></p>
        <p className="confirmacion-subtitle">Tu pedido ha sido procesado exitosamente</p>
      </div>

      <div className="confirmacion-content">
        {/* Resumen del Pedido */}
        <div className="resumen-pedido">
          <h2>📋 Resumen del Pedido</h2>
          <div className="resumen-items">
            <div className="resumen-row">
              <span>Número de Pedido:</span>
              <strong>#{numeroPedido}</strong>
            </div>
            <div className="resumen-row">
              <span>Cantidad de Productos:</span>
              <strong>{pedidoData.detalles?.length || 0} artículos</strong>
            </div>
            <div className="resumen-row">
              <span>Monto Total:</span>
              <strong className="total-amount">${total?.toFixed(2)} CLP</strong>
            </div>
            <div className="resumen-row">
              <span>Estado:</span>
              <span className="estado-badge estado-pendiente">⏳ Pendiente de Pago</span>
            </div>
          </div>
        </div>

        {/* Método de Pago Seleccionado */}
        <div className="metodo-pago-section">
          <h2>💳 Información de Pago</h2>
          <p className="pago-description">
            Completa tu pago usando uno de los siguientes métodos:
          </p>

          {/* Tabs de Métodos */}
          <div className="metodos-tabs">
            <button
              className={`tab-button ${metodoPago === 'qr' ? 'active' : ''}`}
              onClick={() => setMetodoPago('qr')}
            >
              <span className="tab-icon">📱</span>
              <span className="tab-text">QR Transferencia</span>
            </button>
            <button
              className={`tab-button ${metodoPago === 'transferencia' ? 'active' : ''}`}
              onClick={() => setMetodoPago('transferencia')}
            >
              <span className="tab-icon">🏦</span>
              <span className="tab-text">Transferencia Bancaria</span>
            </button>
          </div>

          {/* Contenido QR */}
          {metodoPago === 'qr' && (
            <div className="metodo-contenido qr-section">
              <div className="qr-container">
                <h3>Escanea el QR para transferir</h3>
                <div className="qr-image-wrapper">
                  <img
                    src="/imagenes/sliders/transferencia.jpg"
                    alt="QR para transferencia"
                    className="qr-image"
                    onError={(e) => {
                      e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200"%3E%3Crect fill="%23f0f0f0" width="200" height="200"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" font-size="14" fill="%23999"%3EQR No disponible%3C/text%3E%3C/svg%3E';
                    }}
                  />
                </div>
                <div className="qr-instructions">
                  <h4>📱 Instrucciones:</h4>
                  <ol>
                    <li>Abre tu aplicación bancaria</li>
                    <li>Selecciona "Pagar con QR" o "Escanear código"</li>
                    <li>Escanea la imagen QR anterior</li>
                    <li>Verifica los datos de la transferencia</li>
                    <li>Confirma y completa el pago</li>
                  </ol>
                  <p className="qr-amount">
                    <strong>Monto a transferir: ${total?.toFixed(2)} CLP</strong>
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Contenido Transferencia Bancaria */}
          {metodoPago === 'transferencia' && (
            <div className="metodo-contenido transferencia-section">
              <div className="banco-container">
                <div className="banco-header">
                  <h3>🏦 Datos de Transferencia Bancaria</h3>
                  <p className="banco-subtitle">Realiza tu transferencia a los datos que se muestran a continuación</p>
                </div>

                <div className="banco-datos">
                  <div className="dato-item">
                    <div className="dato-label">Banco</div>
                    <div className="dato-valor">Banco del Estado de Chile</div>
                  </div>

                  <div className="dato-item">
                    <div className="dato-label">Tipo de Cuenta</div>
                    <div className="dato-valor">Cuenta Corriente</div>
                  </div>

                  <div className="dato-item">
                    <div className="dato-label">Titular</div>
                    <div className="dato-valor">Elixir Bebidas SpA</div>
                  </div>

                  <div className="dato-item highlight">
                    <div className="dato-label">Número de Cuenta</div>
                    <div className="dato-valor-container">
                      <div className="dato-valor-numero">3948729847</div>
                      <button
                        className={`btn-copiar ${copiado ? 'copiado' : ''}`}
                        onClick={() => copiarAlPortapapeles('3948729847')}
                        title="Copiar número de cuenta"
                      >
                        {copiado ? '✓ Copiado' : '📋 Copiar'}
                      </button>
                    </div>
                  </div>

                  <div className="dato-item">
                    <div className="dato-label">RUT / RFC</div>
                    <div className="dato-valor">76.123.456-7</div>
                  </div>

                  <div className="dato-item">
                    <div className="dato-label">Email Contacto</div>
                    <div className="dato-valor">pagos@elixir.cl</div>
                  </div>

                  <div className="dato-item highlight">
                    <div className="dato-label">Monto a Transferir</div>
                    <div className="dato-valor-numero" style={{ fontSize: '24px', color: 'var(--success-color)' }}>
                      ${total?.toFixed(2)} CLP
                    </div>
                  </div>

                  <div className="dato-item">
                    <div className="dato-label">Referencia / Glosa (Opcional)</div>
                    <div className="dato-valor-container">
                      <div className="dato-valor-numero">Pedido #{numeroPedido}</div>
                      <button
                        className={`btn-copiar ${copiado ? 'copiado' : ''}`}
                        onClick={() => copiarAlPortapapeles(`Pedido #${numeroPedido}`)}
                        title="Copiar referencia"
                      >
                        {copiado ? '✓ Copiado' : '📋 Copiar'}
                      </button>
                    </div>
                  </div>
                </div>

                <div className="transferencia-instructions">
                  <h4>📋 Instrucciones de Transferencia:</h4>
                  <ul>
                    <li><strong>1.</strong> Accede a tu banco en línea o app móvil</li>
                    <li><strong>2.</strong> Selecciona "Realizar transferencia" o "Enviar dinero"</li>
                    <li><strong>3.</strong> Ingresa el número de cuenta: <strong>3948729847</strong></li>
                    <li><strong>4.</strong> Verifica el nombre del titular: <strong>Elixir Bebidas SpA</strong></li>
                    <li><strong>5.</strong> Ingresa el monto: <strong>${total?.toFixed(2)} CLP</strong></li>
                    <li><strong>6.</strong> En la referencia, ingresa: <strong>Pedido #{numeroPedido}</strong></li>
                    <li><strong>7.</strong> Revisa todos los datos y confirma</li>
                    <li><strong>8.</strong> Guarda el comprobante de transferencia</li>
                  </ul>
                </div>

                <div className="transferencia-info-box">
                  <div className="info-icon">ℹ️</div>
                  <div className="info-content">
                    <h4>Información Importante</h4>
                    <p>
                      Por favor, <strong>conserva el comprobante de tu transferencia</strong>. 
                      Recibirás un correo de confirmación en <strong>{location.state?.usuario?.email}</strong> 
                      una vez que verifiquemos el pago (esto puede tomar entre 1 a 24 horas hábiles).
                    </p>
                    <p>
                      Si necesitas ayuda, contáctanos a <strong>pagos@elixir.cl</strong> con tu número de pedido.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Detalles de Productos */}
        {pedidoData.detalles && pedidoData.detalles.length > 0 && (
          <div className="detalles-productos">
            <h2>📦 Productos en tu Pedido</h2>
            <div className="productos-list">
              {pedidoData.detalles.map((item, idx) => (
                <div key={idx} className="producto-item">
                  {(item.imagen_url || item.imagen) && (
                    <img src={item.imagen_url || item.imagen} alt={item.nombre} className="producto-imagen" />
                  )}
                  <div className="producto-details">
                    <p className="producto-nombre">{item.nombre}</p>
                    <p className="producto-sku">SKU: {item.sku}</p>
                  </div>
                  <div className="producto-cantidad">
                    <span className="cantidad-badge">{item.cantidad}x</span>
                  </div>
                  <div className="producto-precio">
                    ${(item.precio * item.cantidad)?.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Próximos Pasos */}
        <div className="proximos-pasos">
          <h2>🎯 Próximos Pasos</h2>
          <div className="pasos-grid">
            <div className="paso-item">
              <div className="paso-numero">1</div>
              <div className="paso-content">
                <h4>Realiza el Pago</h4>
                <p>Completa la transferencia con los datos proporcionados</p>
              </div>
            </div>
            <div className="paso-item">
              <div className="paso-numero">2</div>
              <div className="paso-content">
                <h4>Guarda el Comprobante</h4>
                <p>Conserva la evidencia de tu pago por seguridad</p>
              </div>
            </div>
            <div className="paso-item">
              <div className="paso-numero">3</div>
              <div className="paso-content">
                <h4>Recibe Confirmación</h4>
                <p>Te notificaremos por email cuando verifiquemos el pago</p>
              </div>
            </div>
            <div className="paso-item">
              <div className="paso-numero">4</div>
              <div className="paso-content">
                <h4>Prepara tu Entrega</h4>
                <p>Tu pedido será preparado y enviado inmediatamente</p>
              </div>
            </div>
          </div>
        </div>

        {/* Acciones */}
        <div className="confirmacion-actions">
          <button
            onClick={() => navigate('/')}
            className="btn btn-primary btn-lg"
          >
            🛍️ Seguir Comprando
          </button>
          <button
            onClick={() => navigate('/perfil')}
            className="btn btn-secondary btn-lg"
          >
            📋 Ver mis Pedidos
          </button>
        </div>
      </div>

      {/* Footer Info */}
      <div className="confirmacion-footer">
        <div className="footer-item">
          <span className="footer-icon">📧</span>
          <span>Recibirás confirmación por email</span>
        </div>
        <div className="footer-item">
          <span className="footer-icon">🕐</span>
          <span>Verificación en 1-24 horas hábiles</span>
        </div>
        <div className="footer-item">
          <span className="footer-icon">💬</span>
          <span>Soporte disponible 24/7</span>
        </div>
        <div className="footer-item">
          <span className="footer-icon">🔒</span>
          <span>Datos protegidos y seguros</span>
        </div>
      </div>
    </div>
  );
}
