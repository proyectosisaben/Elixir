// hooks/useApi.js
// Hook personalizado para consumir la API de Elixir

import { useState, useEffect } from 'react';

const API_URL = 'http://localhost:8000/api';

export const useApi = (endpoint) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${API_URL}${endpoint}`);
        if (!response.ok) {
          throw new Error(`Error ${response.status}`);
        }
        const json = await response.json();
        setData(json);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [endpoint]);

  return { data, loading, error };
};

// ============================================
// FUNCIONES DE API PARA CONSUMO DIRECTO
// ============================================

/**
 * Obtener datos para la página de inicio
 */
export const fetchHome = async () => {
  try {
    const response = await fetch(`${API_URL}/home/`);
    if (!response.ok) throw new Error('Error al obtener home');
    return await response.json();
  } catch (error) {
    console.error('Error en fetchHome:', error);
    throw error;
  }
};

/**
 * Obtener productos con filtros
 * @param {Object} filters - { q: 'búsqueda', categoria: 1 }
 */
export const fetchCatalogo = async (filters = {}) => {
  try {
    const params = new URLSearchParams();
    if (filters.q) params.append('q', filters.q);
    if (filters.categoria) params.append('categoria', filters.categoria);
    
    const url = `${API_URL}/catalogo/?${params.toString()}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Error al obtener catálogo');
    return await response.json();
  } catch (error) {
    console.error('Error en fetchCatalogo:', error);
    throw error;
  }
};

/**
 * Obtener detalle de un producto
 * @param {Number} productoId - ID del producto
 */
export const fetchProducto = async (productoId) => {
  try {
    const response = await fetch(`${API_URL}/producto/${productoId}/`);
    if (!response.ok) throw new Error('Producto no encontrado');
    return await response.json();
  } catch (error) {
    console.error('Error en fetchProducto:', error);
    throw error;
  }
};

/**
 * Obtener todos los productos
 */
export const fetchProductos = async () => {
  try {
    const response = await fetch(`${API_URL}/productos`);
    if (!response.ok) throw new Error('Error al obtener productos');
    return await response.json();
  } catch (error) {
    console.error('Error en fetchProductos:', error);
    throw error;
  }
};

/**
 * Registrar un nuevo cliente
 * @param {Object} datos - { email, password, password_confirm, fecha_nacimiento }
 */
export const registroCliente = async (datos) => {
  try {
    const response = await fetch(`${API_URL}/registro/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(datos),
    });

    const json = await response.json();
    
    if (!response.ok) {
      throw new Error(json.message || json.errors || 'Error en el registro');
    }
    
    return json;
  } catch (error) {
    console.error('Error en registroCliente:', error);
    throw error;
  }
};

/**
 * Iniciar sesión
 * @param {Object} datos - { email, password }
 */
export const loginCliente = async (datos) => {
  try {
    const response = await fetch(`${API_URL}/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(datos),
    });

    const json = await response.json();
    
    if (!response.ok) {
      throw new Error(json.message || 'Error en el inicio de sesión');
    }
    
    return json;
  } catch (error) {
    console.error('Error en loginCliente:', error);
    
    if (error instanceof TypeError && error.message === 'Failed to fetch') {
      throw new Error(`No se puede conectar al servidor en ${API_URL}. Verifica que el backend esté corriendo.`);
    }
    
    throw error;
  }
};

/**
 * Procesar checkout
 */
export const processCheckout = async (carrito) => {
  try {
    const response = await fetch(`${API_URL}/checkout/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(carrito),
    });
    
    if (!response.ok) throw new Error('Error en checkout');
    return await response.json();
  } catch (error) {
    console.error('Error en processCheckout:', error);
    throw error;
  }
};
