import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import '../styles/globals.css';

export default function Checkout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [usuario, setUsuario] = useState(null);
  const [carrito, setCarrito] = useState([]);
  const [loading, setLoading] = useState(false);
  const [procesando, setProcessando] = useState(false);
  const [message, setMessage] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [metodo_pago, setMetodo] = useState('transferencia');

  useEffect(() => {
    const usuarioGuardado = localStorage.getItem('usuario');
    const carritoGuardado = localStorage.getItem('carrito');

    if (!usuarioGuardado) {
      navigate('/');
      return;
    }

    const usuarioParsed = JSON.parse(usuarioGuardado);
    
    // Solo clientes pueden hacer checkout
    if (usuarioParsed.rol !== 'cliente') {
      setErrorMsg('❌ Solo los clientes pueden realizar compras');
      return;
    }

    setUsuario(usuarioParsed);
    
    if (carritoGuardado) {
      try {
        setCarrito(JSON.parse(carritoGuardado));
      } catch (err) {
        setCarrito([]);
      }
    }

    setLoading(false);
  }, [navigate]);

  const calcularTotal = () => {
    return carrito.reduce((total, item) => total + (item.precio * item.cantidad), 0);
  };

  const handleCrearPedido = async () => {
    if (carrito.length === 0) {
      setErrorMsg('⚠️ El carrito está vacío');
      return;
    }

    setProcessando(true);
    setErrorMsg('');
    setMessage('');

    try {
      const items = carrito.map(item => ({
        producto_id: item.id,
        cantidad: item.cantidad,
        precio: item.precio
      }));

      const response = await fetch('http://localhost:8000/api/crear-pedido/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          usuario_id: usuario.id,
          items: items,
          metodo_pago: metodo_pago
        })
      });

      const data = await response.json();

      if (data.success) {
        setMessage(`✅ ¡Pedido creado exitosamente!\n\nNúmero de Pedido: ${data.numero_pedido}\nTotal: $${data.total.toFixed(2)}`);
        
        // Limpiar carrito
        localStorage.removeItem('carrito');
        setCarrito([]);

        // Redirigir a la página de confirmación de pago según el método elegido
        setTimeout(() => {
          const metodoPagoMap = {
            'transferencia': 'transferencia',
            'tarjeta': 'qr'
          };
          
          navigate('/confirmacion-pago-detalle', {
            state: {
              metodoPago: metodoPagoMap[metodo_pago],
              pedidoData: {
                numero_pedido: data.numero_pedido,
                total: data.total,
                detalles: carrito
              },
              usuario: usuario
            }
          });
        }, 2000);
      } else {
        setErrorMsg('❌ Error: ' + data.message);
      }
    } catch (err) {
      setErrorMsg('❌ Error al crear pedido: ' + err.message);
    } finally {
      setProcessando(false);
    }
  };

  const total = calcularTotal();

  return (
    <div className="checkout-container">
      {/* Header */}
      <div className="checkout-header">
        <h1>🛒 Carrito de Compras</h1>
        <p>Completa tu compra de forma segura</p>
      </div>

      {errorMsg && <div className="alert alert-danger">{errorMsg}</div>}
      {message && (
        <div className="alert alert-success">
          {message.split('\n').map((line, idx) => (
            <div key={idx}>{line}</div>
          ))}
        </div>
      )}

      <div className="checkout-content">
        {/* Resumen del carrito */}
        <div className="carrito-section">
          <h2>📦 Resumen de tu Compra</h2>
          
          {carrito.length > 0 ? (
            <div className="carrito-items">
              <div className="items-table">
                <div className="table-header">
                  <div className="col-producto">Producto</div>
                  <div className="col-cantidad">Cantidad</div>
                  <div className="col-precio">Precio Unitario</div>
                  <div className="col-subtotal">Subtotal</div>
                </div>

                {carrito.map((item) => (
                  <div key={item.id} className="table-row">
                    <div className="col-producto">
                      <div className="producto-info">
                        {item.imagen && (
                          <img src={item.imagen} alt={item.nombre} className="producto-img" />
                        )}
                        <div>
                          <p className="producto-nombre">{item.nombre}</p>
                          <p className="producto-sku">SKU: {item.sku}</p>
                        </div>
                      </div>
                    </div>
                    <div className="col-cantidad">{item.cantidad}</div>
                    <div className="col-precio">${item.precio?.toFixed(2)}</div>
                    <div className="col-subtotal">${(item.precio * item.cantidad)?.toFixed(2)}</div>
                  </div>
                ))}
              </div>

              {/* Totales */}
              <div className="carrito-totales">
                <div className="total-row">
                  <span>Subtotal:</span>
                  <span>${total?.toFixed(2)}</span>
                </div>
                <div className="total-row">
                  <span>Impuesto (0%):</span>
                  <span>$0.00</span>
                </div>
                <div className="total-row">
                  <span>Descuento:</span>
                  <span>$0.00</span>
                </div>
                <div className="total-row total-final">
                  <span>Total a Pagar:</span>
                  <span>${total?.toFixed(2)}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="empty-carrito">
              <p>🛒 Tu carrito está vacío</p>
              <button onClick={() => navigate('/')} className="btn btn-primary">
                👉 Ir a Comprar
              </button>
            </div>
          )}
        </div>

        {/* Información de pago */}
        {carrito.length > 0 && (
          <div className="pago-section">
            <h2>💳 Información de Pago</h2>

            {/* Información del cliente */}
            <div className="info-cliente">
              <h3>👤 Datos del Cliente</h3>
              <div className="info-fields">
                <div className="info-field">
                  <span className="label">Email</span>
                  <span className="value">{usuario?.email}</span>
                </div>
                <div className="info-field">
                  <span className="label">Nombre</span>
                  <span className="value">{usuario?.nombre || 'No registrado'}</span>
                </div>
              </div>
            </div>

            {/* Método de pago */}
            <div className="metodos-pago">
              <h3>Método de Pago</h3>
              <div className="pago-options">
                <label className="pago-option active">
                  <input
                    type="radio"
                    name="metodo_pago"
                    value="transferencia"
                    checked={metodo_pago === 'transferencia'}
                    onChange={(e) => setMetodo(e.target.value)}
                  />
                  <span className="option-content">
                    <span className="option-icon">🏦</span>
                    <span className="option-text">
                      <strong>Transferencia Bancaria</strong>
                      <small>Transferencia directa a nuestra cuenta bancaria</small>
                    </span>
                  </span>
                </label>
              </div>
            </div>

            {/* Información de método seleccionado */}
            {metodo_pago === 'transferencia' && (
              <div className="metodo-info">
                <div className="info-box success-info">
                  <h4>🏦 Transferencia Bancaria Seleccionada</h4>
                  <p>Se te mostrará una página con:</p>
                  <ul>
                    <li>Datos bancarios profesionales</li>
                    <li>Instrucciones paso a paso</li>
                    <li>Números copiables con un clic</li>
                    <li>Referencia del pedido</li>
                  </ul>
                  <p className="info-nota">
                    ℹ️ Después de confirmar, verás todos los detalles en la siguiente página.
                  </p>
                </div>
              </div>
            )}



            {/* Términos y condiciones */}
            <div className="terminos">
              <label className="terminos-checkbox">
                <input type="checkbox" required />
                <span>Acepto los términos y condiciones de la compra</span>
              </label>
              <label className="terminos-checkbox">
                <input type="checkbox" required />
                <span>He revisado que mi información sea correcta</span>
              </label>
            </div>

            {/* Botones de acción */}
            <div className="checkout-actions">
              <button
                onClick={handleCrearPedido}
                disabled={procesando || carrito.length === 0}
                className="btn btn-primary btn-lg"
              >
                {procesando ? '⏳ Procesando...' : '✅ Confirmar Compra'}
              </button>
              <button
                onClick={() => navigate('/')}
                className="btn btn-secondary"
              >
                🛍️ Seguir Comprando
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Información de seguridad */}
      <div className="seguridad-info">
        <div className="seguridad-item">
          <span className="seguridad-icon">🔒</span>
          <span className="seguridad-text">Compra 100% Segura</span>
        </div>
        <div className="seguridad-item">
          <span className="seguridad-icon">🚚</span>
          <span className="seguridad-text">Envío Rápido</span>
        </div>
        <div className="seguridad-item">
          <span className="seguridad-icon">💬</span>
          <span className="seguridad-text">Soporte 24/7</span>
        </div>
        <div className="seguridad-item">
          <span className="seguridad-icon">↩️</span>
          <span className="seguridad-text">Devoluciones Gratis</span>
        </div>
      </div>
    </div>
  );
}
