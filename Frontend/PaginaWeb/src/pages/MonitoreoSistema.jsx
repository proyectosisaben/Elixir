import React, { useState, useEffect } from 'react';
import { FaServer, FaExclamationTriangle, FaEye, FaChartLine, FaFilter, FaDownload, FaSearch } from 'react-icons/fa';
import { useRol } from '../contexts/RolContext';
import '../styles/globals.css';

function MonitoreoSistema() {
  const { usuario } = useRol();
  const [estadisticas, setEstadisticas] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [mostrarFiltros, setMostrarFiltros] = useState(false);
  const [filtros, setFiltros] = useState({
    nivel: '',
    categoria: '',
    fecha_inicio: '',
    fecha_fin: '',
    modulo: ''
  });

  useEffect(() => {
    if (usuario && usuario.rol === 'admin_sistema') {
      cargarEstadisticas();
      cargarLogs();
    }
  }, [filtros, usuario]);

  const cargarEstadisticas = async () => {
    try {
      const response = await fetch(`/api/sistema/estadisticas/?user_id=${usuario?.id}`);
      const data = await response.json();

      if (response.ok && data.success) {
        setEstadisticas(data.estadisticas);
        setError(null);
      } else {
        throw new Error(data.message || 'Error en la respuesta');
      }
    } catch (error) {
      console.error('Error cargando estadísticas:', error);
      setError('Error al cargar el monitoreo del sistema');
    }
  };

  const cargarLogs = async () => {
    try {
      setLoading(true);
      const queryParams = new URLSearchParams();

      // Agregar filtros
      Object.entries(filtros).forEach(([key, value]) => {
        if (value) queryParams.append(key, value);
      });

      // Agregar user_id para autenticación
      if (usuario && usuario.id) {
        queryParams.append('user_id', usuario.id);
      }

      const url = `/api/sistema/logs/?${queryParams.toString()}`;
      const response = await fetch(url);
      const data = await response.json();

      if (response.ok && data.success) {
        setLogs(data.logs || []);
        setTotalLogsFiltrados(data.total || 0);
        setTotalPaginasLogs(data.total_paginas || 1);
        setError(null);
      } else {
        throw new Error(data.message || 'Error al cargar logs');
      }
    } catch (error) {
      console.error('Error cargando logs:', error);
      setError('Error al cargar los logs del sistema');
    } finally {
      setLoading(false);
    }
  };

  const handleFiltroChange = (e) => {
    const { name, value } = e.target;
    setFiltros(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const limpiarFiltros = () => {
    setFiltros({
      nivel: '',
      categoria: '',
      fecha_inicio: '',
      fecha_fin: '',
      modulo: ''
    });
  };

  const formatearFecha = (fechaString) => {
    if (!fechaString) return 'N/A';
    try {
      const date = new Date(fechaString);
      return date.toLocaleString('es-CL');
    } catch {
      return fechaString;
    }
  };

  const getNivelColor = (nivel) => {
    switch (nivel) {
      case 'info': return '#48bb78';
      case 'warning': return '#ed8936';
      case 'error': return '#e53e3e';
      case 'critical': return '#9f1a1a';
      default: return '#718096';
    }
  };

  const exportarLogs = () => {
    const queryParams = new URLSearchParams();
    Object.entries(filtros).forEach(([key, value]) => {
      if (value) queryParams.append(key, value);
    });
    if (usuario && usuario.id) {
      queryParams.append('user_id', usuario.id);
    }
    window.open(`/api/sistema/logs/?${queryParams.toString()}&export=1`, '_blank');
  };

  if (usuario && usuario.rol !== 'admin_sistema') {
    return (
      <div className="monitoreo-container">
        <div className="error-state">
          <FaExclamationTriangle className="error-icon" />
          <h2>Acceso Denegado</h2>
          <p>Solo los administradores del sistema pueden acceder al monitoreo del sistema.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="monitoreo-container">
      <div className="monitoreo-header">
        <div className="header-content">
          <FaServer className="header-icon" />
          <div>
            <h1>Monitoreo del Sistema</h1>
            <p>Logs, estadísticas y métricas de rendimiento en tiempo real</p>
          </div>
        </div>
        <div className="header-actions">
          <button
            className="btn-filtros"
            onClick={() => setMostrarFiltros(!mostrarFiltros)}
          >
            <FaFilter /> Filtros
          </button>
          <button className="btn-exportar" onClick={exportarLogs}>
            <FaDownload /> Exportar Logs
          </button>
        </div>
      </div>

      {mostrarFiltros && (
        <div className="filtros-container">
          <div className="filtros-grid">
            <div className="filtro-group">
              <label>Nivel:</label>
              <select name="nivel" value={filtros.nivel} onChange={handleFiltroChange}>
                <option value="">Todos</option>
                <option value="info">Información</option>
                <option value="warning">Advertencia</option>
                <option value="error">Error</option>
                <option value="critical">Crítico</option>
              </select>
            </div>

            <div className="filtro-group">
              <label>Categoría:</label>
              <select name="categoria" value={filtros.categoria} onChange={handleFiltroChange}>
                <option value="">Todas</option>
                <option value="sistema">Sistema</option>
                <option value="seguridad">Seguridad</option>
                <option value="usuario">Usuario</option>
                <option value="venta">Venta</option>
                <option value="inventario">Inventario</option>
                <option value="api">API</option>
                <option value="base_datos">Base de Datos</option>
              </select>
            </div>

            <div className="filtro-group">
              <label>Módulo:</label>
              <input
                type="text"
                name="modulo"
                value={filtros.modulo}
                onChange={handleFiltroChange}
                placeholder="Ej: views.login"
              />
            </div>

            <div className="filtro-group">
              <label>Fecha Inicio:</label>
              <input
                type="datetime-local"
                name="fecha_inicio"
                value={filtros.fecha_inicio}
                onChange={handleFiltroChange}
              />
            </div>

            <div className="filtro-group">
              <label>Fecha Fin:</label>
              <input
                type="datetime-local"
                name="fecha_fin"
                value={filtros.fecha_fin}
                onChange={handleFiltroChange}
              />
            </div>
          </div>

          <div className="filtros-actions">
            <button className="btn-limpiar" onClick={limpiarFiltros}>
              Limpiar Filtros
            </button>
          </div>
        </div>
      )}

      <div className="monitoreo-main">
        {loading ? (
          <div className="loading">Cargando monitoreo del sistema...</div>
        ) : estadisticas ? (
          <>
            {/* Métricas principales */}
            <div className="metricas-grid">
              <div className="metrica-card">
                <div className="metrica-header">
                  <FaServer className="metrica-icon" />
                  <h3>Logs Totales</h3>
                </div>
                <p className="metrica-valor">{estadisticas.logs_sistema?.total || 0}</p>
                <span className="metrica-label">Eventos registrados</span>
              </div>

              <div className="metrica-card">
                <div className="metrica-header">
                  <FaExclamationTriangle className="metrica-icon" />
                  <h3>Logs 24h</h3>
                </div>
                <p className="metrica-valor">{estadisticas.logs_sistema?.ultimas_24h || 0}</p>
                <span className="metrica-label">Últimas 24 horas</span>
              </div>

              <div className="metrica-card">
                <div className="metrica-header">
                  <FaEye className="metrica-icon" />
                  <h3>Visitas Productos</h3>
                </div>
                <p className="metrica-valor">{estadisticas.visitas_productos?.total || 0}</p>
                <span className="metrica-label">Total de visitas</span>
              </div>

              <div className="metrica-card">
                <div className="metrica-header">
                  <FaChartLine className="metrica-icon" />
                  <h3>Usuarios Activos</h3>
                </div>
                <p className="metrica-valor">{estadisticas.actividad?.usuarios_activos_24h || 0}</p>
                <span className="metrica-label">Últimas 24 horas</span>
              </div>
            </div>

            {/* Logs por nivel */}
            {estadisticas.logs_sistema?.por_nivel && estadisticas.logs_sistema.por_nivel.length > 0 && (
              <div className="chart-section">
                <h3>Distribución de Logs por Nivel</h3>
                <div className="logs-por-nivel">
                  {estadisticas.logs_sistema.por_nivel.map((item, index) => (
                    <div key={index} className="nivel-item">
                      <span className="nivel-label" style={{ color: getNivelColor(item.nivel) }}>
                        {item.nivel}
                      </span>
                      <span className="nivel-count">{item.cantidad}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Productos más visitados */}
            {estadisticas.visitas_productos?.productos_mas_visitados && estadisticas.visitas_productos.productos_mas_visitados.length > 0 && (
              <div className="productos-visitados-section">
                <h3>Productos Más Visitados</h3>
                <div className="productos-table-container">
                  <table className="productos-table">
                    <thead>
                      <tr>
                        <th>Producto</th>
                        <th>Visitas</th>
                        <th>Tiempo Promedio</th>
                      </tr>
                    </thead>
                    <tbody>
                      {estadisticas.visitas_productos.productos_mas_visitados.map((producto, index) => (
                        <tr key={index}>
                          <td>{producto.producto__nombre}</td>
                          <td>{producto.visitas}</td>
                          <td>{Math.round(producto.tiempo_promedio || 0)}s</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Tabla de logs */}
            <div className="logs-section">
              <h3>Registro de Eventos del Sistema</h3>
              {logs.length === 0 ? (
                <div className="empty-state">
                  <FaSearch className="empty-icon" />
                  <p>No se encontraron logs con los filtros aplicados</p>
                </div>
              ) : (
                <div className="logs-table-container">
                  <table className="logs-table">
                    <thead>
                      <tr>
                        <th>Fecha</th>
                        <th>Nivel</th>
                        <th>Categoría</th>
                        <th>Usuario</th>
                        <th>Módulo</th>
                        <th>Mensaje</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logs.map((log) => (
                        <tr key={log.id}>
                          <td>{formatearFecha(log.fecha_creacion)}</td>
                          <td>
                            <span
                              className="nivel-badge"
                              style={{ backgroundColor: getNivelColor(log.nivel) }}
                            >
                              {log.nivel_display}
                            </span>
                          </td>
                          <td>{log.categoria_display}</td>
                          <td>{log.usuario || 'Sistema'}</td>
                          <td>{log.modulo || '-'}</td>
                          <td className="mensaje-cell" title={log.mensaje}>
                            {log.mensaje.length > 100 ? log.mensaje.substring(0, 100) + '...' : log.mensaje}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="error-state">
            <p>Error al cargar el monitoreo del sistema</p>
            <button onClick={() => { cargarEstadisticas(); cargarLogs(); }} className="btn-retry">
              Reintentar
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default MonitoreoSistema;
