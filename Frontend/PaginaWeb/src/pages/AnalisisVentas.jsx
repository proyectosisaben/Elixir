import React, { useState, useEffect } from 'react';
import { FaChartBar, FaDollarSign, FaShoppingCart, FaDownload, FaFilter, FaChartLine, FaChartPie, FaCalendarAlt } from 'react-icons/fa';
import { useRol } from '../contexts/RolContext';
import { Line, Pie, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
} from 'chart.js';
import '../styles/globals.css';

// Registrar componentes de Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);
function AnalisisVentas() {
  const { usuario } = useRol();
  const [datos, setDatos] = useState(null);
  const [loading, setLoading] = useState(false); // Comienza en false, se activa al cargar datos
  const [filtros, setFiltros] = useState({
    period: 'monthly',
    fecha_inicio: '',
    fecha_fin: '',
    categoria_id: '',
    producto_id: '',
    vendedor_id: '',
    compare: false
  });
  const [mostrarFiltros, setMostrarFiltros] = useState(false);
  const [categorias, setCategorias] = useState([]);
  const [productos, setProductos] = useState([]);
  const [vendedores, setVendedores] = useState([]);

  // Cargar filtros disponibles solo una vez al montar el componente
  useEffect(() => {
    if (usuario && usuario.id) {
      console.log('Usuario disponible, cargando filtros...');
      cargarFiltros();
    }
  }, [usuario]);

  // Cargar datos cuando cambian los filtros O cuando el usuario cambia
  useEffect(() => {
    if (usuario && usuario.id) {
      console.log('Ejecutando cargarDatos con filtros:', filtros);
      cargarDatos();
    }
  }, [filtros, usuario]);

  const cargarDatos = async () => {
    try {
      setLoading(true);
      const queryParams = new URLSearchParams();

      // Agregar filtros
      Object.entries(filtros).forEach(([key, value]) => {
        if (value && value !== false) queryParams.append(key, value);
      });

      // Agregar user_id para autenticación
      if (usuario && usuario.id) {
        queryParams.append('user_id', usuario.id);
      }

      const url = `/api/ventas/analiticas/?${queryParams.toString()}`;
      console.log('🔍 Llamando endpoint:', url);
      console.log('📊 Filtros aplicados:', {
        period: filtros.period,
        categoria_id: filtros.categoria_id || 'Todas',
        producto_id: filtros.producto_id || 'Todos',
        vendedor_id: filtros.vendedor_id || 'Todos',
        fecha_inicio: filtros.fecha_inicio || 'Sin fecha',
        fecha_fin: filtros.fecha_fin || 'Sin fecha'
      });
      
      const response = await fetch(url);
      console.log('Respuesta status:', response.status);
      
      if (!response.ok) {
        console.error('Error en respuesta HTTP:', response.status, response.statusText);
        setDatos(null);
        setLoading(false);
        return;
      }

      const data = await response.json();
      console.log('✅ Datos recibidos:', data);

      // Validar que sea un objeto y que tenga la estructura correcta
      if (data && data.success && data.data && typeof data.data === 'object') {
        // Asegurar que las propiedades existan
        const datosLimpios = {
          series: Array.isArray(data.data.series) ? data.data.series : [],
          by_category: Array.isArray(data.data.by_category) ? data.data.by_category : [],
          by_product: Array.isArray(data.data.by_product) ? data.data.by_product : [],
          compare: data.data.compare || null
        };
        console.log('📈 Datos procesados:', {
          series: datosLimpios.series.length,
          categorias: datosLimpios.by_category.length,
          productos: datosLimpios.by_product.length
        });
        console.log('🎯 Categorías para gráfico:', datosLimpios.by_category);
        setDatos(datosLimpios);
      } else {
        console.error('Estructura de datos inválida:', data);
        setDatos(null);
      }
    } catch (error) {
      console.error('❌ Error cargando datos:', error);
      setDatos(null);
    } finally {
      setLoading(false);
    }
  };

  const cargarFiltros = async () => {
    try {
      console.log('Iniciando carga de filtros...');
      
      // Cargar categorías
      try {
        const catResponse = await fetch(`${window.API_BASE_URL}/api/categorias/');
        console.log('Respuesta categorías status:', catResponse.status);
        if (catResponse.ok) {
          const catData = await catResponse.json();
          console.log('Categorías cargadas:', catData);
          setCategorias(Array.isArray(catData) ? catData : []);
        } else {
          console.error('Error cargando categorías:', catResponse.status);
          setCategorias([]);
        }
      } catch (error) {
        console.error('Error en fetch de categorías:', error);
        setCategorias([]);
      }

      // Cargar productos
      try {
        const prodResponse = await fetch(`${window.API_BASE_URL}/api/productos-lista/');
        console.log('Respuesta productos status:', prodResponse.status);
        if (prodResponse.ok) {
          const prodData = await prodResponse.json();
          console.log('Productos cargados:', prodData);
          setProductos(Array.isArray(prodData) ? prodData : []);
        } else {
          console.error('Error cargando productos:', prodResponse.status);
          setProductos([]);
        }
      } catch (error) {
        console.error('Error en fetch de productos:', error);
        setProductos([]);
      }

      // Cargar vendedores
      if (usuario && usuario.id) {
        try {
          const vendResponse = await fetch(`${window.API_BASE_URL}/api/listar-clientes/?user_id=${usuario.id}`);
          console.log('Respuesta vendedores status:', vendResponse.status);
          if (vendResponse.ok) {
            const vendData = await vendResponse.json();
            console.log('Datos vendedores:', vendData);
            const vendedoresFiltrados = (vendData.clientes || []).filter(c => c.rol === 'vendedor');
            setVendedores(vendedoresFiltrados);
          } else {
            console.error('Error cargando vendedores:', vendResponse.status);
            setVendedores([]);
          }
        } catch (error) {
          console.error('Error en fetch de vendedores:', error);
          setVendedores([]);
        }
      }
      
      console.log('Filtros cargados correctamente');
    } catch (error) {
      console.error('Error general cargando filtros:', error);
      setCategorias([]);
      setProductos([]);
      setVendedores([]);
    }
  };

  const handleFiltroChange = (e) => {
    const { name, value, type, checked } = e.target;
    const newValue = type === 'checkbox' ? checked : value;
    console.log(`🔧 Filtro ${name} cambió a:`, newValue);
    setFiltros(prev => ({
      ...prev,
      [name]: newValue
    }));
  };

  const limpiarFiltros = () => {
    setFiltros({
      period: 'monthly',
      fecha_inicio: '',
      fecha_fin: '',
      categoria_id: '',
      producto_id: '',
      vendedor_id: '',
      compare: false
    });
  };

  const formatearMoneda = (valor) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP'
    }).format(valor);
  };

  const formatearFecha = (fechaString) => {
    if (!fechaString) return 'N/A';
    try {
      const date = new Date(fechaString);
      return date.toLocaleDateString('es-CL');
    } catch {
      return fechaString;
    }
  };

  const calcularTotalVentas = () => {
    if (!datos?.series) return 0;
    return datos.series.reduce((total, item) => total + (item.total || 0), 0);
  };

  const exportarDatos = () => {
    const queryParams = new URLSearchParams();
    Object.entries(filtros).forEach(([key, value]) => {
      if (value && value !== false) queryParams.append(key, value);
    });
    if (usuario && usuario.id) {
      queryParams.append('user_id', usuario.id);
    }
    window.open(`/api/ventas/exportar/?${queryParams.toString()}`, '_blank');
  };

  // Función para generar datos del gráfico de línea (ventas por período)
  const obtenerGraficoSeries = () => {
    if (!datos || !datos.series || datos.series.length === 0) {
      return null;
    }

    const labels = datos.series.map(item => {
      const fecha = new Date(item.period);
      if (filtros.period === 'daily') {
        return fecha.toLocaleDateString('es-CL');
      } else if (filtros.period === 'weekly') {
        return `Semana ${Math.ceil(fecha.getDate() / 7)}`;
      } else if (filtros.period === 'monthly') {
        return fecha.toLocaleDateString('es-CL', { month: 'long', year: 'numeric' });
      } else {
        return fecha.getFullYear();
      }
    });

    const chartData = {
      labels: labels,
      datasets: [
        {
          label: 'Ventas',
          data: datos.series.map(item => item.total),
          borderColor: '#1a73e8',
          backgroundColor: 'rgba(26, 115, 232, 0.1)',
          tension: 0.3,
          fill: true,
          pointBackgroundColor: '#1a73e8',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7
        }
      ]
    };

    return {
      data: chartData,
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              font: { size: 12 },
              color: '#333'
            }
          },
          title: {
            display: false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: function(value) {
                return '$' + value.toLocaleString('es-CL');
              }
            }
          }
        }
      }
    };
  };

  // Función para generar datos del gráfico de pastel (ventas por categoría)
  const obtenerGraficoCategoria = () => {
    if (!datos || !datos.by_category || datos.by_category.length === 0) {
      return null;
    }

    const colores = [
      '#1a73e8', '#34a853', '#fbbc04', '#ea4335', '#4285f4',
      '#ab47bc', '#00bcd4', '#ff7043', '#8bc34a', '#ff9800'
    ];

    // Calcular total para porcentajes
    const totalVentas = datos.by_category.reduce((sum, item) => sum + item.total, 0);
    
    // Crear labels con porcentajes
    const labelsConPorcentaje = datos.by_category.map(item => {
      const porcentaje = totalVentas > 0 ? ((item.total / totalVentas) * 100).toFixed(1) : 0;
      return `${item.categoria} (${porcentaje}%)`;
    });

    const chartData = {
      labels: labelsConPorcentaje,
      datasets: [
        {
          label: 'Ventas por Categoría',
          data: datos.by_category.map(item => item.total),
          backgroundColor: colores.slice(0, datos.by_category.length),
          borderColor: '#fff',
          borderWidth: 2
        }
      ]
    };

    return {
      data: chartData,
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          datalabels: {
            color: '#fff',
            font: {
              weight: 'bold',
              size: 12
            }
          },
          legend: {
            display: true,
            position: 'right',
            labels: {
              font: { size: 11 },
              color: '#333',
              padding: 15,
              generateLabels: (chart) => {
                const data = chart.data;
                return data.labels.map((label, i) => ({
                  text: label,
                  fillStyle: data.datasets[0].backgroundColor[i],
                  hidden: false,
                  index: i
                }));
              }
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const porcentaje = ((context.parsed / total) * 100).toFixed(1);
                const valor = '$' + context.parsed.toLocaleString('es-CL');
                return `${valor} (${porcentaje}%)`;
              }
            }
          }
        }
      }
    };
  };

  // Función para generar datos del gráfico de barras (productos más vendidos)
  const obtenerGraficoProductos = () => {
    if (!datos || !datos.by_product || datos.by_product.length === 0) {
      return null;
    }

    // Tomar top 10 productos
    const topProductos = datos.by_product.slice(0, 10);

    const chartData = {
      labels: topProductos.map(item => item.producto.substring(0, 20) + (item.producto.length > 20 ? '...' : '')),
      datasets: [
        {
          label: 'Ingresos Totales',
          data: topProductos.map(item => item.total),
          backgroundColor: '#34a853',
          borderColor: '#2d8659',
          borderWidth: 1
        }
      ]
    };

    return {
      data: chartData,
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              font: { size: 12 },
              color: '#333'
            }
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            ticks: {
              callback: function(value) {
                return '$' + value.toLocaleString('es-CL');
              }
            }
          }
        }
      }
    };
  };

  return (
    <div className="analisis-ventas-container">
      <div className="analisis-header">
        <div className="header-content">
          <FaChartBar className="header-icon" />
          <div>
            <h1>Análisis de Ventas</h1>
            <p>Gráficos interactivos y métricas de rendimiento</p>
          </div>
        </div>
        <div className="header-actions">
          <button
            className="btn-filtros"
            onClick={() => setMostrarFiltros(!mostrarFiltros)}
          >
            <FaFilter /> Filtros
          </button>
          <button className="btn-exportar" onClick={exportarDatos}>
            <FaDownload /> Exportar PDF
          </button>
        </div>
      </div>

      {mostrarFiltros && (
        <div className="filtros-container">
          <div className="filtros-grid">
            <div className="filtro-group">
              <label>Período:</label>
              <select name="period" value={filtros.period} onChange={handleFiltroChange}>
                <option value="daily">Diario</option>
                <option value="weekly">Semanal</option>
                <option value="monthly">Mensual</option>
                <option value="yearly">Anual</option>
              </select>
            </div>

            <div className="filtro-group">
              <label>Fecha Inicio:</label>
              <input
                type="date"
                name="fecha_inicio"
                value={filtros.fecha_inicio}
                onChange={handleFiltroChange}
              />
            </div>

            <div className="filtro-group">
              <label>Fecha Fin:</label>
              <input
                type="date"
                name="fecha_fin"
                value={filtros.fecha_fin}
                onChange={handleFiltroChange}
              />
            </div>

            <div className="filtro-group">
              <label>Categoría:</label>
              <select name="categoria_id" value={filtros.categoria_id} onChange={handleFiltroChange}>
                <option value="">Todas las categorías</option>
                {categorias.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.nombre}</option>
                ))}
              </select>
            </div>

            <div className="filtro-group">
              <label>Producto:</label>
              <select name="producto_id" value={filtros.producto_id} onChange={handleFiltroChange}>
                <option value="">Todos los productos</option>
                {productos.map(prod => (
                  <option key={prod.id} value={prod.id}>{prod.nombre}</option>
                ))}
              </select>
            </div>

            <div className="filtro-group">
              <label>Vendedor:</label>
              <select name="vendedor_id" value={filtros.vendedor_id} onChange={handleFiltroChange}>
                <option value="">Todos los vendedores</option>
                {vendedores.map(vend => (
                  <option key={vend.id} value={vend.id}>{vend.user.first_name || vend.user.username}</option>
                ))}
              </select>
            </div>

            <div className="filtro-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  name="compare"
                  checked={filtros.compare}
                  onChange={handleFiltroChange}
                />
                Comparar con período anterior
              </label>
            </div>
          </div>

          <div className="filtros-actions">
            <button className="btn-limpiar" onClick={limpiarFiltros}>
              Limpiar Filtros
            </button>
          </div>
        </div>
      )}

      <div className="analisis-main">
        {loading ? (
          <div className="loading">Cargando análisis de ventas...</div>
        ) : datos ? (
          <>
            {/* Métricas principales */}
            <div className="metricas-grid">
              <div className="metrica-card">
                <div className="metrica-header">
                  <FaDollarSign className="metrica-icon" />
                  <h3>Ventas Totales</h3>
                </div>
                <p className="metrica-valor">{formatearMoneda(calcularTotalVentas())}</p>
                <span className="metrica-label">En el período seleccionado</span>
              </div>

              <div className="metrica-card">
                <div className="metrica-header">
                  <FaShoppingCart className="metrica-icon" />
                  <h3>Total Pedidos</h3>
                </div>
                <p className="metrica-valor">{datos.series?.length || 0}</p>
                <span className="metrica-label">Pedidos en el período</span>
              </div>

              {datos.compare && (
                <>
                  <div className="metrica-card">
                    <div className="metrica-header">
                      <FaChartLine className="metrica-icon" />
                      <h3>Período Actual</h3>
                    </div>
                    <p className="metrica-valor">{formatearMoneda(datos.compare.current)}</p>
                    <span className="metrica-label">Ventas actuales</span>
                  </div>

                  <div className="metrica-card">
                    <div className="metrica-header">
                      <FaCalendarAlt className="metrica-icon" />
                      <h3>Período Anterior</h3>
                    </div>
                    <p className="metrica-valor">{formatearMoneda(datos.compare.previous)}</p>
                    <span className="metrica-label">Ventas anteriores</span>
                  </div>
                </>
              )}
            </div>

            {/* Gráfico de ventas por período */}
            {datos.series && datos.series.length > 0 ? (
              <div className="chart-section">
                <h3>Ventas por {filtros.period === 'daily' ? 'Día' : filtros.period === 'weekly' ? 'Semana' : filtros.period === 'monthly' ? 'Mes' : 'Año'}</h3>
                {obtenerGraficoSeries() ? (
                  <div className="chart-container">
                    <Line data={obtenerGraficoSeries().data} options={obtenerGraficoSeries().options} />
                  </div>
                ) : (
                  <div className="empty-state">
                    <p>No hay datos para mostrar</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="chart-section">
                <h3>Ventas por {filtros.period === 'daily' ? 'Día' : filtros.period === 'weekly' ? 'Semana' : filtros.period === 'monthly' ? 'Mes' : 'Año'}</h3>
                <div className="empty-state">
                  <p>No hay datos disponibles para este período y filtros seleccionados</p>
                </div>
              </div>
            )}

            {/* Ventas por categoría */}
            {datos.by_category && datos.by_category.length > 0 ? (
              <div className="chart-section">
                <h3>📊 Ventas por Categoría</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: '30px', alignItems: 'start', marginTop: '20px' }}>
                  {/* Gráfico */}
                  <div style={{ display: 'flex', justifyContent: 'center' }}>
                    {obtenerGraficoCategoria() ? (
                      <div className="chart-container" style={{ height: '320px', maxWidth: '350px' }}>
                        <Pie data={obtenerGraficoCategoria().data} options={obtenerGraficoCategoria().options} />
                      </div>
                    ) : (
                      <div className="empty-state">
                        <p>No hay datos para mostrar</p>
                      </div>
                    )}
                  </div>
                  
                  {/* Tabla de datos */}
                  <div>
                    <table className="tabla-categorias">
                      <thead>
                        <tr>
                          <th>Categoría</th>
                          <th>Ventas Totales</th>
                          <th>Porcentaje</th>
                        </tr>
                      </thead>
                      <tbody>
                        {datos.by_category.map((cat, idx) => {
                          const totalVentas = datos.by_category.reduce((sum, item) => sum + item.total, 0);
                          const porcentaje = totalVentas > 0 ? ((cat.total / totalVentas) * 100).toFixed(1) : 0;
                          const colores = ['#1a73e8', '#34a853', '#fbbc04', '#ea4335', '#4285f4', '#ab47bc', '#00bcd4', '#ff7043', '#8bc34a', '#ff9800'];
                          const color = colores[idx % colores.length];
                          
                          return (
                            <tr key={idx}>
                              <td>
                                <span className="color-indicator" style={{ backgroundColor: color }}></span>
                                <span className="categoria-cell">{cat.categoria}</span>
                              </td>
                              <td>
                                <span className="venta-valor">${cat.total.toLocaleString('es-CL')}</span>
                              </td>
                              <td>
                                <span className="porcentaje-badge">{porcentaje}%</span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                      <tfoot>
                        <tr>
                          <td>TOTAL</td>
                          <td>
                            <span className="venta-valor">${datos.by_category.reduce((sum, item) => sum + item.total, 0).toLocaleString('es-CL')}</span>
                          </td>
                          <td>
                            <span className="porcentaje-badge">100%</span>
                          </td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                </div>
              </div>
            ) : (
              <div className="chart-section">
                <h3>📊 Ventas por Categoría</h3>
                <div className="empty-state">
                  <p>No hay datos de categorías disponibles con los filtros seleccionados</p>
                </div>
              </div>
            )}

            {/* Productos más vendidos */}
            {datos.by_product && datos.by_product.length > 0 ? (
              <div className="productos-vendidos-section">
                <h3>Top 10 Productos Más Vendidos</h3>
                {obtenerGraficoProductos() ? (
                  <div className="chart-container">
                    <Bar data={obtenerGraficoProductos().data} options={obtenerGraficoProductos().options} />
                  </div>
                ) : (
                  <div className="empty-state">
                    <p>No hay datos para mostrar</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="productos-vendidos-section">
                <h3>Productos Más Vendidos</h3>
                <div className="empty-state">
                  <p>No hay productos vendidos en este período</p>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="error-state">
            <p>Error al cargar el análisis de ventas</p>
            <button onClick={cargarDatos} className="btn-retry">
              Reintentar
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default AnalisisVentas;
