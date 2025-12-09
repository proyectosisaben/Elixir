import React, { useEffect, useState } from 'react';

export function useBackendConnectivity() {
  const [isConnected, setIsConnected] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const checkConnectivity = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/home/', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
          setIsConnected(true);
          setError(null);
        } else {
          setIsConnected(false);
          setError(`Error del servidor: ${response.status}`);
        }
      } catch (err) {
        setIsConnected(false);
        setError('No se puede conectar al backend. Asegúrate de que esté corriendo en http://localhost:8000');
      }
    };

    checkConnectivity();
    
    // Verificar conectividad cada 30 segundos
    const interval = setInterval(checkConnectivity, 30000);
    
    return () => clearInterval(interval);
  }, []);

  return { isConnected, error };
}

export function ConnectivityWarning() {
  const { isConnected, error } = useBackendConnectivity();

  if (isConnected) {
    return null;
  }

  return (
    <div className="alert alert-danger position-fixed bottom-0 start-50 translate-middle-x" style={{ zIndex: 9999, width: '90%', maxWidth: '500px', marginBottom: '20px' }}>
      <strong>⚠️ Error de Conexión</strong>
      <p className="mb-0 mt-2">{error}</p>
      <small className="text-muted">Por favor, verifica que el servidor Django esté ejecutándose.</small>
    </div>
  );
}
