import React, { createContext, useState, useEffect, useCallback, useRef } from 'react';

export const RolContext = createContext();

export function RolProvider({ children }) {
  const [usuario, setUsuario] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [rolActualizado, setRolActualizado] = useState(0); // Contador para forzar re-renders
  const actualizacionTimeoutRef = useRef(null);

  // Función para cargar usuario desde localStorage
  const cargarUsuario = useCallback(() => {
    try {
      const usuarioGuardado = localStorage.getItem('usuario');
      if (usuarioGuardado) {
        const usuarioParsed = JSON.parse(usuarioGuardado);
        setUsuario(usuarioParsed);
        console.log('Usuario cargado:', usuarioParsed.rol);
      } else {
        setUsuario(null);
      }
    } catch (err) {
      console.error('Error al cargar usuario:', err);
      setUsuario(null);
    } finally {
      setCargando(false);
    }
  }, []);

  // Cargar usuario inicial
  useEffect(() => {
    cargarUsuario();

    // Escuchar cambios desde storage (otros tabs)
    const handleStorageChange = () => {
      console.log('Storage cambió, recargar usuario');
      cargarUsuario();
      setRolActualizado(prev => prev + 1);
    };

    const handleUsuarioActualizado = () => {
      console.log('Evento usuario-actualizado recibido');
      // Limpiar timeout anterior si existe
      if (actualizacionTimeoutRef.current) {
        clearTimeout(actualizacionTimeoutRef.current);
      }
      
      // Esperar un poco para que se actualice el localStorage
      actualizacionTimeoutRef.current = setTimeout(() => {
        cargarUsuario();
        setRolActualizado(prev => prev + 1);
      }, 100);
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('usuario-actualizado', handleUsuarioActualizado);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('usuario-actualizado', handleUsuarioActualizado);
      if (actualizacionTimeoutRef.current) {
        clearTimeout(actualizacionTimeoutRef.current);
      }
    };
  }, [cargarUsuario]);

  // Función para actualizar usuario
  const actualizarUsuario = useCallback((nuevoUsuario) => {
    if (nuevoUsuario) {
      console.log('Actualizando usuario a:', nuevoUsuario.rol);
      localStorage.setItem('usuario', JSON.stringify(nuevoUsuario));
      setUsuario(nuevoUsuario);
      setRolActualizado(prev => prev + 1);
      // Emitir evento personalizado
      window.dispatchEvent(new Event('usuario-actualizado'));
    } else {
      localStorage.removeItem('usuario');
      setUsuario(null);
      setRolActualizado(prev => prev + 1);
    }
  }, []);

  // Función para cerrar sesión
  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('usuario');
    setUsuario(null);
    setRolActualizado(prev => prev + 1);
    window.dispatchEvent(new Event('usuario-actualizado'));
  }, []);

  // Función para verificar si el usuario tiene un rol específico
  const tieneRol = useCallback((rol) => {
    if (!usuario) return false;
    if (typeof rol === 'string') {
      return usuario.rol === rol;
    }
    if (Array.isArray(rol)) {
      return rol.includes(usuario.rol);
    }
    return false;
  }, [usuario]);

  // Función para verificar si el usuario está autenticado
  const estaAutenticado = useCallback(() => {
    return usuario !== null;
  }, [usuario]);

  const valor = {
    usuario,
    cargando,
    actualizarUsuario,
    logout,
    tieneRol,
    estaAutenticado,
    rolActualizado // Exponemos para que componentes se actualicen cuando cambia
  };

  return (
    <RolContext.Provider value={valor}>
      {children}
    </RolContext.Provider>
  );
}

export function useRol() {
  const contexto = React.useContext(RolContext);
  if (!contexto) {
    throw new Error('useRol debe ser usado dentro de RolProvider');
  }
  return contexto;
}
