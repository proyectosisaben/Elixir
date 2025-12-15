import React, { useState, useEffect } from 'react';
import { useRol } from '../contexts/RolContext';
import '../styles/globals.css';
import {
  FaClipboardList,
  FaCheck,
  FaTimes,
  FaClock,
  FaExclamationTriangle,
  FaUser,
  FaBox,
  FaDollarSign,
  FaTag,
  FaEye,
  FaFilter,
  FaSearch
} from 'react-icons/fa';

function AutorizacionesGerente() {
  const { usuario } = useRol();
  const [solicitudes, setSolicitudes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filtros, setFiltros] = useState({
    estado: '',  // Cambiado de 'pendiente' a '' para mostrar todas
    tipo: '',
    solicitante_id: '',
    fecha_inicio: '',
    fecha_fin: '',
    prioridad: '',
    pagina: 1,
    items_por_pagina: 10
  });
  const [solicitudDetalle, setSolicitudDetalle] = useState(null);
  const [mostrarDetalle, setMostrarDetalle] = useState(false);
  const [comentarioRespuesta, setComentarioRespuesta] = useState('');

  useEffect(() => {
    if (usuario && (usuario.rol === 'gerente' || usuario.rol === 'admin_sistema')) {
      cargarSolicitudes();
    }
  }, [usuario, filtros]);

  const cargarSolicitudes = async () => {
    try {
      setLoading(true);
      const queryParams = new URLSearchParams();
      queryParams.append('user_id', usuario?.id);

      // Agregar filtros
      Object.entries(filtros).forEach(([key, value]) => {
        if (value) queryParams.append(key, value);
      });

      const response = await fetch("${window.API_BASE_URL}/api/autorizaciones/solicitudes/?${queryParams.toString()}`);
      const data = await response.json();

      if (response.ok && data.success) {
        const solicitudesData = data.solicitudes || [];
        console.log(`Cargadas ${solicitudesData.length} solicitudes:`, solicitudesData.map(s => ({id: s.id, estado: s.estado})));
        setSolicitudes(solicitudesData);

        // Mostrar resumen de estados para debug
        const estados = {};
        solicitudesData.forEach(s => {
          estados[s.estado] = (estados[s.estado] || 0) + 1;
        });
        console.log('Resumen de estados:', estados);
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

  const gestionarSolicitud = async (solicitudId, accion) => {
    if (accion === 'rechazar' && !comentarioRespuesta.trim()) {
      alert('Debe proporcionar un comentario para rechazar la solicitud.');
      return;
    }

    try {
      console.log(`🔄 FRONTEND - Iniciando gestión de solicitud ${solicitudId} (${accion})`);

      // Primero probar la conexión con una solicitud de test
      console.log('🔍 FRONTEND - Probando conexión con test...');
      const testResponse = await fetch("${window.API_BASE_URL}/api/autorizaciones/${solicitudId}/test/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ test: true, user_id: usuario.id, accion: accion })
      });

      if (testResponse.ok) {
        console.log('✅ FRONTEND - Test de conexión exitoso');
      } else {
        console.log('❌ FRONTEND - Test de conexión falló:', testResponse.status);
      }

      const requestData = {
        user_id: usuario.id,
        accion: accion,
        comentario: comentarioRespuesta
      };

      console.log('📤 FRONTEND - Enviando datos reales:', JSON.stringify(requestData, null, 2));

      const response = await fetch("${window.API_BASE_URL}/api/autorizaciones/${solicitudId}/gestionar/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      console.log(`📥 FRONTEND - Respuesta HTTP: ${response.status} ${response.statusText}`);

      const data = await response.json();
      console.log('📋 FRONTEND - Datos respuesta:', data);

      if (response.ok && data.success) {
        alert(`Solicitud ${accion === 'aprobar' ? 'aprobada' : 'rechazada'} exitosamente`);
        console.log(`Solicitud ${solicitudId} ${accion === 'aprobar' ? 'aprobada' : 'rechazada'} exitosamente`);
        setMostrarDetalle(false);
        setComentarioRespuesta('');

        // Limpiar filtros para mostrar todas las solicitudes y ver el cambio
        setFiltros(prev => ({ ...prev, estado: '', pagina: 1 }));

        // Pequeño delay para asegurar que el backend procesó el cambio
        setTimeout(() => {
          cargarSolicitudes();
        }, 500);
      } else {
        throw new Error(data.message || 'Error al gestionar solicitud');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error al gestionar solicitud: ' + error.message);
    }
  };

  const verDetalleSolicitud = (solicitud) => {
    setSolicitudDetalle(solicitud);
    setMostrarDetalle(true);
    setComentarioRespuesta('');
  };

  const handleFiltroChange = (e) => {
    const { name, value } = e.target;
    setFiltros(prev => ({ ...prev, [name]: value, pagina: 1 })); // Reset página al cambiar filtros
  };

  const aplicarFiltros = () => {
    setFiltros(prev => ({ ...prev, pagina: 1 }));
    cargarSolicitudes();
  };

  const limpiarFiltros = () => {
    setFiltros({
      estado: '',
      tipo: '',
      solicitante_id: '',
      fecha_inicio: '',
      fecha_fin: '',
      prioridad: '',
      pagina: 1,
      items_por_pagina: 10
    });
  };

  const cambiarPagina = (nuevaPagina) => {
    setFiltros(prev => ({ ...prev, pagina: nuevaPagina }));
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

  const getPrioridadColor = (prioridad) => {
    switch (prioridad) {
      case 'urgente': return '#dc3545';
      case 'alta': return '#fd7e14';
      case 'media': return '#ffc107';
      case 'baja': return '#28a745';
      default: return '#6c757d';
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

  const compararDatos = (anteriores, nuevos) => {
    const cambios = [];
    if (anteriores && nuevos) {
      Object.keys(nuevos).forEach(key => {
        if (anteriores[key] !== nuevos[key]) {
          cambios.push({
            campo: key,
            anterior: anteriores[key],
            nuevo: nuevos[key]
          });
        }
      });
    }
    return cambios;
  };

  if (!usuario || (usuario.rol !== 'gerente' && usuario.rol !== 'admin_sistema')) {
    return (
      <div className="autorizaciones-container">
        <div className="alert alert-danger text-center">
          <h3>❌ Acceso Denegado</h3>
          <p>Solo los gerentes pueden acceder a esta sección.</p>
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
            <h1>Gestión de Autorizaciones</h1>
            <p>Aprueba o rechaza solicitudes de cambios en el inventario</p>
          </div>
        </div>
      </div>

      <div className="autorizaciones-main">
        {/* Filtros Avanzados */}
        <div className="filtros-section">
          <h3>Filtros Avanzados</h3>
          <div className="filtros-grid">
            <div className="filtro-group">
              <label htmlFor="estado">Estado:</label>
              <select
                id="estado"
                name="estado"
                value={filtros.estado}
                onChange={handleFiltroChange}
              >
                <option value="">Todas</option>
                <option value="pendiente">Pendientes</option>
                <option value="aprobada">Aprobadas</option>
                <option value="rechazada">Rechazadas</option>
                <option value="cancelada">Canceladas</option>
              </select>
            </div>

            <div className="filtro-group">
              <label htmlFor="tipo">Tipo:</label>
              <select
                id="tipo"
                name="tipo"
                value={filtros.tipo}
                onChange={handleFiltroChange}
              >
                <option value="">Todos</option>
                <option value="cambio_stock">Cambio de Stock</option>
                <option value="nuevo_producto">Nuevo Producto</option>
                <option value="modificar_precio">Modificar Precio</option>
                <option value="eliminar_producto">Eliminar Producto</option>
              </select>
            </div>

            <div className="filtro-group">
              <label htmlFor="prioridad">Prioridad:</label>
              <select
                id="prioridad"
                name="prioridad"
                value={filtros.prioridad}
                onChange={handleFiltroChange}
              >
                <option value="">Todas</option>
                <option value="urgente">Urgente</option>
                <option value="alta">Alta</option>
                <option value="media">Media</option>
                <option value="baja">Baja</option>
              </select>
            </div>

            <div className="filtro-group">
              <label htmlFor="fecha_inicio">Fecha Inicio:</label>
              <input
                type="date"
                id="fecha_inicio"
                name="fecha_inicio"
                value={filtros.fecha_inicio}
                onChange={handleFiltroChange}
              />
            </div>

            <div className="filtro-group">
              <label htmlFor="fecha_fin">Fecha Fin:</label>
              <input
                type="date"
                id="fecha_fin"
                name="fecha_fin"
                value={filtros.fecha_fin}
                onChange={handleFiltroChange}
              />
            </div>

            <div className="filtro-group">
              <label htmlFor="items_por_pagina">Items por página:</label>
              <select
                id="items_por_pagina"
                name="items_por_pagina"
                value={filtros.items_por_pagina}
                onChange={handleFiltroChange}
              >
                <option value="5">5</option>
                <option value="10">10</option>
                <option value="20">20</option>
                <option value="50">50</option>
              </select>
            </div>
          </div>

          <div className="filtros-actions">
            <button className="btn-aplicar" onClick={aplicarFiltros}>
              Aplicar Filtros
            </button>
            <button className="btn-limpiar" onClick={limpiarFiltros}>
              Limpiar Filtros
            </button>
          </div>
        </div>

        {/* Estadísticas rápidas */}
        <div className="estadisticas-autorizaciones">
          <div className="metrica-card">
            <div className="metrica-header">
              <FaClock className="metrica-icon" />
              <h3>Pendientes</h3>
            </div>
            <p className="metrica-valor">{(() => {
              const pendientes = solicitudes.filter(s => s.estado === 'pendiente').length;
              console.log(`Estadísticas - Pendientes: ${pendientes}`);
              return pendientes;
            })()}</p>
          </div>
          <div className="metrica-card">
            <div className="metrica-header">
              <FaCheck className="metrica-icon" />
              <h3>Aprobadas (Hoy)</h3>
            </div>
            <p className="metrica-valor">
              {solicitudes.filter(s =>
                s.estado === 'aprobada' &&
                new Date(s.fecha_respuesta).toDateString() === new Date().toDateString()
              ).length}
            </p>
          </div>
          <div className="metrica-card">
            <div className="metrica-header">
              <FaTimes className="metrica-icon" />
              <h3>Rechazadas (Hoy)</h3>
            </div>
            <p className="metrica-valor">
              {solicitudes.filter(s =>
                s.estado === 'rechazada' &&
                new Date(s.fecha_respuesta).toDateString() === new Date().toDateString()
              ).length}
            </p>
          </div>
        </div>

        {/* Lista de solicitudes */}
        <div className="solicitudes-section">
          <h3>Solicitudes ({solicitudes.length})</h3>

          {solicitudes.length === 0 ? (
            <div className="empty-state">
              <FaClipboardList className="empty-icon" />
              <p>No hay solicitudes con el filtro seleccionado.</p>
            </div>
          ) : (
            <div className="solicitudes-list">
              {solicitudes.map(solicitud => (
                <div key={solicitud.id} className="solicitud-card">
                  <div className="solicitud-header">
                    <div className="solicitud-titulo">
                      <h4>Solicitud #{solicitud.id}</h4>
                      <span className="tipo-solicitud">{solicitud.tipo_solicitud}</span>
                      <span
                        className="prioridad-badge"
                        style={{ backgroundColor: getPrioridadColor(solicitud.prioridad) }}
                      >
                        {solicitud.prioridad}
                      </span>
                    </div>
                    <div className="solicitud-estado" style={{ backgroundColor: getEstadoColor(solicitud.estado) }}>
                      {getEstadoIcono(solicitud.estado)}
                      <span>{solicitud.estado}</span>
                    </div>
                  </div>

                  <div className="solicitud-content">
                    <div className="solicitud-info">
                      <p><strong>Solicitante:</strong> {solicitud.solicitante?.email || 'N/A'}</p>
                      <p><strong>Producto:</strong> {solicitud.producto_afectado?.nombre || 'N/A'}</p>
                      <p><strong>Fecha:</strong> {formatearFecha(solicitud.fecha_solicitud)}</p>
                    </div>

                    <div className="solicitud-motivo">
                      <p><strong>Motivo:</strong> {solicitud.motivo}</p>
                    </div>

                    <div className="solicitud-actions">
                      <button
                        className="btn-ver-detalle"
                        onClick={() => verDetalleSolicitud(solicitud)}
                      >
                        <FaEye /> Ver Detalle
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modal de detalle de solicitud */}
      {mostrarDetalle && solicitudDetalle && (
        <div className="modal-overlay" onClick={() => setMostrarDetalle(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Detalle de Solicitud #{solicitudDetalle.id}</h3>
              <button className="btn-cerrar" onClick={() => setMostrarDetalle(false)}>×</button>
            </div>

            <div className="modal-body">
              <div className="detalle-grid">
                <div className="detalle-section">
                  <h4>Información General</h4>
                  <p><strong>Tipo:</strong> {solicitudDetalle.tipo_solicitud}</p>
                  <p><strong>Solicitante:</strong> {solicitudDetalle.solicitante?.email}</p>
                  <p><strong>Producto:</strong> {solicitudDetalle.producto_afectado?.nombre}</p>
                  <p><strong>Fecha:</strong> {formatearFecha(solicitudDetalle.fecha_solicitud)}</p>
                  <p><strong>Prioridad:</strong> {solicitudDetalle.prioridad}</p>
                </div>

                <div className="detalle-section">
                  <h4>Motivo</h4>
                  <p>{solicitudDetalle.motivo}</p>
                </div>

                <div className="detalle-section">
                  <h4>Cambios Solicitados</h4>
                  <div className="cambios-list">
                    {/* Aquí mostraríamos los cambios comparados */}
                    <p>Datos anteriores vs nuevos datos solicitados</p>
                  </div>
                </div>
              </div>

              {solicitudDetalle.estado === 'pendiente' ? (
                <div className="modal-actions">
                  <div className="comentario-section">
                    <label htmlFor="comentario">Comentario (requerido para rechazar):</label>
                    <textarea
                      id="comentario"
                      value={comentarioRespuesta}
                      onChange={(e) => setComentarioRespuesta(e.target.value)}
                      placeholder="Explique el motivo de su decisión..."
                      rows="3"
                    />
                  </div>

                  <div className="botones-actions">
                    <button
                      className="btn-rechazar"
                      onClick={() => gestionarSolicitud(solicitudDetalle.id, 'rechazar')}
                    >
                      <FaTimes /> Rechazar
                    </button>
                    <button
                      className="btn-aprobar"
                      onClick={() => gestionarSolicitud(solicitudDetalle.id, 'aprobar')}
                    >
                      <FaCheck /> Aprobar
                    </button>
                  </div>
                </div>
              ) : (
                <div className="modal-info-procesada">
                  <div className="estado-procesado">
                    <h4>Estado: <span className={`estado-${solicitudDetalle.estado}`}>
                      {solicitudDetalle.estado === 'aprobada' ? '✅ Aprobada' :
                       solicitudDetalle.estado === 'rechazada' ? '❌ Rechazada' : solicitudDetalle.estado}
                    </span></h4>
                    {solicitudDetalle.fecha_respuesta && (
                      <p><strong>Fecha de respuesta:</strong> {formatearFecha(solicitudDetalle.fecha_respuesta)}</p>
                    )}
                    {solicitudDetalle.comentario_respuesta && (
                      <div className="comentario-respuesta">
                        <strong>Comentario:</strong>
                        <p>{solicitudDetalle.comentario_respuesta}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default AutorizacionesGerente;
