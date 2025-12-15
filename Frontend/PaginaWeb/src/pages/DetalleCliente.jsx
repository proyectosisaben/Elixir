import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useRol } from '../contexts/RolContext';
import '../styles/globals.css';
import {
  FaUser,
  FaShoppingCart,
  FaDollarSign,
  FaCalendarAlt,
  FaStar,
  FaSearch,
  FaArrowLeft,
  FaBox,
  FaCreditCard,
  FaMapMarkerAlt,
  FaPhone
} from 'react-icons/fa';

function DetalleCliente() {
  const { clienteId } = useParams();
  const { usuario, tieneRol } = useRol();
  const navigate = useNavigate();
  const [cliente, setCliente] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('estadisticas');

  useEffect(() => {
    if (usuario && (tieneRol('vendedor') || tieneRol('gerente') || tieneRol('admin_sistema'))) {
      cargarDetalleCliente();
    }
  }, [usuario, clienteId]);

  const cargarDetalleCliente = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/clientes/${clienteId}/?user_id=${usuario?.id}`);
      const data = await response.json();

      if (response.ok && data.success) {
        setCliente(data);
      } else {
        throw new Error(data.message || 'Error al cargar detalle del cliente');
      }
    } catch (err) {
      console.error('Error cargando detalle del cliente:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatearMoneda = (valor) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP'
    }).format(valor);
  };

  const formatearFecha = (fecha) => {
    if (!fecha) return 'N/A';
    try {
      return new Date(fecha).toLocaleString('es-CL');
    } catch {
      return fecha;
    }
  };

  if (!usuario || (!tieneRol('vendedor') && !tieneRol('gerente') && !tieneRol('admin_sistema'))) {
    return (
      <div className="detalle-cliente-container">
        <div className="alert alert-danger text-center">
          <h3>❌ Acceso Denegado</h3>
          <p>Solo vendedores, gerentes y administradores pueden ver detalles de clientes.</p>
          <button onClick={() => navigate('/')} className="btn btn-primary">
            <FaArrowLeft /> Volver al inicio
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="detalle-cliente-container">
        <div className="loading">Cargando información del cliente...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="detalle-cliente-container">
        <div className="alert alert-danger text-center">
          <h3>❌ Error</h3>
          <p>{error}</p>
          <button onClick={cargarDetalleCliente} className="btn btn-primary">Reintentar</button>
        </div>
      </div>
    );
  }

  if (!cliente) {
    return (
      <div className="detalle-cliente-container">
        <div className="alert alert-warning text-center">
          <h3>Cliente no encontrado</h3>
          <button onClick={() => navigate('/dashboard')} className="btn btn-primary">
            <FaArrowLeft /> Volver al dashboard
          </button>
        </div>
      </div>
    );
  }

  const infoCliente = cliente.cliente;
  const estadisticas = cliente.estadisticas;
  const productosFavoritos = cliente.productos_favoritos;
  const historialPedidos = cliente.historial_pedidos;

  return (
    <div className="detalle-cliente-container">
      <div className="detalle-cliente-header">
        <div className="header-actions">
          <button
            onClick={() => navigate('/dashboard')}
            className="btn-volver"
          >
            <FaArrowLeft /> Volver al Dashboard
          </button>
        </div>

        <div className="cliente-info-principal">
          <div className="cliente-avatar">
            <FaUser />
          </div>
          <div className="cliente-datos">
            <h1>{infoCliente.user.first_name} {infoCliente.user.last_name}</h1>
            <p className="cliente-email">{infoCliente.user.email}</p>
            <p className="cliente-fecha">Cliente desde: {formatearFecha(infoCliente.user.date_joined)}</p>
          </div>
        </div>
      </div>

      <div className="detalle-cliente-main">
        {/* Información de contacto */}
        <div className="info-contacto-section">
          <h3><FaPhone /> Información de Contacto</h3>
          <div className="info-contacto-grid">
            <div className="info-item">
              <FaUser className="info-icon" />
              <div>
                <strong>Nombre completo</strong>
                <p>{infoCliente.user.first_name} {infoCliente.user.last_name}</p>
              </div>
            </div>
            <div className="info-item">
              <FaMapMarkerAlt className="info-icon" />
              <div>
                <strong>Dirección</strong>
                <p>{infoCliente.direccion || 'No especificada'}</p>
              </div>
            </div>
            <div className="info-item">
              <FaPhone className="info-icon" />
              <div>
                <strong>Teléfono</strong>
                <p>{infoCliente.telefono || 'No especificado'}</p>
              </div>
            </div>
            <div className="info-item">
              <FaCalendarAlt className="info-icon" />
              <div>
                <strong>Fecha de nacimiento</strong>
                <p>{formatearFecha(infoCliente.fecha_nacimiento) || 'No especificada'}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs de navegación */}
        <div className="tabs-container">
          <div className="tabs-nav">
            <button
              className={`tab-btn ${activeTab === 'estadisticas' ? 'active' : ''}`}
              onClick={() => setActiveTab('estadisticas')}
            >
              <FaShoppingCart /> Estadísticas
            </button>
            <button
              className={`tab-btn ${activeTab === 'productos' ? 'active' : ''}`}
              onClick={() => setActiveTab('productos')}
            >
              <FaStar /> Productos Favoritos
            </button>
            <button
              className={`tab-btn ${activeTab === 'historial' ? 'active' : ''}`}
              onClick={() => setActiveTab('historial')}
            >
              <FaBox /> Historial de Pedidos
            </button>
          </div>

          <div className="tab-content">
            {/* Tab Estadísticas */}
            {activeTab === 'estadisticas' && (
              <div className="estadisticas-content">
                <div className="estadisticas-grid">
                  <div className="estadistica-card">
                    <div className="estadistica-header">
                      <FaShoppingCart className="estadistica-icon" />
                      <h4>Total de Pedidos</h4>
                    </div>
                    <p className="estadistica-valor">{estadisticas.total_pedidos}</p>
                    <p className="estadistica-label">Pedidos realizados</p>
                  </div>

                  <div className="estadistica-card">
                    <div className="estadistica-header">
                      <FaDollarSign className="estadistica-icon" />
                      <h4>Total Gastado</h4>
                    </div>
                    <p className="estadistica-valor">{formatearMoneda(estadisticas.total_gastado)}</p>
                    <p className="estadistica-label">En todos los pedidos</p>
                  </div>

                  <div className="estadistica-card">
                    <div className="estadistica-header">
                      <FaCreditCard className="estadistica-icon" />
                      <h4>Ticket Promedio</h4>
                    </div>
                    <p className="estadistica-valor">{formatearMoneda(estadisticas.ticket_promedio)}</p>
                    <p className="estadistica-label">Por pedido promedio</p>
                  </div>

                  <div className="estadistica-card">
                    <div className="estadistica-header">
                      <FaCalendarAlt className="estadistica-icon" />
                      <h4>Última Compra</h4>
                    </div>
                    {estadisticas.ultima_compra ? (
                      <>
                        <p className="estadistica-valor">{formatearFecha(estadisticas.ultima_compra.fecha)}</p>
                        <p className="estadistica-label">{formatearMoneda(estadisticas.ultima_compra.total)}</p>
                      </>
                    ) : (
                      <>
                        <p className="estadistica-valor">Sin compras</p>
                        <p className="estadistica-label">Aún no ha comprado</p>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Tab Productos Favoritos */}
            {activeTab === 'productos' && (
              <div className="productos-content">
                <h3>Productos Más Comprados</h3>
                {productosFavoritos.length === 0 ? (
                  <div className="empty-state">
                    <FaBox className="empty-icon" />
                    <p>Este cliente aún no ha realizado compras.</p>
                  </div>
                ) : (
                  <div className="productos-grid">
                    {productosFavoritos.map((producto, index) => (
                      <div key={index} className="producto-card">
                        <div className="producto-header">
                          <h4>{producto.nombre}</h4>
                          <span className="producto-rank">#{index + 1}</span>
                        </div>
                        <div className="producto-stats">
                          <div className="stat-item">
                            <span className="stat-label">Cantidad total:</span>
                            <span className="stat-value">{producto.cantidad_total}</span>
                          </div>
                          <div className="stat-item">
                            <span className="stat-label">Total gastado:</span>
                            <span className="stat-value">{formatearMoneda(producto.total_gastado)}</span>
                          </div>
                          <div className="stat-item">
                            <span className="stat-label">En pedidos:</span>
                            <span className="stat-value">{producto.pedidos_donde_aparece}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Tab Historial de Pedidos */}
            {activeTab === 'historial' && (
              <div className="historial-content">
                <h3>Historial de Pedidos ({historialPedidos.length})</h3>
                {historialPedidos.length === 0 ? (
                  <div className="empty-state">
                    <FaShoppingCart className="empty-icon" />
                    <p>Este cliente aún no ha realizado pedidos.</p>
                  </div>
                ) : (
                  <div className="pedidos-list">
                    {historialPedidos.map((pedido) => (
                      <div key={pedido.id} className="pedido-card">
                        <div className="pedido-header">
                          <div className="pedido-info">
                            <h4>Pedido #{pedido.id}</h4>
                            <p className="pedido-fecha">{formatearFecha(pedido.fecha_pedido)}</p>
                          </div>
                          <div className="pedido-estado">
                            <span className={`estado-badge estado-${pedido.estado.toLowerCase().replace(' ', '-')}`}>
                              {pedido.estado}
                            </span>
                          </div>
                        </div>

                        <div className="pedido-detalles">
                          <div className="pedido-resumen">
                            <div className="resumen-item">
                              <span className="resumen-label">Total:</span>
                              <span className="resumen-valor">{formatearMoneda(pedido.total)}</span>
                            </div>
                            <div className="resumen-item">
                              <span className="resumen-label">Método de pago:</span>
                              <span className="resumen-valor">{pedido.metodo_pago}</span>
                            </div>
                          </div>

                          <div className="pedido-productos">
                            <h5>Productos ({pedido.detalles.length})</h5>
                            <div className="productos-lista">
                              {pedido.detalles.map((detalle, index) => (
                                <div key={index} className="producto-item">
                                  <div className="producto-info">
                                    <span className="producto-nombre">{detalle.producto.nombre}</span>
                                    <span className="producto-sku">SKU: {detalle.producto.sku}</span>
                                  </div>
                                  <div className="producto-cantidad">
                                    <span>{detalle.cantidad}x {formatearMoneda(detalle.precio_unitario)}</span>
                                    <span className="producto-subtotal">{formatearMoneda(detalle.subtotal)}</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default DetalleCliente;
