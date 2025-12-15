import React, { useState, useEffect } from 'react';
import { FaExclamationTriangle, FaPlus, FaEdit, FaTrash, FaComments, FaCheckCircle, FaClock, FaTimesCircle, FaSearch, FaFilter, FaUser, FaEnvelope } from 'react-icons/fa';
import { useRol } from '../contexts/RolContext';
import '../styles/globals.css';

function GestionReclamos() {
  const { usuario } = useRol();
  const [reclamos, setReclamos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [reclamoEditando, setReclamoEditando] = useState(null);
  const [reclamoSeleccionado, setReclamoSeleccionado] = useState(null);
  const [mostrarComentarios, setMostrarComentarios] = useState(false);
  const [nuevoComentario, setNuevoComentario] = useState('');
  const [comentarioInterno, setComentarioInterno] = useState(false);
  const [filtros, setFiltros] = useState({
    estado: '',
    tipo: '',
    prioridad: '',
    busqueda: ''
  });

  const [formData, setFormData] = useState({
    titulo: '',
    descripcion: '',
    tipo: 'otro',
    prioridad: 'media',
    pedido_relacionado: ''
  });

  useEffect(() => {
    if (usuario && usuario.id) {
      cargarReclamos();
    }
  }, [filtros, usuario]);

  const cargarReclamos = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const queryParams = new URLSearchParams();
      if (filtros.estado) queryParams.append('estado', filtros.estado);
      if (filtros.tipo) queryParams.append('tipo', filtros.tipo);
      if (filtros.prioridad) queryParams.append('prioridad', filtros.prioridad);
      if (usuario && usuario.id) queryParams.append('usuario_id', usuario.id);
      
      // Si es cliente, solo ver sus reclamos
      if (usuario && usuario.rol === 'cliente') {
        queryParams.append('cliente_id', usuario.cliente_id || '');
      }

      const queryString = queryParams.toString();
      const url = `${window.API_BASE_URL}/api/reclamos/${queryString ? '?' + queryString : ''}`;
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (response.ok && data.success) {
        let reclamosFiltrados = data.reclamos || [];
        
        // Filtrar por búsqueda si existe
        if (filtros.busqueda) {
          reclamosFiltrados = reclamosFiltrados.filter(reclamo =>
            reclamo.titulo.toLowerCase().includes(filtros.busqueda.toLowerCase()) ||
            reclamo.descripcion.toLowerCase().includes(filtros.busqueda.toLowerCase())
          );
        }

        setReclamos(reclamosFiltrados);
      } else {
        throw new Error(data.message || 'Error al cargar reclamos');
      }
    } catch (error) {
      console.error('Error cargando reclamos:', error);
      setError('Error al cargar los reclamos');
    } finally {
      setLoading(false);
    }
  };

  const cargarComentarios = async (reclamoId) => {
    try {
      const response = await fetch(`${window.API_BASE_URL}/api/reclamos/${reclamoId}/comentarios/?usuario_id=${usuario?.id}`, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();
      if (response.ok && data.success) {
        return data.comentarios || [];
      }
      return [];
    } catch (error) {
      console.error('Error cargando comentarios:', error);
      return [];
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    try {
      const url = reclamoEditando 
        ? `${window.API_BASE_URL}/api/reclamos/${reclamoEditando.id}/`
        : `${window.API_BASE_URL}/api/reclamos/`;
      
      const method = reclamoEditando ? 'PUT' : 'POST';

      const datos = {
        ...formData,
        pedido_relacionado: formData.pedido_relacionado || null,
        usuario_id: usuario?.id
      };

      const response = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(datos)
      });

      const data = await response.json();

      if (response.ok && data.success) {
        cargarReclamos();
        resetForm();
        alert(reclamoEditando ? 'Reclamo actualizado exitosamente' : 'Reclamo creado exitosamente');
      } else {
        throw new Error(data.message || 'Error al guardar reclamo');
      }
    } catch (error) {
      console.error('Error guardando reclamo:', error);
      alert('Error al guardar el reclamo: ' + error.message);
    }
  };

  const handleAgregarComentario = async (e) => {
    e.preventDefault();
    if (!nuevoComentario.trim() || !reclamoSeleccionado) return;

    try {
      const response = await fetch(`${window.API_BASE_URL}/api/reclamos/${reclamoSeleccionado.id}/comentarios/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          comentario: nuevoComentario,
          es_interno: comentarioInterno,
          usuario_id: usuario?.id
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setNuevoComentario('');
        setComentarioInterno(false);
        // Recargar comentarios del reclamo seleccionado
        if (reclamoSeleccionado) {
          const comentarios = await cargarComentarios(reclamoSeleccionado.id);
          setReclamoSeleccionado({ ...reclamoSeleccionado, comentarios });
        }
        cargarReclamos();
        alert('Comentario agregado exitosamente');
      } else {
        throw new Error(data.message || 'Error al agregar comentario');
      }
    } catch (error) {
      console.error('Error agregando comentario:', error);
      alert('Error al agregar comentario: ' + error.message);
    }
  };

  const handleEditar = (reclamo) => {
    setReclamoEditando(reclamo);
    setFormData({
      titulo: reclamo.titulo,
      descripcion: reclamo.descripcion,
      tipo: reclamo.tipo,
      prioridad: reclamo.prioridad,
      pedido_relacionado: reclamo.pedido_relacionado || ''
    });
    setMostrarFormulario(true);
  };

  const handleEliminar = async (reclamoId) => {
    if (!window.confirm('¿Estás seguro de que deseas eliminar este reclamo?')) {
      return;
    }

    try {
      const response = await fetch(`${window.API_BASE_URL}/api/reclamos/${reclamoId}/?usuario_id=${usuario?.id}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (response.ok && data.success) {
        cargarReclamos();
        alert('Reclamo eliminado exitosamente');
      } else {
        throw new Error(data.message || 'Error al eliminar reclamo');
      }
    } catch (error) {
      console.error('Error eliminando reclamo:', error);
      alert('Error al eliminar el reclamo: ' + error.message);
    }
  };

  const handleCambiarEstado = async (reclamoId, nuevoEstado, resolucion = '') => {
    try {
      const response = await fetch(`${window.API_BASE_URL}/api/reclamos/${reclamoId}/?usuario_id=${usuario?.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          estado: nuevoEstado,
          resolucion: resolucion,
          usuario_id: usuario?.id
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        cargarReclamos();
        alert('Estado actualizado exitosamente');
      } else {
        throw new Error(data.message || 'Error al actualizar estado');
      }
    } catch (error) {
      console.error('Error actualizando estado:', error);
      alert('Error al actualizar estado: ' + error.message);
    }
  };

  const resetForm = () => {
    setFormData({
      titulo: '',
      descripcion: '',
      tipo: 'otro',
      prioridad: 'media',
      pedido_relacionado: ''
    });
    setReclamoEditando(null);
    setMostrarFormulario(false);
  };

  const formatearFecha = (fecha) => {
    if (!fecha) return '-';
    const date = new Date(fecha);
    return date.toLocaleDateString('es-CL', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getEstadoColor = (estado) => {
    const colores = {
      'abierto': '#ff9800',
      'en_proceso': '#2196f3',
      'resuelto': '#4caf50',
      'cerrado': '#9e9e9e'
    };
    return colores[estado] || '#666';
  };

  const getPrioridadColor = (prioridad) => {
    const colores = {
      'baja': '#4caf50',
      'media': '#ff9800',
      'alta': '#f44336',
      'urgente': '#d32f2f'
    };
    return colores[prioridad] || '#666';
  };

  const puedeEditar = (reclamo) => {
    if (!usuario) return false;
    if (usuario.rol === 'cliente') {
      return reclamo.cliente === usuario.cliente_id;
    }
    return ['vendedor', 'gerente', 'admin_sistema'].includes(usuario.rol);
  };

  const puedeEliminar = () => {
    if (!usuario) return false;
    return ['gerente', 'admin_sistema'].includes(usuario.rol);
  };

  if (loading && reclamos.length === 0) {
    return (
      <div className="reclamos-container" style={{ padding: '20px', textAlign: 'center' }}>
        <p>Cargando reclamos...</p>
      </div>
    );
  }

  return (
    <div className="reclamos-container" style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      <div className="reclamos-header" style={{ marginBottom: '30px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '20px' }}>
          <FaExclamationTriangle style={{ fontSize: '2rem', color: 'var(--primary-color)' }} />
          <div>
            <h1 style={{ margin: 0 }}>Gestión de Reclamos</h1>
            <p style={{ margin: '5px 0 0 0', color: '#666' }}>Gestiona quejas y reclamos de clientes</p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          {usuario && usuario.rol === 'cliente' && (
            <button
              onClick={() => {
                resetForm();
                setMostrarFormulario(!mostrarFormulario);
              }}
              className="btn btn-primary"
              style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              <FaPlus /> {mostrarFormulario ? 'Cancelar' : 'Nuevo Reclamo'}
            </button>
          )}
          <button
            onClick={cargarReclamos}
            className="btn btn-secondary"
          >
            Recargar
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger" style={{ marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {/* Filtros */}
      <div className="filtros-container" style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
        <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap', alignItems: 'end' }}>
          <div style={{ flex: '1', minWidth: '200px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Buscar</label>
            <div style={{ position: 'relative' }}>
              <FaSearch style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#666' }} />
              <input
                type="text"
                placeholder="Buscar por título o descripción..."
                value={filtros.busqueda}
                onChange={(e) => setFiltros({ ...filtros, busqueda: e.target.value })}
                style={{ width: '100%', padding: '8px 8px 8px 35px', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>
          </div>
          <div style={{ minWidth: '150px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Estado</label>
            <select
              value={filtros.estado}
              onChange={(e) => setFiltros({ ...filtros, estado: e.target.value })}
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">Todos</option>
              <option value="abierto">Abierto</option>
              <option value="en_proceso">En Proceso</option>
              <option value="resuelto">Resuelto</option>
              <option value="cerrado">Cerrado</option>
            </select>
          </div>
          <div style={{ minWidth: '150px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Tipo</label>
            <select
              value={filtros.tipo}
              onChange={(e) => setFiltros({ ...filtros, tipo: e.target.value })}
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">Todos</option>
              <option value="producto">Producto</option>
              <option value="entrega">Entrega</option>
              <option value="servicio">Servicio</option>
              <option value="pago">Pago</option>
              <option value="otro">Otro</option>
            </select>
          </div>
          <div style={{ minWidth: '150px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Prioridad</label>
            <select
              value={filtros.prioridad}
              onChange={(e) => setFiltros({ ...filtros, prioridad: e.target.value })}
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">Todas</option>
              <option value="baja">Baja</option>
              <option value="media">Media</option>
              <option value="alta">Alta</option>
              <option value="urgente">Urgente</option>
            </select>
          </div>
        </div>
      </div>

      {/* Formulario de creación/edición */}
      {mostrarFormulario && (
        <div className="formulario-container" style={{ marginBottom: '30px', padding: '20px', backgroundColor: '#fff', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <h2 style={{ marginTop: 0 }}>{reclamoEditando ? 'Editar Reclamo' : 'Nuevo Reclamo'}</h2>
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Título *</label>
              <input
                type="text"
                required
                value={formData.titulo}
                onChange={(e) => setFormData({ ...formData, titulo: e.target.value })}
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                placeholder="Título breve del reclamo"
              />
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Descripción *</label>
              <textarea
                required
                value={formData.descripcion}
                onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px', minHeight: '100px' }}
                placeholder="Descripción detallada del reclamo"
              />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Tipo *</label>
                <select
                  required
                  value={formData.tipo}
                  onChange={(e) => setFormData({ ...formData, tipo: e.target.value })}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value="producto">Producto</option>
                  <option value="entrega">Entrega</option>
                  <option value="servicio">Servicio</option>
                  <option value="pago">Pago</option>
                  <option value="otro">Otro</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Prioridad *</label>
                <select
                  required
                  value={formData.prioridad}
                  onChange={(e) => setFormData({ ...formData, prioridad: e.target.value })}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value="baja">Baja</option>
                  <option value="media">Media</option>
                  <option value="alta">Alta</option>
                  <option value="urgente">Urgente</option>
                </select>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button type="button" onClick={resetForm} className="btn btn-secondary">Cancelar</button>
              <button type="submit" className="btn btn-primary">Guardar</button>
            </div>
          </form>
        </div>
      )}

      {/* Lista de reclamos */}
      <div className="reclamos-lista">
        {reclamos.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
            <FaExclamationTriangle style={{ fontSize: '3rem', color: '#ccc', marginBottom: '15px' }} />
            <p>No hay reclamos para mostrar</p>
          </div>
        ) : (
          reclamos.map((reclamo) => (
            <div key={reclamo.id} className="reclamo-card" style={{ 
              marginBottom: '20px', 
              padding: '20px', 
              backgroundColor: '#fff', 
              borderRadius: '8px', 
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              borderLeft: `4px solid ${getEstadoColor(reclamo.estado)}`
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '15px' }}>
                <div style={{ flex: '1' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                    <h3 style={{ margin: 0 }}>#{reclamo.id} - {reclamo.titulo}</h3>
                    <span style={{ 
                      padding: '4px 8px', 
                      borderRadius: '4px', 
                      fontSize: '0.85rem',
                      backgroundColor: getEstadoColor(reclamo.estado),
                      color: '#fff'
                    }}>
                      {reclamo.estado_display}
                    </span>
                    <span style={{ 
                      padding: '4px 8px', 
                      borderRadius: '4px', 
                      fontSize: '0.85rem',
                      backgroundColor: getPrioridadColor(reclamo.prioridad),
                      color: '#fff'
                    }}>
                      {reclamo.prioridad_display}
                    </span>
                  </div>
                  <div style={{ color: '#666', fontSize: '0.9rem', marginBottom: '10px' }}>
                    <div><strong>Tipo:</strong> {reclamo.tipo_display}</div>
                    <div><strong>Cliente:</strong> {reclamo.cliente_email}</div>
                    {reclamo.asignado_a_email && (
                      <div><strong>Asignado a:</strong> {reclamo.asignado_a_email}</div>
                    )}
                    <div><strong>Fecha:</strong> {formatearFecha(reclamo.fecha_creacion)}</div>
                    {reclamo.tiempo_resolucion_horas && (
                      <div><strong>Tiempo de resolución:</strong> {reclamo.tiempo_resolucion_horas} horas</div>
                    )}
                  </div>
                  <p style={{ margin: '10px 0', color: '#333' }}>{reclamo.descripcion}</p>
                  {reclamo.resolucion && (
                    <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#e8f5e9', borderRadius: '4px' }}>
                      <strong>Resolución:</strong> {reclamo.resolucion}
                    </div>
                  )}
                </div>
                <div style={{ display: 'flex', gap: '5px', flexDirection: 'column' }}>
                  {puedeEditar(reclamo) && (
                    <>
                      <button
                        onClick={() => handleEditar(reclamo)}
                        className="btn btn-sm btn-secondary"
                        style={{ fontSize: '0.85rem' }}
                      >
                        <FaEdit /> Editar
                      </button>
                      {['vendedor', 'gerente', 'admin_sistema'].includes(usuario?.rol) && (
                        <>
                          <button
                            onClick={() => handleCambiarEstado(reclamo.id, 'en_proceso')}
                            className="btn btn-sm btn-info"
                            style={{ fontSize: '0.85rem' }}
                            disabled={reclamo.estado === 'en_proceso'}
                          >
                            <FaClock /> En Proceso
                          </button>
                          <button
                            onClick={() => {
                              const resolucion = prompt('Ingrese la resolución del reclamo:');
                              if (resolucion) {
                                handleCambiarEstado(reclamo.id, 'resuelto', resolucion);
                              }
                            }}
                            className="btn btn-sm btn-success"
                            style={{ fontSize: '0.85rem' }}
                            disabled={reclamo.estado === 'resuelto' || reclamo.estado === 'cerrado'}
                          >
                            <FaCheckCircle /> Resolver
                          </button>
                          <button
                            onClick={() => handleCambiarEstado(reclamo.id, 'cerrado')}
                            className="btn btn-sm btn-secondary"
                            style={{ fontSize: '0.85rem' }}
                            disabled={reclamo.estado === 'cerrado'}
                          >
                            <FaTimesCircle /> Cerrar
                          </button>
                        </>
                      )}
                    </>
                  )}
                  {puedeEliminar() && (
                    <button
                      onClick={() => handleEliminar(reclamo.id)}
                      className="btn btn-sm btn-danger"
                      style={{ fontSize: '0.85rem' }}
                    >
                      <FaTrash /> Eliminar
                    </button>
                  )}
                  <button
                    onClick={async () => {
                      if (reclamoSeleccionado?.id === reclamo.id) {
                        setReclamoSeleccionado(null);
                        setMostrarComentarios(false);
                      } else {
                        const comentarios = await cargarComentarios(reclamo.id);
                        setReclamoSeleccionado({ ...reclamo, comentarios });
                        setMostrarComentarios(true);
                      }
                    }}
                    className="btn btn-sm btn-primary"
                    style={{ fontSize: '0.85rem' }}
                  >
                    <FaComments /> Comentarios ({reclamo.comentarios?.length || 0})
                  </button>
                </div>
              </div>

              {/* Sección de comentarios */}
              {mostrarComentarios && reclamoSeleccionado?.id === reclamo.id && (
                <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                  <h4 style={{ marginTop: 0 }}>Comentarios</h4>
                  {reclamo.comentarios && reclamo.comentarios.length > 0 ? (
                    <div style={{ marginBottom: '15px' }}>
                      {reclamo.comentarios.map((comentario) => (
                        <div key={comentario.id} style={{ 
                          marginBottom: '10px', 
                          padding: '10px', 
                          backgroundColor: comentario.es_interno ? '#fff3cd' : '#fff',
                          borderRadius: '4px',
                          borderLeft: `3px solid ${comentario.es_interno ? '#ffc107' : '#2196f3'}`
                        }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                            <strong>{comentario.usuario_nombre || comentario.usuario_email}</strong>
                            <span style={{ fontSize: '0.85rem', color: '#666' }}>
                              {formatearFecha(comentario.fecha_creacion)}
                              {comentario.es_interno && <span style={{ marginLeft: '10px', color: '#ff9800' }}>(Interno)</span>}
                            </span>
                          </div>
                          <p style={{ margin: 0 }}>{comentario.comentario}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p style={{ color: '#666', fontStyle: 'italic' }}>No hay comentarios aún</p>
                  )}
                  <form onSubmit={handleAgregarComentario}>
                    <div style={{ marginBottom: '10px' }}>
                      <textarea
                        required
                        value={nuevoComentario}
                        onChange={(e) => setNuevoComentario(e.target.value)}
                        placeholder="Escribe un comentario..."
                        style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px', minHeight: '80px' }}
                      />
                    </div>
                    {['vendedor', 'gerente', 'admin_sistema'].includes(usuario?.rol) && (
                      <div style={{ marginBottom: '10px' }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <input
                            type="checkbox"
                            checked={comentarioInterno}
                            onChange={(e) => setComentarioInterno(e.target.checked)}
                          />
                          <span>Comentario interno (solo visible para staff)</span>
                        </label>
                      </div>
                    )}
                    <button type="submit" className="btn btn-primary btn-sm">Agregar Comentario</button>
                  </form>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default GestionReclamos;

