/**
 * Utilidades para manejo de filtros avanzados de productos
 */

/**
 * Construir parámetros de query para la API
 * @param {Object} filtros - Objeto con los filtros aplicados
 * @returns {string} - String de parámetros para la URL
 */
export const construirParametrosQueryFiltros = (filtros) => {
  const params = new URLSearchParams();

  if (filtros.busqueda) {
    params.append('q', filtros.busqueda);
  }

  if (filtros.categorias && filtros.categorias.length > 0) {
    filtros.categorias.forEach(cat => params.append('categorias', cat));
  }

  if (filtros.proveedor) {
    params.append('proveedor', filtros.proveedor);
  }

  if (filtros.precioMin !== null && filtros.precioMin !== undefined) {
    params.append('precio_min', filtros.precioMin);
  }

  if (filtros.precioMax !== null && filtros.precioMax !== undefined) {
    params.append('precio_max', filtros.precioMax);
  }

  if (filtros.disponible !== null && filtros.disponible !== undefined) {
    params.append('disponible', filtros.disponible);
  }

  return params.toString();
};

/**
 * Obtener descripción legible del filtro
 * @param {Object} filtro - Objeto con datos del filtro
 * @returns {string} - Descripción legible
 */
export const obtenerDescripcionFiltro = (filtro) => {
  const { tipo, valor, label } = filtro;

  switch (tipo) {
    case 'precio':
      return `Precio: ${valor.min} - ${valor.max}`;
    case 'categoria':
      return `Categoría: ${label || valor}`;
    case 'proveedor':
      return `Proveedor: ${label || valor}`;
    case 'disponibilidad':
      return valor ? 'En stock' : 'Agotado';
    case 'busqueda':
      return `Búsqueda: ${valor}`;
    default:
      return label || valor;
  }
};

/**
 * Formatear precio en formato chileno
 * @param {number} precio - Precio a formatear
 * @returns {string} - Precio formateado
 */
export const formatearPrecio = (precio) => {
  return new Intl.NumberFormat('es-CL', {
    style: 'currency',
    currency: 'CLP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(precio);
};

/**
 * Validar rango de precios
 * @param {number} precioMin - Precio mínimo
 * @param {number} precioMax - Precio máximo
 * @param {number} minDisponible - Mínimo disponible en el catálogo
 * @param {number} maxDisponible - Máximo disponible en el catálogo
 * @returns {Object} - Precios validados
 */
export const validarRangoPrecios = (
  precioMin,
  precioMax,
  minDisponible,
  maxDisponible
) => {
  let min = precioMin;
  let max = precioMax;

  if (min < minDisponible) min = minDisponible;
  if (max > maxDisponible) max = maxDisponible;
  if (min > max) {
    const temp = min;
    min = max;
    max = temp;
  }

  return { min, max };
};

/**
 * Generar estadísticas de filtros aplicados
 * @param {Object} filtros - Filtros aplicados
 * @returns {Object} - Estadísticas
 */
export const generarEstadisticasFiltros = (filtros) => {
  const aplicados = [];

  if (filtros.busqueda) aplicados.push('busqueda');
  if (filtros.categorias?.length > 0) aplicados.push('categorias');
  if (filtros.proveedor) aplicados.push('proveedor');
  if (filtros.precioMin !== null || filtros.precioMax !== null)
    aplicados.push('precio');
  if (filtros.disponible !== null) aplicados.push('disponibilidad');

  return {
    filtrosAplicados: aplicados.length,
    detalles: aplicados,
    activo: aplicados.length > 0,
  };
};

/**
 * Resetear filtros a valores por defecto
 * @returns {Object} - Filtros por defecto
 */
export const obtenerFiltrosPorDefecto = () => ({
  busqueda: '',
  categorias: [],
  proveedor: null,
  precioMin: null,
  precioMax: null,
  disponible: null,
});
