import React, { useState, useEffect } from 'react';
import './ReportesFinancieros.css';

const ReportesFinancieros = () => {
  const [reportes, setReportes] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [generando, setGenerando] = useState(false);
  const [filtros, setFiltros] = useState({
    tipo_reporte: 'resumen_completo',
    fecha_inicio: '',
    fecha_fin: '',
    categoria_id: null,
    emails_destino: '',
    enviar_email: false
  });
  const [categorias, setCategorias] = useState([]);
  const [mensaje, setMensaje] = useState(null);

  // Cargar reportes al montar
  useEffect(() => {
    cargarReportes();
    cargarCategorias();
  }, []);

  // Cargar lista de reportes
  const cargarReportes = async () => {
    setCargando(true);
    try {
      const response = await fetch(`${window.API_BASE_URL}/api/reportes/listar/', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();
      if (data.success) {
        setReportes(data.reportes);
      }
    } catch (error) {
      console.error('Error al cargar reportes:', error);
      setMensaje({ tipo: 'error', texto: 'Error al cargar reportes' });
    } finally {
      setCargando(false);
    }
  };

  // Cargar categorías
  const cargarCategorias = async () => {
    try {
      const response = await fetch(`${window.API_BASE_URL}/api/catalogo/?limit=1000', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();
      if (data.success && data.data) {
        // Extraer categorías únicas
        const cats = [...new Set(data.data.map(p => p.categoria).filter(Boolean))];
        setCategorias(cats);
      }
    } catch (error) {
      console.error('Error al cargar categorías:', error);
    }
  };

  // Manejar cambios en filtros
  const handleFiltroChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFiltros({
      ...filtros,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  // Generar reporte
  const generarReporte = async (e) => {
    e.preventDefault();
    
    // Validar fechas
    if (!filtros.fecha_inicio || !filtros.fecha_fin) {
      setMensaje({ tipo: 'error', texto: 'Las fechas de inicio y fin son requeridas' });
      return;
    }

    setGenerando(true);
    setMensaje(null);

    try {
      const payload = {
        tipo_reporte: filtros.tipo_reporte,
        fecha_inicio: filtros.fecha_inicio,
        fecha_fin: filtros.fecha_fin,
        categoria_id: filtros.categoria_id ? parseInt(filtros.categoria_id) : null,
        emails_destino: filtros.emails_destino ? filtros.emails_destino.split(',').map(e => e.trim()) : [],
        enviar_email: filtros.enviar_email
      };

      const response = await fetch(`${window.API_BASE_URL}/api/reportes/generar/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      
      if (data.success) {
        setMensaje({ tipo: 'exito', texto: 'Reporte generado correctamente' });
        // Limpiar formulario
        setFiltros({
          tipo_reporte: 'resumen_completo',
          fecha_inicio: '',
          fecha_fin: '',
          categoria_id: null,
          emails_destino: '',
          enviar_email: false
        });
        // Recargar reportes
        setTimeout(cargarReportes, 1000);
      } else {
        setMensaje({ tipo: 'error', texto: data.message || 'Error al generar reporte' });
      }
    } catch (error) {
      console.error('Error al generar reporte:', error);
      setMensaje({ tipo: 'error', texto: 'Error al generar reporte' });
    } finally {
      setGenerando(false);
    }
  };

  // Descargar reporte
  const descargarReporte = (reporte) => {
    if (reporte.archivo_url) {
      window.open(reporte.archivo_url, '_blank');
    }
  };

  // Eliminar reporte
  const eliminarReporte = async (reporteId) => {
    if (!window.confirm('¿Está seguro de que desea eliminar este reporte?')) {
      return;
    }

    try {
      const response = await fetch(`${window.API_BASE_URL}/api/reportes/${reporteId}/eliminar/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();
      
      if (data.success) {
        setMensaje({ tipo: 'exito', texto: 'Reporte eliminado correctamente' });
        cargarReportes();
      } else {
        setMensaje({ tipo: 'error', texto: data.message || 'Error al eliminar reporte' });
      }
    } catch (error) {
      console.error('Error al eliminar reporte:', error);
      setMensaje({ tipo: 'error', texto: 'Error al eliminar reporte' });
    }
  };

  const getTipoReporteLabel = (tipo) => {
    const tipos = {
      'ventas_general': 'Ventas Generales',
      'productos_top': 'Productos Más Vendidos',
      'ingresos_categoria': 'Ingresos por Categoría',
      'comparativa_periodos': 'Comparativa entre Períodos',
      'resumen_completo': 'Resumen Completo'
    };
    return tipos[tipo] || tipo;
  };

  const getEstadoLabel = (estado) => {
    const estados = {
      'pendiente': 'Pendiente',
      'procesando': 'Procesando',
      'generado': 'Generado',
      'enviado_email': 'Enviado por Email',
      'error': 'Error'
    };
    return estados[estado] || estado;
  };

  return (
    <div className="reportes-financieros-container">
      <h2>📊 Reportes Financieros</h2>

      {/* Mensaje de estado */}
      {mensaje && (
        <div className={`alert alert-${mensaje.tipo === 'exito' ? 'success' : 'danger'}`} role="alert">
          {mensaje.texto}
          <button type="button" className="btn-close" onClick={() => setMensaje(null)}></button>
        </div>
      )}

      {/* Formulario de generación */}
      <div className="card mb-4 shadow-sm">
        <div className="card-header bg-primary text-white">
          <h5 className="mb-0">Generar Nuevo Reporte</h5>
        </div>
        <div className="card-body">
          <form onSubmit={generarReporte}>
            <div className="row">
              <div className="col-md-6">
                <div className="mb-3">
                  <label htmlFor="tipo_reporte" className="form-label">Tipo de Reporte</label>
                  <select
                    className="form-select"
                    id="tipo_reporte"
                    name="tipo_reporte"
                    value={filtros.tipo_reporte}
                    onChange={handleFiltroChange}
                  >
                    <option value="resumen_completo">Resumen Completo</option>
                    <option value="ventas_general">Ventas Generales</option>
                    <option value="productos_top">Productos Más Vendidos</option>
                    <option value="ingresos_categoria">Ingresos por Categoría</option>
                    <option value="comparativa_periodos">Comparativa entre Períodos</option>
                  </select>
                </div>
              </div>

              <div className="col-md-6">
                <div className="mb-3">
                  <label htmlFor="categoria_id" className="form-label">Categoría (Opcional)</label>
                  <select
                    className="form-select"
                    id="categoria_id"
                    name="categoria_id"
                    value={filtros.categoria_id || ''}
                    onChange={handleFiltroChange}
                  >
                    <option value="">Todas las categorías</option>
                    {categorias.map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <div className="row">
              <div className="col-md-6">
                <div className="mb-3">
                  <label htmlFor="fecha_inicio" className="form-label">Fecha de Inicio</label>
                  <input
                    type="date"
                    className="form-control"
                    id="fecha_inicio"
                    name="fecha_inicio"
                    value={filtros.fecha_inicio}
                    onChange={handleFiltroChange}
                    required
                  />
                </div>
              </div>

              <div className="col-md-6">
                <div className="mb-3">
                  <label htmlFor="fecha_fin" className="form-label">Fecha de Fin</label>
                  <input
                    type="date"
                    className="form-control"
                    id="fecha_fin"
                    name="fecha_fin"
                    value={filtros.fecha_fin}
                    onChange={handleFiltroChange}
                    required
                  />
                </div>
              </div>
            </div>

            <div className="row">
              <div className="col-md-8">
                <div className="mb-3">
                  <label htmlFor="emails_destino" className="form-label">
                    Emails para Envío (separados por comas, opcional)
                  </label>
                  <input
                    type="text"
                    className="form-control"
                    id="emails_destino"
                    name="emails_destino"
                    placeholder="email1@example.com, email2@example.com"
                    value={filtros.emails_destino}
                    onChange={handleFiltroChange}
                  />
                </div>
              </div>

              <div className="col-md-4">
                <div className="mb-3">
                  <label className="form-label">&nbsp;</label>
                  <div className="form-check">
                    <input
                      className="form-check-input"
                      type="checkbox"
                      id="enviar_email"
                      name="enviar_email"
                      checked={filtros.enviar_email}
                      onChange={handleFiltroChange}
                    />
                    <label className="form-check-label" htmlFor="enviar_email">
                      Enviar por Email
                    </label>
                  </div>
                </div>
              </div>
            </div>

            <button
              type="submit"
              className="btn btn-success"
              disabled={generando}
            >
              {generando ? '⏳ Generando...' : '✅ Generar Reporte'}
            </button>
          </form>
        </div>
      </div>

      {/* Lista de reportes */}
      <div className="card shadow-sm">
        <div className="card-header bg-info text-white">
          <h5 className="mb-0">Reportes Generados</h5>
        </div>
        <div className="card-body">
          {cargando ? (
            <div className="text-center">
              <div className="spinner-border" role="status">
                <span className="visually-hidden">Cargando...</span>
              </div>
            </div>
          ) : reportes.length === 0 ? (
            <p className="text-muted">No hay reportes generados aún</p>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover">
                <thead className="table-light">
                  <tr>
                    <th>Tipo</th>
                    <th>Período</th>
                    <th>Generado por</th>
                    <th>Fecha Generación</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {reportes.map(reporte => (
                    <tr key={reporte.id}>
                      <td>
                        <span className="badge bg-primary">
                          {getTipoReporteLabel(reporte.tipo_reporte)}
                        </span>
                      </td>
                      <td>
                        {reporte.fecha_inicio} a {reporte.fecha_fin}
                      </td>
                      <td>{reporte.generado_por}</td>
                      <td>{new Date(reporte.fecha_creacion).toLocaleDateString('es-ES')}</td>
                      <td>
                        <span className={`badge bg-${
                          reporte.estado === 'generado' ? 'success' :
                          reporte.estado === 'enviado_email' ? 'info' :
                          reporte.estado === 'error' ? 'danger' : 'warning'
                        }`}>
                          {getEstadoLabel(reporte.estado)}
                        </span>
                      </td>
                      <td>
                        <button
                          className="btn btn-sm btn-primary me-2"
                          onClick={() => descargarReporte(reporte)}
                          disabled={!reporte.archivo_url}
                          title="Descargar PDF"
                        >
                          📥 Descargar
                        </button>
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={() => eliminarReporte(reporte.id)}
                          title="Eliminar reporte"
                        >
                          🗑️ Eliminar
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReportesFinancieros;
