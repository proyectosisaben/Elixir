import React, { useState, useEffect } from 'react';
import { useRol } from '../contexts/RolContext';
import '../styles/globals.css';
import {
  FaPlus,
  FaClipboardList,
  FaClock,
  FaCheck,
  FaTimes,
  FaExclamationTriangle,
  FaPaperPlane,
  FaEdit,
  FaTrash,
  FaDollarSign,
  FaBox,
  FaTag
} from 'react-icons/fa';

function AutorizacionesVendedor() {
  const { usuario } = useRol();
  const [solicitudes, setSolicitudes] = useState([]);
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Estado del formulario
  const [formData, setFormData] = useState({
    tipo_solicitud: 'cambio_stock',
    modelo_afectado: 'Producto',
    id_objeto_afectado: '',
    datos_anteriores: {},
    datos_nuevos: {},
    motivo: ''
  });

  const [productos, setProductos] = useState([]);
  const [productoSeleccionado, setProductoSeleccionado] = useState(null);

  useEffect(() => {
    if (usuario && usuario.rol === 'vendedor') {
      cargarSolicitudes();
      cargarProductos();
    }
  }, [usuario]);

  const cargarSolicitudes = async () => {
    try {
      setLoading(true);
      const response = await fetch("${window.API_BASE_URL}/api/autorizaciones/solicitudes/?user_id=${usuario?.id}`);
      const data = await response.json();

      if (response.ok && data.success) {
        setSolicitudes(data.solicitudes || []);
      } else {
        throw new Error(data.message || 'Error al cargar solicitudes');
      }
    } catch (err) {
      console.error('Error cargando solicitudes:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const cargarProductos = async () => {
    try {
      const response = await fetch("${window.API_BASE_URL}/api/productos/');
      const data = await response.json();
      if (response.ok) {
        setProductos(data.productos || []);
      }
    } catch (error) {
      console.error('Error cargando productos:', error);
    }
  };

  const handleProductoChange = (e) => {
    const productoId = e.target.value;
    const producto = productos.find(p => p.id.toString() === productoId);

    if (producto) {
      setProductoSeleccionado(producto);
      setFormData(prev => ({
        ...prev,
        id_objeto_afectado: productoId,
        datos_anteriores: {
          nombre: producto.nombre,
          precio: producto.precio,
          stock: producto.stock,
          stock_minimo: producto.stock_minimo
        }
      }));
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleDatosNuevosChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      datos_nuevos: {
        ...prev.datos_nuevos,
        [name]: value
      }
    }));
  };

  const enviarSolicitud = async (e) => {
    e.preventDefault();

    try {
      const solicitudData = {
        ...formData,
        user_id: usuario.id  // Agregar user_id para autenticación
      };

      const response = await fetch("${window.API_BASE_URL}/api/autorizaciones/crear/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(solicitudData)
      });

      const data = await response.json();

      if (response.ok && data.success) {
        alert('Solicitud enviada exitosamente');
        setMostrarFormulario(false);
        setFormData({
          tipo_solicitud: 'cambio_stock',
          modelo_afectado: 'Producto',
          id_objeto_afectado: '',
          datos_anteriores: {},
          datos_nuevos: {},
          motivo: ''
        });
        setProductoSeleccionado(null);
        cargarSolicitudes();
      } else {
        throw new Error(data.message || 'Error al enviar solicitud');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error al enviar solicitud: ' + error.message);
    }
  };

  const getEstadoColor = (estado) => {
    switch (estado) {
      case 'pendiente': return '#ffc107';
      case 'aprobada': return '#28a745';
      case 'rechazada': return '#dc3545';
      case 'cancelada': return '#6c757d';
      default: return '#6c757d';
    }
  };

  const getEstadoIcono = (estado) => {
    switch (estado) {
      case 'pendiente': return <FaClock />;
      case 'aprobada': return <FaCheck />;
      case 'rechazada': return <FaTimes />;
      case 'cancelada': return <FaTimes />;
      default: return <FaExclamationTriangle />;
    }
  };

  const formatearFecha = (fecha) => {
    if (!fecha) return 'N/A';
    try {
      return new Date(fecha).toLocaleString('es-CL');
    } catch {
      return fecha;
    }
  };

  if (!usuario || usuario.rol !== 'vendedor') {
    return (
      <div className="autorizaciones-container">
        <div className="alert alert-danger text-center">
          <h3>❌ Acceso Denegado</h3>
          <p>Solo los vendedores pueden acceder a esta sección.</p>
          <a href="/login" className="btn btn-primary">Iniciar Sesión</a>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="autorizaciones-container">
        <div className="loading">Cargando solicitudes...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="autorizaciones-container">
        <div className="alert alert-danger text-center">
          <h3>❌ Error</h3>
          <p>{error}</p>
          <button onClick={cargarSolicitudes} className="btn btn-primary">Reintentar</button>
        </div>
      </div>
    );
  }

  return (
    <div className="autorizaciones-container">
      <div className="autorizaciones-header">
        <div className="header-content">
          <FaClipboardList className="header-icon" />
          <div>
            <h1>Solicitudes de Autorización</h1>
            <p>Gestiona tus solicitudes de cambios en el inventario</p>
          </div>
        </div>
        <button
          className="btn-nueva-solicitud"
          onClick={() => setMostrarFormulario(!mostrarFormulario)}
        >
          <FaPlus /> {mostrarFormulario ? 'Cancelar' : 'Nueva Solicitud'}
        </button>
      </div>

      <div className="autorizaciones-main">
        {/* Formulario de nueva solicitud */}
        {mostrarFormulario && (
          <div className="solicitud-form-section">
            <h3>
              <FaPaperPlane /> Nueva Solicitud de Autorización
            </h3>
            <form onSubmit={enviarSolicitud} className="solicitud-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="tipo_solicitud">Tipo de Solicitud</label>
                  <select
                    id="tipo_solicitud"
                    name="tipo_solicitud"
                    value={formData.tipo_solicitud}
                    onChange={handleInputChange}
                    required
                  >
                    <option value="cambio_stock">Cambio de Stock</option>
                    <option value="nuevo_producto">Nuevo Producto</option>
                    <option value="modificar_precio">Modificar Precio</option>
                    <option value="eliminar_producto">Eliminar Producto</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="producto">Producto Afectado</label>
                  <select
                    id="producto"
                    value={formData.id_objeto_afectado}
                    onChange={handleProductoChange}
                    required
                  >
                    <option value="">Seleccionar producto...</option>
                    {productos.map(producto => (
                      <option key={producto.id} value={producto.id}>
                        {producto.nombre} (Stock: {producto.stock})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Mostrar datos actuales del producto */}
              {productoSeleccionado && (
                <div className="datos-actuales">
                  <h4>Datos Actuales del Producto</h4>
                  <div className="datos-grid">
                    <div className="dato-item">
                      <FaBox className="dato-icon" />
                      <span>Stock: {productoSeleccionado.stock}</span>
                    </div>
                    <div className="dato-item">
                      <FaDollarSign className="dato-icon" />
                      <span>Precio: ${productoSeleccionado.precio}</span>
                    </div>
                    <div className="dato-item">
                      <FaTag className="dato-icon" />
                      <span>Stock Mínimo: {productoSeleccionado.stock_minimo}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Campos para datos nuevos según el tipo de solicitud */}
              <div className="datos-nuevos">
                <h4>Datos Nuevos Solicitados</h4>
                <div className="form-row">
                  {formData.tipo_solicitud === 'cambio_stock' && (
                    <div className="form-group">
                      <label htmlFor="nuevo_stock">Nuevo Stock</label>
                      <input
                        type="number"
                        id="nuevo_stock"
                        name="stock"
                        onChange={handleDatosNuevosChange}
                        placeholder="Ingrese el nuevo stock"
                        min="0"
                        required
                      />
                    </div>
                  )}

                  {formData.tipo_solicitud === 'modificar_precio' && (
                    <div className="form-group">
                      <label htmlFor="nuevo_precio">Nuevo Precio</label>
                      <input
                        type="number"
                        id="nuevo_precio"
                        name="precio"
                        onChange={handleDatosNuevosChange}
                        placeholder="Ingrese el nuevo precio"
                        min="0"
                        step="0.01"
                        required
                      />
                    </div>
                  )}
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="motivo">Motivo de la Solicitud</label>
                <textarea
                  id="motivo"
                  name="motivo"
                  value={formData.motivo}
                  onChange={handleInputChange}
                  placeholder="Explique detalladamente el motivo de este cambio..."
                  rows="4"
                  required
                />
              </div>

              <div className="form-actions">
                <button type="button" className="btn-cancelar" onClick={() => setMostrarFormulario(false)}>
                  Cancelar
                </button>
                <button type="submit" className="btn-enviar">
                  <FaPaperPlane /> Enviar Solicitud
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Lista de solicitudes */}
        <div className="solicitudes-section">
          <h3>Mis Solicitudes ({solicitudes.length})</h3>

          {solicitudes.length === 0 ? (
            <div className="empty-state">
              <FaClipboardList className="empty-icon" />
              <p>No tienes solicitudes de autorización.</p>
              <p>Haz clic en "Nueva Solicitud" para crear una.</p>
            </div>
          ) : (
            <div className="solicitudes-list">
              {solicitudes.map(solicitud => (
                <div key={solicitud.id} className="solicitud-card">
                  <div className="solicitud-header">
                    <div className="solicitud-titulo">
                      <h4>Solicitud #{solicitud.id}</h4>
                      <span className="tipo-solicitud">{solicitud.tipo_solicitud}</span>
                    </div>
                    <div className="solicitud-estado" style={{ backgroundColor: getEstadoColor(solicitud.estado) }}>
                      {getEstadoIcono(solicitud.estado)}
                      <span>{solicitud.estado}</span>
                    </div>
                  </div>

                  <div className="solicitud-content">
                    <div className="solicitud-info">
                      <p><strong>Producto:</strong> {solicitud.producto_afectado?.nombre || 'N/A'}</p>
                      <p><strong>Fecha:</strong> {formatearFecha(solicitud.fecha_solicitud)}</p>
                      <p><strong>Prioridad:</strong> {solicitud.prioridad}</p>
                    </div>

                    <div className="solicitud-motivo">
                      <p><strong>Motivo:</strong> {solicitud.motivo}</p>
                      {solicitud.comentario_respuesta && (
                        <p><strong>Respuesta:</strong> {solicitud.comentario_respuesta}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AutorizacionesVendedor;
