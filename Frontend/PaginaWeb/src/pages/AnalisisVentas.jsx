import React, { useState, useEffect } from 'react';
import { FaChartBar, FaDollarSign, FaShoppingCart } from 'react-icons/fa';
import '../styles/globals.css';

function AnalisisVentas() {
  const [estadisticas, setEstadisticas] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    cargarEstadisticas();
  }, []);

  const cargarEstadisticas = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/ventas/analiticas/');
      const data = await response.json();

      if (response.ok && data.success) {
        setEstadisticas(data.estadisticas);
      }
    } catch (error) {
      console.error('Error cargando estadísticas:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatearMoneda = (valor) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP'
    }).format(valor);
  };

  return (
    <div className="analisis-ventas-container">
      <div className="analisis-header">
        <div className="header-content">
          <FaChartBar className="header-icon" />
          <div>
            <h1>Análisis de Ventas</h1>
            <p>Reportes y métricas de rendimiento</p>
          </div>
        </div>
      </div>

      <div className="analisis-main">
        {loading ? (
          <div className="loading">Cargando estadísticas...</div>
        ) : estadisticas ? (
          <>
            <div className="metricas-grid">
              <div className="metrica-card">
                <div className="metrica-header">
                  <FaDollarSign className="metrica-icon" />
                  <h3>Ventas Totales</h3>
                </div>
                <p className="metrica-valor">{formatearMoneda(estadisticas.ventas_totales || 0)}</p>
                <span className="metrica-label">En el período seleccionado</span>
              </div>

              <div className="metrica-card">
                <div className="metrica-header">
                  <FaShoppingCart className="metrica-icon" />
                  <h3>Total Pedidos</h3>
                </div>
                <p className="metrica-valor">{estadisticas.total_pedidos || 0}</p>
                <span className="metrica-label">Pedidos realizados</span>
              </div>
            </div>

            {estadisticas.productos_mas_vendidos && estadisticas.productos_mas_vendidos.length > 0 && (
              <div className="productos-vendidos-section">
                <h3>Productos Más Vendidos</h3>
                <div className="productos-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Producto</th>
                        <th>Cantidad</th>
                        <th>Ingresos</th>
                      </tr>
                    </thead>
                    <tbody>
                      {estadisticas.productos_mas_vendidos.map((producto, index) => (
                        <tr key={index}>
                          <td>{producto.nombre}</td>
                          <td>{producto.cantidad_vendida}</td>
                          <td>{formatearMoneda(producto.ingresos_totales)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="error-state">
            <p>Error al cargar las estadísticas</p>
            <button onClick={cargarEstadisticas} className="btn-retry">
              Reintentar
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default AnalisisVentas;
