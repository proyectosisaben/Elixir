import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useRol } from '../contexts/RolContext';

/**
 * Hook que navega automáticamente cuando el rol cambia
 * Si el usuario obtiene permisos para acceder a una nueva página, lo redirige allá
 */
export function useRoleBasedNavigation() {
  const navigate = useNavigate();
  const location = useLocation();
  const { usuario, tieneRol, rolActualizado } = useRol();

  useEffect(() => {
    // Si el usuario es administrador y accedió a alguna página, mostrar notificación
    if (usuario && tieneRol('admin_sistema')) {
      // Notificar que tiene nuevos permisos
      console.log('Usuario ahora tiene permisos de admin');
    }
  }, [usuario, tieneRol, rolActualizado]);
}

/**
 * Hook que verifica si el usuario puede acceder a una página
 * Si no puede, redirige automáticamente
 */
export function useAccessControl(requiredRoles) {
  const navigate = useNavigate();
  const { usuario, tieneRol, rolActualizado } = useRol();

  useEffect(() => {
    if (!usuario) {
      navigate('/login');
      return;
    }

    if (requiredRoles && !tieneRol(requiredRoles)) {
      navigate('/');
      return;
    }
  }, [usuario, tieneRol, rolActualizado, requiredRoles, navigate]);
}
