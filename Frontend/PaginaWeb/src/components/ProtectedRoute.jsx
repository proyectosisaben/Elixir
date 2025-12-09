import React from 'react';
import { Navigate } from 'react-router-dom';
import { useRol } from '../contexts/RolContext';

export function ProtectedRoute({ element, requiredRoles }) {
  const { usuario, cargando, tieneRol, rolActualizado } = useRol();

  if (cargando) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Cargando...</span>
        </div>
      </div>
    );
  }

  if (!usuario) {
    return <Navigate to="/login" />;
  }

  if (requiredRoles && !tieneRol(requiredRoles)) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="alert alert-danger text-center" style={{ maxWidth: '500px' }}>
          <h3>❌ Acceso Denegado</h3>
          <p>No tienes permisos para acceder a esta página.</p>
          <p>Rol actual: <strong>{usuario.rol}</strong></p>
          <a href="/" className="btn btn-primary">Volver al inicio</a>
        </div>
      </div>
    );
  }

  return element;
}
