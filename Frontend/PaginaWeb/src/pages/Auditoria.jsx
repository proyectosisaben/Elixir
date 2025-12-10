import React, { useState, useEffect } from 'react';
import { FaSearch, FaDownload } from 'react-icons/fa';
import '../styles/globals.css';

function Auditoria() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    cargarLogsAuditoria();
  }, []);

  const cargarLogsAuditoria = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/auditoria/logs/');
      const data = await response.json();

      if (response.ok && data.success) {
        setLogs(data.logs || []);
      }
    } catch (error) {
      console.error('Error cargando logs:', error);
    } finally {
      setLoading(false);
    }
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
            <button className="btn-exportar" onClick={() => window.open('http://localhost:8000/api/auditoria/exportar/', '_blank')}>
              <FaDownload /> Exportar CSV
            </button>
          </div>

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
