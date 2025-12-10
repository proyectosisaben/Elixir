import React, { useState, useEffect } from 'react';
import { FaLock, FaCheck, FaTimes } from 'react-icons/fa';
import { useRol } from '../contexts/RolContext';
import '../styles/globals.css';

function Autorizaciones() {
  const { usuario } = useRol();
  const [solicitudes, setSolicitudes] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    cargarSolicitudes();
  }, []);

  const cargarSolicitudes = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/autorizaciones/solicitudes/');
      const data = await response.json();

      if (response.ok && data.success) {
        setSolicitudes(data.solicitudes || []);
      }
    } catch (error) {
      console.error('Error cargando solicitudes:', error);
    } finally {
      setLoading(false);
    }
  };

  const gestionarSolicitud = async (solicitudId, accion) => {
    try {
      const response = await fetch(`http://localhost:8000/api/autorizaciones/${solicitudId}/gestionar/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          accion: accion,
          comentario: '',
          usuario_id: usuario?.id
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        alert(`Solicitud ${accion === 'aprobar' ? 'aprobada' : 'rechazada'} exitosamente`);
        cargarSolicitudes();
      } else {
        alert('Error: ' + (data.message || 'No se pudo procesar la solicitud'));
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error al procesar la solicitud');
    }
  };

  const formatearFecha = (fecha) => {
    return new Date(fecha).toLocaleString('es-CL');
  };

  const getEstadoColor = (estado) => {
    const colores = {
      'pendiente': 'warning',
      'aprobada': 'success',
      'rechazada': 'danger',
      'cancelada': 'secondary'
    };
    return colores[estado] || 'secondary';
  };

  const puedeGestionar = () => {
    return usuario?.rol === 'gerente' || usuario?.rol === 'admin_sistema';
  };

  return (
    <div className="autorizaciones-container">
      <div className="autorizaciones-header">
        <div className="header-content">
          <FaLock className="header-icon" />
          <div>
            <h1>Sistema de Autorizaciones</h1>
            <p>Gestión de solicitudes de cambios en inventario</p>
          </div>
        </div>
      </div>

      <div className="autorizaciones-main">
        <div className="solicitudes-section">
          <div className="section-header">
            <h3>Solicitudes de Autorización</h3>
          </div>

          {loading ? (
            <div className="loading">Cargando solicitudes...</div>
          ) : solicitudes.length === 0 ? (
            <div className="empty-state">
              <FaLock className="empty-icon" />
              <p>No hay solicitudes de autorización</p>
            </div>
          ) : (
            <div className="solicitudes-table-container">
              <table className="solicitudes-table">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Solicitante</th>
                    <th>Tipo</th>
                    <th>Modelo</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {solicitudes.map((solicitud) => (
                    <tr key={solicitud.id}>
                      <td>{formatearFecha(solicitud.fecha_solicitud)}</td>
                      <td>{solicitud.solicitante.username}</td>
                      <td>{solicitud.tipo_solicitud}</td>
                      <td>{solicitud.modelo_afectado}</td>
                      <td>
                        <span className={`badge badge-${getEstadoColor(solicitud.estado)}`}>
                          {solicitud.estado}
                        </span>
                      </td>
                      <td>
                        {puedeGestionar() && solicitud.estado === 'pendiente' && (
                          <>
                            <button
                              className="btn-aprobar"
                              onClick={() => gestionarSolicitud(solicitud.id, 'aprobar')}
                              title="Aprobar solicitud"
                            >
                              <FaCheck />
                            </button>
                            <button
                              className="btn-rechazar"
                              onClick={() => gestionarSolicitud(solicitud.id, 'rechazar')}
                              title="Rechazar solicitud"
                            >
                              <FaTimes />
                            </button>
                          </>
                        )}
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
}

export default Autorizaciones;
