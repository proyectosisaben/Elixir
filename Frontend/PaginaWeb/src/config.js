// Configuración de la aplicación

// Detectar si estamos en producción (Render)
const isProduction = window.location.hostname.includes('onrender.com');

// URL base de la API
export const API_BASE_URL = isProduction 
  ? 'https://elixir-pk6r.onrender.com' 
  : 'http://localhost:8000';

// URL de la API con /api
export const API_URL = `${API_BASE_URL}/api`;

// Hacer disponible globalmente
window.API_BASE_URL = API_BASE_URL;
window.API_URL = API_URL;

export default {
  API_BASE_URL,
  API_URL,
  isProduction
};
