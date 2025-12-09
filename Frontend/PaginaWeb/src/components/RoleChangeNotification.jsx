import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useRol } from '../contexts/RolContext';

export function RoleChangeNotification() {
  const navigate = useNavigate();
  const { usuario, tieneRol, rolActualizado } = useRol();
  const [mostrarNotificacion, setMostrarNotificacion] = useState(false);
  const [usuarioAnterior, setUsuarioAnterior] = useState(null);

  useEffect(() => {
    // Detectar si cambió el rol
    if (usuarioAnterior && usuario && usuarioAnterior.rol !== usuario.rol) {
      console.log('Rol cambió de:', usuarioAnterior.rol, 'a:', usuario.rol);
      setMostrarNotificacion(true);
      
      // Auto-ocultar después de 10 segundos
      const timeout = setTimeout(() => setMostrarNotificacion(false), 10000);
      return () => clearTimeout(timeout);
    }
    
    if (usuario && !usuarioAnterior) {
      setUsuarioAnterior(usuario);
    }
  }, [rolActualizado, usuario, usuarioAnterior]);

  if (!mostrarNotificacion || !usuario) {
    return null;
  }

  const handleNavegar = () => {
    if (tieneRol(['admin_sistema', 'gerente'])) {
      navigate('/dashboard');
    }
    setMostrarNotificacion(false);
  };

  return (
    <div className="alert alert-success alert-dismissible fade show position-fixed" 
         style={{ top: '80px', right: '20px', zIndex: 9998, minWidth: '300px', maxWidth: '400px' }}
         role="alert">
      <strong>🎉 ¡Rol Actualizado!</strong>
      <p className="mb-2">
        Tu rol ha sido cambiado a <strong>{usuario.rol}</strong>
      </p>
      
      {tieneRol(['admin_sistema', 'gerente']) && (
        <button 
          className="btn btn-sm btn-success"
          onClick={handleNavegar}
          style={{ marginRight: '10px' }}
        >
          Ver Dashboard →
        </button>
      )}

      {tieneRol('admin_sistema') && (
        <button 
          className="btn btn-sm btn-warning"
          onClick={() => {
            navigate('/admin/roles');
            setMostrarNotificacion(false);
          }}
          style={{ marginRight: '10px' }}
        >
          Gestionar Roles →
        </button>
      )}
      
      <button 
        type="button" 
        className="btn-close"
        onClick={() => setMostrarNotificacion(false)}
        aria-label="Cerrar"
      ></button>
    </div>
  );
}
