import React, { useState, useEffect } from 'react';
import { useRol } from '../contexts/RolContext';
import { FaBell, FaExclamationTriangle, FaEye } from 'react-icons/fa';
import '../styles/globals.css';

function NotificacionesAutorizaciones() {
  const { usuario, tieneRol } = useRol();
  const [notificaciones, setNotificaciones] = useState(null);
  const [mostrarDropdown, setMostrarDropdown] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (usuario && (tieneRol('gerente') || tieneRol('admin_sistema'))) {
      cargarNotificaciones();
      // Actualizar cada 30 segundos
      const intervalo = setInterval(cargarNotificaciones, 30000);
      return () => clearInterval(intervalo);
    }
  }, [usuario]);

  const cargarNotificaciones = async () => {
    if (!usuario) return;

    try {
      setLoading(true);
      const response = await fetch("${window.API_BASE_URL}/api/autorizaciones/notificaciones/?user_id=${usuario.id}`);
      const data = await response.json();

      if (response.ok && data.success) {
        setNotificaciones(data.notificaciones);
      }
    } catch (error) {
      console.error('Error cargando notificaciones:', error);
    } finally {
      setLoading(false);
    }
  };

  const marcarComoVista = (notificacionId) => {
    // Aquí podríamos implementar marcar como vista individualmente
    // Por ahora solo cerramos el dropdown
    setMostrarDropdown(false);
  };

  if (!usuario || (!tieneRol('gerente') && !tieneRol('admin_sistema'))) {
    return null;
  }

  const totalPendientes = notificaciones?.total_pendientes || 0;
  const ultimasNotificaciones = notificaciones?.ultimas || [];

  return (
    <div className="notificaciones-container">
      <button
        className="btn-notificaciones"
        onClick={() => setMostrarDropdown(!mostrarDropdown)}
        title="Notificaciones de autorizaciones"
      >
        <FaBell />
        {totalPendientes > 0 && (
          <span className="badge-notificaciones">{totalPendientes}</span>
        )}
      </button>

      {mostrarDropdown && (
        <div className="notificaciones-dropdown">
          <div className="notificaciones-header">
            <h4>Notificaciones</h4>
            <button
              className="btn-cerrar-dropdown"
              onClick={() => setMostrarDropdown(false)}
            >
              ×
            </button>
          </div>

          <div className="notificaciones-content">
            {loading ? (
              <div className="notificaciones-loading">
                Cargando notificaciones...
              </div>
            ) : totalPendientes === 0 ? (
              <div className="notificaciones-vacias">
                <FaBell className="icono-vacio" />
                <p>No hay solicitudes pendientes</p>
              </div>
            ) : (
              <>
                <div className="notificaciones-resumen">
                  <span className="total-pendientes">
                    {totalPendientes} solicitud{totalPendientes !== 1 ? 'es' : ''} pendiente{totalPendientes !== 1 ? 's' : ''}
                  </span>
                </div>

                <div className="notificaciones-list">
                  {ultimasNotificaciones.map(notificacion => (
                    <div
                      key={notificacion.id}
                      className={`notificacion-item prioridad-${notificacion.prioridad}`}
                      onClick={() => marcarComoVista(notificacion.id)}
                    >
                      <div className="notificacion-icono">
                        <FaExclamationTriangle />
                      </div>
                      <div className="notificacion-content">
                        <div className="notificacion-titulo">
                          {notificacion.titulo}
                        </div>
                        <div className="notificacion-mensaje">
                          {notificacion.mensaje}
                        </div>
                        <div className="notificacion-fecha">
                          {new Date(notificacion.fecha).toLocaleString('es-CL')}
                        </div>
                      </div>
                      <div className="notificacion-actions">
                        <a
                          href={notificacion.url}
                          className="btn-ver-notificacion"
                          onClick={(e) => {
                            e.stopPropagation();
                            setMostrarDropdown(false);
                          }}
                        >
                          <FaEye />
                        </a>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="notificaciones-footer">
                  <a
                    href="/autorizaciones/gerente"
                    className="btn-ver-todas"
                    onClick={() => setMostrarDropdown(false)}
                  >
                    Ver todas las solicitudes
                  </a>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default NotificacionesAutorizaciones;
