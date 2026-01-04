import React, { useState, useEffect } from 'react';
import { FaSearch, FaDownload, FaFilter } from 'react-icons/fa';
import { useRol } from '../contexts/RolContext';
import '../styles/globals.css';

function Auditoria() {
  const { usuario } = useRol();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filtros, setFiltros] = useState({
    usuario_id: '',
    tipo_accion: '',
    modelo: '',
    fecha_inicio: '',
    fecha_fin: '',
    descripcion: ''
  });
  const [mostrarFiltros, setMostrarFiltros] = useState(false);

  useEffect(() => {
    if (usuario) {
      cargarLogsAuditoria();
    }
  }, [filtros, usuario]);

  const cargarLogsAuditoria = async () => {
    try {
      setLoading(true);
      const queryParams = new URLSearchParams();

      // Agregar filtros a los query params
      Object.entries(filtros).forEach(([key, value]) => {
        if (value) queryParams.append(key, value);
      });

      // Agregar user_id para autenticación
      if (usuario && usuario.id) {
        queryParams.append('user_id', usuario.id);
      }

      const url = `/api/auditoria/logs/?${queryParams.toString()}`;
      const response = await fetch(url);
      const data = await response.json();

      if (response.ok && data.success) {
        setLogs(data.logs || []);
      } else {
        console.error('Error en respuesta:', data);
        setLogs([]);
      }
    } catch (error) {
      console.error('Error cargando logs:', error);
      setLogs([]);
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
      usuario_id: '',
      tipo_accion: '',
      modelo: '',
      fecha_inicio: '',
      fecha_fin: '',
      descripcion: ''
    });
  };

  const formatearFecha = (fecha) => {
    return new Date(fecha).toLocaleString('es-CL');
  };

  return (
    <div className="auditoria-container">
      <div className="auditoria-header">
        <div className="header-content">
          <FaSearch className="header-icon" />
          <div>
            <h1>Sistema de Auditoría</h1>
            <p>Registro de actividades del sistema</p>
          </div>
        </div>
      </div>

      <div className="auditoria-main">
        <div className="logs-section">
          <div className="section-header">
            <h3>Registro de Actividades</h3>
            <div className="header-actions">
              <button
                className="btn-filtros"
                onClick={() => setMostrarFiltros(!mostrarFiltros)}
              >
                <FaFilter /> Filtros
              </button>
              <button
                className="btn-exportar"
                onClick={() => {
                  const queryParams = new URLSearchParams();
                  // Agregar filtros actuales a la exportación
                  Object.entries(filtros).forEach(([key, value]) => {
                    if (value) queryParams.append(key, value);
                  });
                  // Agregar user_id para autenticación
                  if (usuario && usuario.id) {
                    queryParams.append('user_id', usuario.id);
                  }
                  window.open(`/api/auditoria/exportar/?${queryParams.toString()}`, '_blank');
                }}
              >
                <FaDownload /> Exportar CSV
              </button>
            </div>
          </div>

          {mostrarFiltros && (
            <div className="filtros-container">
              <div className="filtros-grid">
                <div className="filtro-group">
                  <label>Usuario ID:</label>
                  <input
                    type="text"
                    name="usuario_id"
                    value={filtros.usuario_id}
                    onChange={handleFiltroChange}
                    placeholder="ID del usuario"
                  />
                </div>
                <div className="filtro-group">
                  <label>Tipo de Acción:</label>
                  <select
                    name="tipo_accion"
                    value={filtros.tipo_accion}
                    onChange={handleFiltroChange}
                  >
                    <option value="">Todas</option>
                    <option value="crear">Crear</option>
                    <option value="modificar">Modificar</option>
                    <option value="eliminar">Eliminar</option>
                    <option value="login">Login</option>
                    <option value="logout">Logout</option>
                  </select>
                </div>
                <div className="filtro-group">
                  <label>Modelo:</label>
                  <select
                    name="modelo"
                    value={filtros.modelo}
                    onChange={handleFiltroChange}
                  >
                    <option value="">Todos</option>
                    <option value="Producto">Producto</option>
                    <option value="Pedido">Pedido</option>
                    <option value="Cliente">Cliente</option>
                    <option value="User">Usuario</option>
                    <option value="AuditLog">AuditLog</option>
                  </select>
                </div>
                <div className="filtro-group">
                  <label>Fecha Inicio:</label>
                  <input
                    type="date"
                    name="fecha_inicio"
                    value={filtros.fecha_inicio}
                    onChange={handleFiltroChange}
                  />
                </div>
                <div className="filtro-group">
                  <label>Fecha Fin:</label>
                  <input
                    type="date"
                    name="fecha_fin"
                    value={filtros.fecha_fin}
                    onChange={handleFiltroChange}
                  />
                </div>
                <div className="filtro-group">
                  <label>Descripción:</label>
                  <input
                    type="text"
                    name="descripcion"
                    value={filtros.descripcion}
                    onChange={handleFiltroChange}
                    placeholder="Buscar en descripción"
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

          {loading ? (
            <div className="loading">Cargando logs de auditoría...</div>
          ) : logs.length === 0 ? (
            <div className="empty-state">
              <FaSearch className="empty-icon" />
              <p>No se encontraron registros de auditoría</p>
            </div>
          ) : (
            <div className="logs-table-container">
              <table className="logs-table">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Usuario</th>
                    <th>Acción</th>
                    <th>Modelo</th>
                    <th>ID Objeto</th>
                    <th>Descripción</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id}>
                      <td>{formatearFecha(log.fecha)}</td>
                      <td>{log.usuario ? log.usuario.username : 'Sistema'}</td>
                      <td>{log.tipo_accion}</td>
                      <td>{log.modelo}</td>
                      <td>{log.id_objeto}</td>
                      <td className="descripcion-cell">{log.descripcion}</td>
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
}

export default Auditoria;
