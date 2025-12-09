import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/globals.css';

export default function GestionPerfil() {
  const navigate = useNavigate();
  const [usuario, setUsuario] = useState(null);
  const [perfil, setPerfil] = useState(null);
  const [pedidos, setPedidos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editando, setEditando] = useState(false);
  const [formData, setFormData] = useState({});
  const [message, setMessage] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [activeTab, setActiveTab] = useState('perfil');

  useEffect(() => {
    const usuarioGuardado = localStorage.getItem('usuario');
    
    if (!usuarioGuardado) {
      navigate('/');
      return;
    }

    const usuarioParsed = JSON.parse(usuarioGuardado);
    setUsuario(usuarioParsed);
    
    cargarPerfil(usuarioParsed.id);
    cargarPedidos(usuarioParsed.id);
  }, [navigate]);

  const cargarPerfil = async (usuarioId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/mi-perfil/?usuario_id=${usuarioId}`);
      const data = await response.json();
      
      if (data.success) {
        setPerfil(data.perfil);
        setFormData({
          nombre: data.perfil.nombre,
          apellido: data.perfil.apellido,
          fecha_nacimiento: data.perfil.fecha_nacimiento
        });
      }
    } catch (err) {
      setErrorMsg('Error al cargar perfil: ' + err.message);
    }
  };

  const cargarPedidos = async (usuarioId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/mis-pedidos/?usuario_id=${usuarioId}`);
      const data = await response.json();
      
      if (data.success) {
        setPedidos(data.pedidos || []);
      }
    } catch (err) {
      setErrorMsg('Error al cargar pedidos: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleActualizarPerfil = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/mi-perfil/', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          usuario_id: usuario.id,
          ...formData
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setMessage('✅ Perfil actualizado exitosamente');
        setEditando(false);
        cargarPerfil(usuario.id);
        setTimeout(() => setMessage(''), 3000);
      } else {
        setErrorMsg(data.message);
      }
    } catch (err) {
      setErrorMsg('Error al actualizar perfil: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !perfil) {
    return (
      <div className="gestion-perfil-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Cargando perfil...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="gestion-perfil-container">
      {/* Header */}
      <div className="perfil-header">
        <h1>Mi Perfil</h1>
        <p>Gestiona tu información personal y visualiza tu historial</p>
      </div>

      {message && <div className="alert alert-success">{message}</div>}
      {errorMsg && <div className="alert alert-danger">{errorMsg}</div>}

      {/* Tabs de navegación */}
      <div className="tabs-navigation">
        <button
          className={`tab-btn ${activeTab === 'perfil' ? 'active' : ''}`}
          onClick={() => setActiveTab('perfil')}
        >
          📋 Mi Perfil
        </button>
        <button
          className={`tab-btn ${activeTab === 'pedidos' ? 'active' : ''}`}
          onClick={() => setActiveTab('pedidos')}
        >
          📦 Mis Pedidos ({pedidos.length})
        </button>
        <button
          className={`tab-btn ${activeTab === 'estadisticas' ? 'active' : ''}`}
          onClick={() => setActiveTab('estadisticas')}
        >
          📊 Estadísticas
        </button>
      </div>

      {/* Contenido - Mi Perfil */}
      {activeTab === 'perfil' && (
        <div className="tab-content">
          <div className="perfil-card">
            <div className="perfil-info">
              <div className="info-section">
                <h2>Información Personal</h2>
                
                {editando ? (
                  <div className="form-group">
                    <div className="form-row">
                      <div className="form-field">
                        <label>Nombre</label>
                        <input
                          type="text"
                          name="nombre"
                          value={formData.nombre || ''}
                          onChange={handleInputChange}
                          className="input-field"
                        />
                      </div>
                      <div className="form-field">
                        <label>Apellido</label>
                        <input
                          type="text"
                          name="apellido"
                          value={formData.apellido || ''}
                          onChange={handleInputChange}
                          className="input-field"
                        />
                      </div>
                    </div>
                    <div className="form-field">
                      <label>Fecha de Nacimiento</label>
                      <input
                        type="date"
                        name="fecha_nacimiento"
                        value={formData.fecha_nacimiento || ''}
                        onChange={handleInputChange}
                        className="input-field"
                      />
                    </div>
                    <div className="form-actions">
                      <button onClick={handleActualizarPerfil} className="btn btn-primary" disabled={loading}>
                        {loading ? 'Guardando...' : '💾 Guardar Cambios'}
                      </button>
                      <button onClick={() => { setEditando(false); setErrorMsg(''); }} className="btn btn-secondary">
                        ❌ Cancelar
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="info-display">
                    <div className="info-field">
                      <span className="label">📧 Email</span>
                      <span className="value">{perfil?.email}</span>
                    </div>
                    <div className="info-field">
                      <span className="label">👤 Nombre</span>
                      <span className="value">{perfil?.nombre || 'No registrado'}</span>
                    </div>
                    <div className="info-field">
                      <span className="label">📝 Apellido</span>
                      <span className="value">{perfil?.apellido || 'No registrado'}</span>
                    </div>
                    <div className="info-field">
                      <span className="label">🎂 Fecha de Nacimiento</span>
                      <span className="value">{perfil?.fecha_nacimiento || 'No registrado'}</span>
                    </div>
                    <div className="info-field">
                      <span className="label">🎭 Rol</span>
                      <span className="value rol-badge" style={{backgroundColor: getRolColor(perfil?.rol)}}>
                        {perfil?.rol?.toUpperCase()}
                      </span>
                    </div>
                    <div className="info-field">
                      <span className="label">✅ Email Confirmado</span>
                      <span className="value">
                        {perfil?.email_confirmado ? '✅ Sí' : '⏳ Pendiente'}
                      </span>
                    </div>
                    <button onClick={() => setEditando(true)} className="btn btn-primary">
                      ✏️ Editar Perfil
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Contenido - Mis Pedidos */}
      {activeTab === 'pedidos' && (
        <div className="tab-content">
          <div className="pedidos-section">
            <h2>📦 Historial de Pedidos</h2>
            
            {pedidos.length > 0 ? (
              <div className="pedidos-list">
                {pedidos.map((pedido) => (
                  <div key={pedido.pedido_id} className="pedido-card">
                    <div className="pedido-header">
                      <div className="pedido-numero">
                        <span className="label">Pedido</span>
                        <span className="numero">{pedido.numero_pedido}</span>
                      </div>
                      <div className="pedido-estado">
                        <span className={`estado-badge estado-${pedido.estado}`}>
                          {getEstadoDisplay(pedido.estado)}
                        </span>
                      </div>
                      <div className="pedido-total">
                        <span className="label">Total</span>
                        <span className="monto">${pedido.total?.toFixed(2)}</span>
                      </div>
                    </div>
                    
                    <div className="pedido-info">
                      <p><strong>Fecha:</strong> {new Date(pedido.fecha_pedido).toLocaleDateString('es-MX')}</p>
                      <p><strong>Método de Pago:</strong> {pedido.metodo_pago.toUpperCase()}</p>
                      {pedido.cliente_nombre && (
                        <p><strong>Cliente:</strong> {pedido.cliente_nombre} ({pedido.cliente_email})</p>
                      )}
                    </div>
                    
                    <div className="pedido-detalles">
                      <h4>Productos</h4>
                      <table>
                        <thead>
                          <tr>
                            <th>Producto</th>
                            <th>Cantidad</th>
                            <th>Precio Unitario</th>
                            <th>Subtotal</th>
                          </tr>
                        </thead>
                        <tbody>
                          {pedido.detalles.map((detalle, idx) => (
                            <tr key={idx}>
                              <td>{detalle.producto_nombre}</td>
                              <td className="text-center">{detalle.cantidad}</td>
                              <td className="text-right">${detalle.precio_unitario?.toFixed(2)}</td>
                              <td className="text-right">${detalle.subtotal?.toFixed(2)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <p>📭 No tienes pedidos aún</p>
                <button onClick={() => navigate('/')} className="btn btn-primary">
                  🛍️ Ir a Comprar
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Contenido - Estadísticas */}
      {activeTab === 'estadisticas' && (
        <div className="tab-content">
          <div className="estadisticas-grid">
            <div className="stat-card">
              <div className="stat-icon">📦</div>
              <h3>Total de Pedidos</h3>
              <p className="stat-value">{perfil?.total_pedidos || 0}</p>
            </div>
            
            <div className="stat-card">
              <div className="stat-icon">💰</div>
              <h3>Gasto Total</h3>
              <p className="stat-value">${perfil?.gasto_total?.toFixed(2) || '0.00'}</p>
            </div>
            
            <div className="stat-card">
              <div className="stat-icon">📊</div>
              <h3>Gasto Promedio</h3>
              <p className="stat-value">
                ${(perfil?.gasto_total / (perfil?.total_pedidos || 1))?.toFixed(2) || '0.00'}
              </p>
            </div>
            
            <div className="stat-card">
              <div className="stat-icon">📅</div>
              <h3>Miembro Desde</h3>
              <p className="stat-value-date">
                {perfil?.fecha_creacion ? new Date(perfil.fecha_creacion).toLocaleDateString('es-MX') : 'N/A'}
              </p>
            </div>
          </div>

          <div className="resumen-gasto">
            <h3>💳 Resumen de Gastos</h3>
            <div className="resumen-content">
              <div className="resumen-item">
                <span>Gasto Total:</span>
                <strong>${perfil?.gasto_total?.toFixed(2) || '0.00'}</strong>
              </div>
              <div className="resumen-item">
                <span>Promedio por Compra:</span>
                <strong>${(perfil?.gasto_total / (perfil?.total_pedidos || 1))?.toFixed(2) || '0.00'}</strong>
              </div>
              <div className="resumen-item">
                <span>Número de Compras:</span>
                <strong>{perfil?.total_pedidos || 0}</strong>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Botones de acción */}
      <div className="perfil-actions">
        <button onClick={() => navigate('/')} className="btn btn-secondary">
          🏠 Ir al Inicio
        </button>
      </div>
    </div>
  );
}

// Funciones auxiliares
function getRolColor(rol) {
  const colors = {
    'cliente': 'var(--primary-color)',
    'vendedor': 'var(--success-color)',
    'gerente': 'var(--warning-color)',
    'admin_sistema': 'var(--danger-color)'
  };
  return colors[rol] || 'var(--muted-color)';
}

function getEstadoDisplay(estado) {
  const estados = {
    'pendiente': '⏳ Pendiente',
    'pagado': '✅ Pagado',
    'en_preparacion': '📦 En Preparación',
    'enviado': '🚚 Enviado',
    'entregado': '✔️ Entregado',
    'cancelado': '❌ Cancelado'
  };
  return estados[estado] || estado;
}
