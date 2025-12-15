import React, { useState, useEffect } from 'react';
import { FaTicketAlt, FaPlus, FaEdit, FaTrash, FaCheckCircle, FaTimesCircle, FaSearch, FaFilter } from 'react-icons/fa';
import { useRol } from '../contexts/RolContext';
import '../styles/globals.css';

function GestionCupones() {
  const { usuario } = useRol();
  const [cupones, setCupones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [cuponEditando, setCuponEditando] = useState(null);
  const [filtros, setFiltros] = useState({
    activo: '',
    tipo_descuento: '',
    busqueda: ''
  });

  const [formData, setFormData] = useState({
    codigo: '',
    tipo_descuento: 'porcentaje',
    descuento_porcentaje: '',
    descuento_monto: '',
    fecha_inicio: '',
    fecha_fin: '',
    usos_maximos: 1,
    monto_minimo: 0,
    descripcion: '',
    activo: true
  });

  useEffect(() => {
    if (usuario && (usuario.rol === 'gerente' || usuario.rol === 'admin_sistema')) {
      cargarCupones();
    }
  }, [filtros, usuario]);

  const cargarCupones = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const queryParams = new URLSearchParams();
      if (filtros.activo) queryParams.append('activo', filtros.activo);
      if (filtros.tipo_descuento) queryParams.append('tipo_descuento', filtros.tipo_descuento);
      if (filtros.busqueda) queryParams.append('search', filtros.busqueda);

      // Agregar usuario_id para autenticación
      if (usuario && usuario.id) {
        queryParams.append('usuario_id', usuario.id);
      }

      const queryString = queryParams.toString();
      const url = `http://localhost:8000/api/cupones/${queryString ? '?' + queryString : ''}`;
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (response.ok && data.success) {
        let cuponesFiltrados = data.cupones || [];
        
        // Filtrar por búsqueda si existe
        if (filtros.busqueda) {
          cuponesFiltrados = cuponesFiltrados.filter(cupon =>
            cupon.codigo.toLowerCase().includes(filtros.busqueda.toLowerCase()) ||
            (cupon.descripcion && cupon.descripcion.toLowerCase().includes(filtros.busqueda.toLowerCase()))
          );
        }

        setCupones(cuponesFiltrados);
      } else {
        throw new Error(data.message || 'Error al cargar cupones');
      }
    } catch (error) {
      console.error('Error cargando cupones:', error);
      setError('Error al cargar los cupones');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    try {
      const url = cuponEditando 
        ? `http://localhost:8000/api/cupones/${cuponEditando.id}/`
        : 'http://localhost:8000/api/cupones/';
      
      const method = cuponEditando ? 'PUT' : 'POST';

      // Convertir fechas a formato ISO para el backend
      const fechaInicioISO = formData.fecha_inicio ? new Date(formData.fecha_inicio).toISOString() : '';
      const fechaFinISO = formData.fecha_fin ? new Date(formData.fecha_fin).toISOString() : '';

      const datos = {
        ...formData,
        descuento_porcentaje: formData.tipo_descuento === 'porcentaje' ? parseFloat(formData.descuento_porcentaje) : null,
        descuento_monto: formData.tipo_descuento === 'monto' ? parseFloat(formData.descuento_monto) : null,
        usos_maximos: parseInt(formData.usos_maximos),
        monto_minimo: parseFloat(formData.monto_minimo) || 0,
        activo: formData.activo,
        fecha_inicio: fechaInicioISO,
        fecha_fin: fechaFinISO,
        usuario_id: usuario?.id  // Agregar usuario_id para autenticación
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
        setMostrarFormulario(false);
        setCuponEditando(null);
        resetForm();
        cargarCupones();
        alert(cuponEditando ? 'Cupón actualizado exitosamente' : 'Cupón creado exitosamente');
      } else {
        throw new Error(data.message || 'Error al guardar cupón');
      }
    } catch (error) {
      console.error('Error guardando cupón:', error);
      setError(error.message || 'Error al guardar el cupón');
    }
  };

  const handleEditar = (cupon) => {
    setCuponEditando(cupon);
    
    // Formatear fechas para datetime-local
    const formatearFechaParaInput = (fecha) => {
      if (!fecha) return '';
      const date = new Date(fecha);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      return `${year}-${month}-${day}T${hours}:${minutes}`;
    };
    
    setFormData({
      codigo: cupon.codigo,
      tipo_descuento: cupon.tipo_descuento,
      descuento_porcentaje: cupon.descuento_porcentaje || '',
      descuento_monto: cupon.descuento_monto || '',
      fecha_inicio: formatearFechaParaInput(cupon.fecha_inicio),
      fecha_fin: formatearFechaParaInput(cupon.fecha_fin),
      usos_maximos: cupon.usos_maximos,
      monto_minimo: cupon.monto_minimo || 0,
      descripcion: cupon.descripcion || '',
      activo: cupon.activo
    });
    setMostrarFormulario(true);
  };

  const handleEliminar = async (cuponId) => {
    if (!window.confirm('¿Estás seguro de que deseas eliminar este cupón?')) {
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/cupones/${cuponId}/?usuario_id=${usuario?.id}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();

      if (response.ok && data.success) {
        cargarCupones();
        alert('Cupón eliminado exitosamente');
      } else {
        throw new Error(data.message || 'Error al eliminar cupón');
      }
    } catch (error) {
      console.error('Error eliminando cupón:', error);
      alert('Error al eliminar el cupón: ' + error.message);
    }
  };

  const resetForm = () => {
    setFormData({
      codigo: '',
      tipo_descuento: 'porcentaje',
      descuento_porcentaje: '',
      descuento_monto: '',
      fecha_inicio: '',
      fecha_fin: '',
      usos_maximos: 1,
      monto_minimo: 0,
      descripcion: '',
      activo: true
    });
    setCuponEditando(null);
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

  if (usuario && usuario.rol !== 'gerente' && usuario.rol !== 'admin_sistema') {
    return (
      <div className="cupones-container">
        <div className="error-state">
          <FaTimesCircle className="error-icon" />
          <h2>Acceso Denegado</h2>
          <p>Solo gerentes y administradores pueden gestionar cupones.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="cupones-container" style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      <div className="cupones-header" style={{ marginBottom: '30px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '20px' }}>
          <FaTicketAlt style={{ fontSize: '2rem', color: 'var(--primary-color)' }} />
          <div>
            <h1 style={{ margin: 0 }}>Gestión de Cupones</h1>
            <p style={{ margin: '5px 0 0 0', color: '#666' }}>Crea y gestiona cupones de descuento para tus clientes</p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            onClick={() => {
              resetForm();
              setMostrarFormulario(!mostrarFormulario);
            }}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <FaPlus /> {mostrarFormulario ? 'Cancelar' : 'Nuevo Cupón'}
          </button>
          <button
            onClick={cargarCupones}
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
      <div className="filtros-container" style={{ 
        padding: '15px', 
        backgroundColor: '#f8f9fa', 
        borderRadius: '8px', 
        marginBottom: '20px' 
      }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Buscar:</label>
            <input
              type="text"
              placeholder="Código o descripción..."
              value={filtros.busqueda}
              onChange={(e) => setFiltros({ ...filtros, busqueda: e.target.value })}
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Estado:</label>
            <select
              value={filtros.activo}
              onChange={(e) => setFiltros({ ...filtros, activo: e.target.value })}
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">Todos</option>
              <option value="true">Activos</option>
              <option value="false">Inactivos</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Tipo:</label>
            <select
              value={filtros.tipo_descuento}
              onChange={(e) => setFiltros({ ...filtros, tipo_descuento: e.target.value })}
              style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
            >
              <option value="">Todos</option>
              <option value="porcentaje">Porcentaje</option>
              <option value="monto">Monto Fijo</option>
            </select>
          </div>
        </div>
      </div>

      {/* Formulario */}
      {mostrarFormulario && (
        <div className="formulario-cupon" style={{
          padding: '20px',
          backgroundColor: '#fff',
          borderRadius: '8px',
          marginBottom: '20px',
          border: '1px solid #ddd'
        }}>
          <h3>{cuponEditando ? 'Editar Cupón' : 'Nuevo Cupón'}</h3>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '15px', marginBottom: '15px' }}>
              <div>
                <label>Código del Cupón *</label>
                <input
                  type="text"
                  required
                  value={formData.codigo}
                  onChange={(e) => setFormData({ ...formData, codigo: e.target.value.toUpperCase() })}
                  placeholder="Ej: DESCUENTO20"
                  disabled={!!cuponEditando}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
              <div>
                <label>Tipo de Descuento *</label>
                <select
                  required
                  value={formData.tipo_descuento}
                  onChange={(e) => setFormData({ ...formData, tipo_descuento: e.target.value })}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value="porcentaje">Porcentaje</option>
                  <option value="monto">Monto Fijo</option>
                </select>
              </div>
              {formData.tipo_descuento === 'porcentaje' ? (
                <div>
                  <label>Descuento Porcentaje (%) *</label>
                  <input
                    type="number"
                    required
                    min="0"
                    max="100"
                    step="0.01"
                    value={formData.descuento_porcentaje}
                    onChange={(e) => setFormData({ ...formData, descuento_porcentaje: e.target.value })}
                    placeholder="Ej: 20"
                    style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                  />
                </div>
              ) : (
                <div>
                  <label>Descuento Monto ($) *</label>
                  <input
                    type="number"
                    required
                    min="0"
                    step="0.01"
                    value={formData.descuento_monto}
                    onChange={(e) => setFormData({ ...formData, descuento_monto: e.target.value })}
                    placeholder="Ej: 5000"
                    style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                  />
                </div>
              )}
              <div>
                <label>Monto Mínimo ($)</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={formData.monto_minimo}
                  onChange={(e) => setFormData({ ...formData, monto_minimo: e.target.value })}
                  placeholder="0"
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
              <div>
                <label>Fecha Inicio *</label>
                <input
                  type="datetime-local"
                  required
                  value={formData.fecha_inicio}
                  onChange={(e) => setFormData({ ...formData, fecha_inicio: e.target.value })}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
              <div>
                <label>Fecha Fin *</label>
                <input
                  type="datetime-local"
                  required
                  value={formData.fecha_fin}
                  onChange={(e) => setFormData({ ...formData, fecha_fin: e.target.value })}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
              <div>
                <label>Usos Máximos *</label>
                <input
                  type="number"
                  required
                  min="1"
                  value={formData.usos_maximos}
                  onChange={(e) => setFormData({ ...formData, usos_maximos: e.target.value })}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
              <div>
                <label>Estado</label>
                <select
                  value={formData.activo}
                  onChange={(e) => setFormData({ ...formData, activo: e.target.value === 'true' })}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value={true}>Activo</option>
                  <option value={false}>Inactivo</option>
                </select>
              </div>
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label>Descripción</label>
              <textarea
                value={formData.descripcion}
                onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
                placeholder="Descripción del cupón..."
                rows="3"
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              />
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button type="submit" className="btn btn-primary">
                {cuponEditando ? 'Actualizar' : 'Crear'} Cupón
              </button>
              <button
                type="button"
                onClick={() => {
                  setMostrarFormulario(false);
                  resetForm();
                }}
                className="btn btn-secondary"
              >
                Cancelar
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tabla de cupones */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <p>Cargando cupones...</p>
        </div>
      ) : cupones.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
          <FaTicketAlt style={{ fontSize: '3rem', color: '#ccc', marginBottom: '15px' }} />
          <p>No hay cupones registrados</p>
          <button onClick={() => setMostrarFormulario(true)} className="btn btn-primary">
            Crear Primer Cupón
          </button>
        </div>
      ) : (
        <div className="tabla-cupones" style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: '#fff', borderRadius: '8px', overflow: 'hidden' }}>
            <thead style={{ backgroundColor: 'var(--primary-color)', color: '#fff' }}>
              <tr>
                <th style={{ padding: '12px', textAlign: 'left' }}>Código</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Tipo</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Descuento</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Vigencia</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Usos</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Estado</th>
                <th style={{ padding: '12px', textAlign: 'center' }}>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {cupones.map((cupon) => (
                <tr key={cupon.id} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '12px', fontWeight: 'bold' }}>{cupon.codigo}</td>
                  <td style={{ padding: '12px' }}>{cupon.tipo_descuento === 'porcentaje' ? 'Porcentaje' : 'Monto Fijo'}</td>
                  <td style={{ padding: '12px' }}>
                    {cupon.tipo_descuento === 'porcentaje' 
                      ? `${cupon.descuento_porcentaje}%`
                      : `$${cupon.descuento_monto}`
                    }
                  </td>
                  <td style={{ padding: '12px', fontSize: '0.9rem' }}>
                    {formatearFecha(cupon.fecha_inicio)} - {formatearFecha(cupon.fecha_fin)}
                  </td>
                  <td style={{ padding: '12px' }}>
                    {cupon.usos_actuales} / {cupon.usos_maximos}
                  </td>
                  <td style={{ padding: '12px' }}>
                    {cupon.es_valido ? (
                      <span style={{ color: '#28a745', fontWeight: 'bold' }}>
                        <FaCheckCircle /> Válido
                      </span>
                    ) : (
                      <span style={{ color: '#dc3545', fontWeight: 'bold' }}>
                        <FaTimesCircle /> Inválido
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'center' }}>
                    <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
                      <button
                        onClick={() => handleEditar(cupon)}
                        className="btn btn-sm btn-primary"
                        style={{ padding: '5px 10px' }}
                      >
                        <FaEdit />
                      </button>
                      <button
                        onClick={() => handleEliminar(cupon.id)}
                        className="btn btn-sm btn-danger"
                        style={{ padding: '5px 10px' }}
                      >
                        <FaTrash />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default GestionCupones;

