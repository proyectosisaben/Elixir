import React, { useState, useEffect } from "react";
import { useRol } from "../contexts/RolContext";
import "../styles/globals.css";
import {
  FaChartLine,
  FaWarehouse,
  FaUsers,
  FaChartBar,
  FaExclamationTriangle,
  FaClipboard,
} from "react-icons/fa";

function Dashboard() {
  const { usuario } = useRol();
  const [metricas, setMetricas] = useState({
    ventasTotales: 0,
    ventasHoy: 0,
    productosTotal: 0,
    stockBajo: 0,
    clientes: 0,
    vendedores: 0,
    margenPromedio: 0,
  });
  const [alertas, setAlertas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [productos, setProductos] = useState([]);
  const [mostrarTodosProductos, setMostrarTodosProductos] = useState(false);

  useEffect(() => {
    cargarDatos();
    
    // Recargar datos cada 30 segundos para actualizar ventas en tiempo real
    const intervalo = setInterval(cargarDatos, 30000);
    
    return () => clearInterval(intervalo);
  }, [usuario]);

  const cargarDatos = async () => {
    try {
      // Obtener datos del endpoint dashboard-gerente
      const dashboardResponse = await fetch(`http://localhost:8000/api/dashboard-gerente/?usuario_id=${usuario?.id || 1}`);
      const productosResponse = await fetch("http://localhost:8000/api/productos/");
      
      const dashboardData = dashboardResponse.ok ? await dashboardResponse.json() : null;
      const productosData = productosResponse.ok ? await productosResponse.json() : null;

      // Procesar datos del dashboard
      if (dashboardData && dashboardData.estadisticas) {
        const stats = dashboardData.estadisticas;
        setMetricas({
          ventasTotales: parseFloat(stats.total_ventas) || 0,
          ventasHoy: Math.floor(Math.random() * 500000),
          productosTotal: parseInt(stats.total_pedidos) || 0,
          stockBajo: 0,
          clientes: parseInt(stats.total_clientes) || 0,
          vendedores: 0,
          margenPromedio: 32.5,
        });
      }

      // Procesar productos para alertas
      if (productosData) {
        let listaProductos = [];
        
        // Manejar diferentes formatos de respuesta
        if (Array.isArray(productosData.productos)) {
          listaProductos = productosData.productos;
        } else if (Array.isArray(productosData)) {
          listaProductos = productosData;
        } else if (typeof productosData === 'object') {
          listaProductos = Object.values(productosData).filter(item => typeof item === 'object' && item.id);
        }

        // Validar y filtrar productos válidos
        listaProductos = listaProductos.filter(p => {
          return p && typeof p === 'object' && p.id && p.nombre;
        });

        setProductos(listaProductos);
        
        const stockBajo = listaProductos.filter(p => {
          const stock = parseInt(p.stock) || 0;
          const minimo = parseInt(p.stock_minimo) || Infinity;
          return stock < minimo;
        }).length;

        setMetricas(prev => ({...prev, stockBajo, productosTotal: listaProductos.length}));

        // Generar alertas basadas en datos reales
        const nuevasAlertas = [];
        if (stockBajo > 0) {
          nuevasAlertas.push({
            id: 1,
            tipo: "stock",
            severidad: "alta",
            titulo: "Stock bajo",
            mensaje: `${stockBajo} bebidas con stock por debajo del mínimo`,
            cantidad: stockBajo,
          });
        }

        // Alerta de productos con poco margen
        const productosPocoMargen = listaProductos.filter(p => {
          const precio = parseFloat(p.precio) || 0;
          const costo = parseFloat(p.costo) || 0;
          const margen = costo > 0 ? ((precio - costo) / costo) * 100 : 0;
          return margen < 20;
        }).length;

        if (productosPocoMargen > 0) {
          nuevasAlertas.push({
            id: 2,
            tipo: "margen",
            severidad: "media",
            titulo: "Margen bajo",
            mensaje: `${productosPocoMargen} bebidas con margen de ganancia bajo (<20%)`,
            cantidad: productosPocoMargen,
          });
        }

        setAlertas(nuevasAlertas);
      }
    } catch (error) {
      console.error("Error cargando datos:", error);
      // Mantener datos por defecto si falla
      setAlertas([
        {
          id: 1,
          tipo: "stock",
          severidad: "media",
          titulo: "Error al cargar datos",
          mensaje: "No se pudieron cargar los datos del dashboard. Intenta recargar la página.",
          cantidad: 1,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const obtenerColorAlerta = (severidad) => {
    const colores = {
      alta: 'var(--danger-color)',
      media: 'var(--warning-color)',
      baja: 'var(--secondary-color)',
    };
    return colores[severidad] || 'var(--primary-color)';
  };

  const getSeveridadColor = (severidad) => {
    const colores = {
      alta: '#f56565',
      media: '#b7791f',
      baja: '#d69e2e',
    };
    return colores[severidad] || '#1a365d';
  };

  return (
    <div className="dashboard-gerente-container">
      {/* Header */}
      <div className="gerente-header">
        <div className="gerente-header-content">
          <div className="gerente-welcome">
            <FaChartLine className="header-icon" />
            <div>
              <h1>Panel de Gerente - Botillería Elixir</h1>
              <p>Supervisa ventas, inventario de bebidas y desempeño del equipo</p>
            </div>
          </div>
        </div>
      </div>

      <div className="gerente-main-container">
        {/* Metricas Principales - Siempre visible */}
        <div className="metricas-grid">
          <div className="metrica-card ventas-totales">
            <div className="metrica-header">
              <h3>Ventas Totales</h3>
              <FaChartLine className="metrica-icon" />
            </div>
            <p className="metrica-valor">${metricas.ventasTotales.toLocaleString('es-CL')}</p>
            <p className="metrica-periodo">Acumulado</p>
            <div className="metrica-bar">
              <div className="bar-fill" style={{ width: "85%", transition: "width 0.8s ease" }}></div>
            </div>
          </div>

          <div className="metrica-card productos-total">
            <div className="metrica-header">
              <h3>Inventario Bebidas</h3>
              <FaWarehouse className="metrica-icon" />
            </div>
            <p className="metrica-valor">{metricas.productosTotal}</p>
            <p className="metrica-periodo">SKUs en stock</p>
            <div className="metrica-bar">
              <div className="bar-fill" style={{ width: "60%", transition: "width 0.8s ease" }}></div>
            </div>
          </div>

          <div className="metrica-card clientes">
            <div className="metrica-header">
              <h3>Clientes Activos</h3>
              <FaUsers className="metrica-icon" />
            </div>
            <p className="metrica-valor">{metricas.clientes}</p>
            <p className="metrica-periodo">Registro total</p>
            <div className="metrica-bar">
              <div className="bar-fill" style={{ width: "45%", transition: "width 0.8s ease" }}></div>
            </div>
          </div>

          <div className="metrica-card margen">
            <div className="metrica-header">
              <h3>Margen Promedio</h3>
              <FaChartBar className="metrica-icon" />
            </div>
            <p className="metrica-valor">{metricas.margenPromedio}%</p>
            <p className="metrica-periodo">Ganancia promedio</p>
            <div className="metrica-bar">
              <div className="bar-fill" style={{ width: `${metricas.margenPromedio}%`, transition: "width 0.8s ease" }}></div>
            </div>
          </div>
        </div>

        {/* Loading Card */}
        {loading && (
          <>
            {/* Skeleton para alertas */}
            <div className="alertas-section">
              <h2>
                <FaExclamationTriangle /> Cargando alertas...
              </h2>
              <div className="alertas-list">
                {[1, 2].map((i) => (
                  <div key={i} className="alerta-item" style={{ borderLeftColor: 'var(--border-color)' }}>
                    <div className="alerta-content">
                      <div style={{ height: '16px', backgroundColor: 'var(--light-bg)', borderRadius: '4px', width: '150px', marginBottom: '8px' }}></div>
                      <div style={{ height: '14px', backgroundColor: 'var(--light-bg)', borderRadius: '4px', width: '250px' }}></div>
                    </div>
                    <div className="alerta-badge" style={{ backgroundColor: 'var(--light-bg)' }}></div>
                  </div>
                ))}
              </div>
            </div>

            {/* Skeleton para tabla */}
            <div className="productos-section">
              <h2>
                <FaClipboard /> Cargando inventario...
              </h2>
              <div className="productos-table">
                <table>
                  <thead>
                    <tr>
                      <th>Bebida</th>
                      <th>Categoría</th>
                      <th>Precio</th>
                      <th>Costo</th>
                      <th>Stock</th>
                      <th>Margen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[1, 2, 3, 4, 5].map((i) => (
                      <tr key={i}>
                        <td><div style={{ height: '16px', backgroundColor: 'var(--light-bg)', borderRadius: '4px', width: '100%' }}></div></td>
                        <td><div style={{ height: '16px', backgroundColor: 'var(--light-bg)', borderRadius: '4px', width: '80%' }}></div></td>
                        <td><div style={{ height: '16px', backgroundColor: 'var(--light-bg)', borderRadius: '4px', width: '70%' }}></div></td>
                        <td><div style={{ height: '16px', backgroundColor: 'var(--light-bg)', borderRadius: '4px', width: '70%' }}></div></td>
                        <td><div style={{ height: '16px', backgroundColor: 'var(--light-bg)', borderRadius: '4px', width: '50%' }}></div></td>
                        <td><div style={{ height: '16px', backgroundColor: 'var(--light-bg)', borderRadius: '4px', width: '60%' }}></div></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {/* Alertas - Solo si no está cargando */}
        {!loading && alertas.length > 0 && (
          <div className="alertas-section">
            <h2>
              <FaExclamationTriangle /> Alertas importantes
            </h2>
            <div className="alertas-list">
              {alertas.map((alerta) => (
                <div
                  key={alerta.id}
                  className="alerta-item"
                  style={{ borderLeftColor: getSeveridadColor(alerta.severidad) }}
                >
                  <div className="alerta-content">
                    <h4>{alerta.titulo}</h4>
                    <p>{alerta.mensaje}</p>
                  </div>
                  <div className="alerta-badge">{alerta.cantidad}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tabla de Bebidas - Solo si no está cargando */}
        {!loading && productos.length > 0 && (
          <div className="productos-section">
            <h2>
              <FaClipboard /> Inventario de Bebidas ({productos.length})
            </h2>
            <div className="productos-table">
              <table>
                <thead>
                  <tr>
                    <th>Bebida</th>
                    <th>Categoría</th>
                    <th>Precio</th>
                    <th>Costo</th>
                    <th>Stock</th>
                    <th>Margen</th>
                  </tr>
                </thead>
                <tbody>
                  {(mostrarTodosProductos ? productos : productos.slice(0, 10)).map((prod) => {
                    try {
                      // Validar que los valores necesarios existan
                      const nombre = prod.nombre || 'N/A';
                      const categoria = typeof prod.categoria === 'object' 
                        ? (prod.categoria?.nombre || 'N/A') 
                        : (prod.categoria || 'N/A');
                      const precio = parseFloat(prod.precio) || 0;
                      const costo = parseFloat(prod.costo) || 0;
                      const stock = parseInt(prod.stock) || 0;
                      const stockMinimo = parseInt(prod.stock_minimo) || 0;
                      
                      const margen = costo > 0 ? ((precio - costo) / costo) * 100 : 0;
                      
                      return (
                        <tr key={prod.id}>
                          <td><strong>{nombre}</strong></td>
                          <td>{String(categoria)}</td>
                          <td>${precio.toLocaleString('es-CL', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                          <td>${costo.toLocaleString('es-CL', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                          <td>
                            <span
                              style={{
                                color: stock < stockMinimo ? "red" : "green",
                                fontWeight: "bold",
                              }}
                            >
                              {stock}
                            </span>
                          </td>
                          <td><strong>{margen.toFixed(1)}%</strong></td>
                        </tr>
                      );
                    } catch (err) {
                      console.error('Error renderizando producto:', prod, err);
                      return null;
                    }
                  })}
                </tbody>
              </table>
            </div>
            {productos.length > 10 && (
              <div style={{ marginTop: '15px', textAlign: 'center' }}>
                <button
                  onClick={() => setMostrarTodosProductos(!mostrarTodosProductos)}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: 'var(--primary-color)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    fontWeight: 'bold',
                    transition: 'all 0.3s ease',
                  }}
                  onMouseEnter={(e) => e.target.style.transform = 'scale(1.05)'}
                  onMouseLeave={(e) => e.target.style.transform = 'scale(1)'}
                >
                  {mostrarTodosProductos ? '👆 Ver menos productos' : '👇 Ver todos los productos'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
