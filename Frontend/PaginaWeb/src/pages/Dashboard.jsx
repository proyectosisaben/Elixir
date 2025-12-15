import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useRol } from "../contexts/RolContext";
import "../styles/globals.css";
import {
  FaChartLine,
  FaWarehouse,
  FaUsers,
  FaChartBar,
  FaExclamationTriangle,
  FaClipboard,
  FaFilter,
  FaCalendarAlt,
  FaDownload,
  FaEye,
  FaSearch,
} from "react-icons/fa";
import { enviarEmailPedidoEntregado } from "../services/emailService";

function Dashboard() {
  const navigate = useNavigate();
  const { usuario, tieneRol } = useRol();

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


  // Estado para búsqueda de clientes - HU 23
  const [busquedaClientes, setBusquedaClientes] = useState('');
  const [resultadosClientes, setResultadosClientes] = useState([]);
  const [mostrarBuscadorClientes, setMostrarBuscadorClientes] = useState(true);

  // Estado para gestión de pedidos
  const [pedidos, setPedidos] = useState([]);
  const [cargandoPedidos, setCargandoPedidos] = useState(false);
  const [filtroEstadoPedido, setFiltroEstadoPedido] = useState('todos');

  // Estado para filtros avanzados - HU 50
  const [mostrarFiltros, setMostrarFiltros] = useState(false);
  const [ventasFiltradas, setVentasFiltradas] = useState(null);
  const [filtros, setFiltros] = useState({
    fecha_inicio: '',
    fecha_fin: '',
    vendedor_id: '',
    estado: '',
    producto_id: '',
    agrupar_por: 'dia'
  });
  const [vendedores, setVendedores] = useState([]);

  useEffect(() => {
    if (usuario && (tieneRol('vendedor') || tieneRol('gerente') || tieneRol('admin_sistema'))) {
      cargarDatos();

      // Solo gerentes y admin_sistema pueden ver vendedores
      if (tieneRol('gerente') || tieneRol('admin_sistema')) {
        cargarVendedores();
      }

      // Cargar pedidos para gestión (vendedores, gerentes y admin_sistema)
      cargarPedidos();

      // Recargar datos cada 30 segundos para actualizar ventas en tiempo real
      const intervalo = setInterval(cargarDatos, 30000);

      return () => clearInterval(intervalo);
    }
  }, [usuario, tieneRol]);

  const cargarVendedores = async () => {
    try {
      const response = await fetch(`/api/listar-clientes/?user_id=${usuario?.id}`);
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          const vendedoresList = data.clientes.filter(c => c.rol === 'vendedor');
          setVendedores(vendedoresList);
        }
      }
    } catch (error) {
      console.error('Error cargando vendedores:', error);
    }
  };

  const cargarVentasFiltradas = async () => {
    try {
      const queryParams = new URLSearchParams();
      queryParams.append('user_id', usuario?.id);

      // Agregar filtros
      Object.entries(filtros).forEach(([key, value]) => {
        if (value) queryParams.append(key, value);
      });

      const response = await fetch(`/api/ventas/filtradas-gerente/?${queryParams.toString()}`);
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setVentasFiltradas(data);
        }
      } else {
        console.error('Error en ventas filtradas:', await response.json());
      }
    } catch (error) {
      console.error('Error cargando ventas filtradas:', error);
    }
  };

  const handleFiltroChange = (e) => {
    const { name, value } = e.target;
    setFiltros(prev => ({ ...prev, [name]: value }));
  };

  const aplicarFiltros = () => {
    cargarVentasFiltradas();
  };

  const limpiarFiltros = () => {
    setFiltros({
      fecha_inicio: '',
      fecha_fin: '',
      vendedor_id: '',
      estado: '',
      producto_id: '',
      agrupar_por: 'dia'
    });
    setVentasFiltradas(null);
  };

  // Funciones para búsqueda de clientes - HU 23
  const buscarClientes = async () => {
    if (!busquedaClientes.trim()) {
      setResultadosClientes([]);
      return;
    }

    try {
      const response = await fetch(`/api/clientes/buscar/?user_id=${usuario?.id}&q=${encodeURIComponent(busquedaClientes)}`);
      const data = await response.json();

      if (response.ok && data.success) {
        setResultadosClientes(data.clientes || []);
      } else {
        console.error('Error buscando clientes:', data);
      }
    } catch (error) {
      console.error('Error en búsqueda de clientes:', error);
    }
  };

  const handleBusquedaClientesChange = (e) => {
    setBusquedaClientes(e.target.value);
  };

  const ejecutarBusqueda = (e) => {
    e.preventDefault();
    buscarClientes();
  };

  const verDetalleCliente = (clienteId) => {
    navigate(`/clientes/${clienteId}`);
  };

  // Funciones para gestión de pedidos
  const cargarPedidos = async () => {
    setCargandoPedidos(true);
    try {
      const response = await fetch(`/api/pedidos/gestion/?usuario_id=${usuario?.id}&estado=${filtroEstadoPedido}`);
      const data = await response.json();

      if (response.ok && data.success) {
        setPedidos(data.pedidos || []);
      } else {
        console.error('Error cargando pedidos:', data);
        setPedidos([]);
      }
    } catch (error) {
      console.error('Error al cargar pedidos:', error);
      setPedidos([]);
    } finally {
      setCargandoPedidos(false);
    }
  };

  const cambiarEstadoPedido = async (pedidoId, nuevoEstado) => {
    try {
      // Buscar datos del pedido para el email
      const pedidoActual = pedidos.find(p => p.id === pedidoId);
      
      const response = await fetch('/api/cambiar-estado-pedido/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          usuario_id: usuario?.id,
          pedido_id: pedidoId,
          estado: nuevoEstado
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Si el nuevo estado es "entregado", enviar email al cliente
        if (nuevoEstado === 'entregado' && pedidoActual) {
          try {
            await enviarEmailPedidoEntregado({
              clienteEmail: pedidoActual.cliente_email,
              clienteNombre: pedidoActual.cliente_nombre || pedidoActual.cliente_email?.split('@')[0],
              numeroPedido: pedidoActual.numero_pedido,
              fechaEntrega: new Date()
            });
            console.log('✅ Email de entrega enviado al cliente');
          } catch (emailError) {
            console.error('Error enviando email de entrega:', emailError);
            // No bloquear el flujo si falla el email
          }
        }
        
        // Recargar pedidos para mostrar el cambio
        cargarPedidos();
        alert(`✅ ${data.message}`);
      } else {
        alert(`❌ Error: ${data.message}`);
      }
    } catch (error) {
      console.error('Error cambiando estado del pedido:', error);
      alert('❌ Error al cambiar el estado del pedido');
    }
  };

  const cargarDatos = async () => {
    try {
      setLoading(true);

      // Obtener datos del endpoint dashboard-admin
      const dashboardResponse = await fetch(`/api/dashboard-admin/?usuario_id=${usuario?.id || 1}`);
      const productosResponse = await fetch("/api/productos/");

      let dashboardData = null;
      if (dashboardResponse.ok) {
        dashboardData = await dashboardResponse.json();
      } else {
        const errorData = await dashboardResponse.json().catch(() => null);
        console.error('Error en dashboard:', errorData);
      }

      const productosData = productosResponse.ok ? await productosResponse.json() : null;

      // Procesar datos del dashboard
      if (dashboardData && dashboardData.estadisticas) {
        const stats = dashboardData.estadisticas;

        // Calcular ventas de hoy desde ventas_por_dia si está disponible
        let ventasHoy = 0;
        if (stats.ventas_por_dia && stats.ventas_por_dia.length > 0) {
          const hoy = new Date().toISOString().split('T')[0];
          const ventaHoy = stats.ventas_por_dia.find(v => v.fecha.startsWith(hoy));
          ventasHoy = ventaHoy ? parseFloat(ventaHoy.total_ventas) : 0;
        }

        setMetricas({
          ventasTotales: parseFloat(stats.total_ventas) || 0,
          ventasHoy: ventasHoy,
          productosTotal: parseInt(stats.total_pedidos) || 0,
          stockBajo: 0,
          clientes: parseInt(stats.total_clientes) || 0,
          vendedores: 0,
          margenPromedio: 32.5,
        });
      } else if (dashboardData && dashboardData.success === false) {
        // Si hay error de permisos, mostrar mensaje
        console.error('Error de permisos:', dashboardData.message);
        setMetricas(prev => ({
          ...prev,
          productosTotal: -1, // Indicador de error
        }));
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

  // Si no hay usuario o no tiene rol de gerente, mostrar mensaje
  // Verificar si está cargando
  if (!usuario) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="alert alert-warning text-center">
          <h3>⚠️ Cargando...</h3>
          <p>Verificando permisos de acceso...</p>
        </div>
      </div>
    );
  }

  // Verificar permisos
  const tieneAcceso = tieneRol('vendedor') || tieneRol('gerente') || tieneRol('admin_sistema');

  if (!tieneAcceso) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="alert alert-danger text-center">
          <h3>❌ Acceso Denegado</h3>
          <p>No tienes permisos para acceder a esta página.</p>
          <p>Rol actual: <strong>{usuario?.rol || 'desconocido'}</strong></p>
          <a href="/" className="btn btn-primary">Volver al inicio</a>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-administrativo-container">
      {/* Mostrar error si no se pudieron cargar datos */}
      {metricas.productosTotal === -1 && (
        <div className="alert alert-warning m-3">
          <h4>⚠️ Algunos datos no se pudieron cargar</h4>
          <p>Las estadísticas principales pueden no estar disponibles, pero puedes usar el buscador de clientes normalmente.</p>
          <p>Si el problema persiste, verifica tu conexión a internet.</p>
        </div>
      )}

      {/* Header */}
      <div className="admin-header">
        <div className="admin-header-content">
          <div className="admin-welcome">
            <FaChartLine className="header-icon" />
            <div>
              <h1>Panel Administrativo - Botillería Elixir</h1>
              <p>Supervisa ventas, inventario de bebidas, desempeño del equipo y consulta clientes</p>
            </div>
          </div>
        </div>
      </div>

      <div className="admin-main-container">
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
            <p className="metrica-valor">
              {metricas.productosTotal === -1 ? 'Error' : metricas.productosTotal}
            </p>
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

        {/* Buscador de Clientes - HU 23 */}
        <div className="buscador-clientes-section">
          <div className="buscador-header">
            <h3>
              <FaSearch /> Buscar Clientes
            </h3>
            <button
              className="btn-toggle-buscador"
              onClick={() => setMostrarBuscadorClientes(!mostrarBuscadorClientes)}
            >
              {mostrarBuscadorClientes ? '🔽 Ocultar' : '🔼 Mostrar'} Buscador de Clientes
            </button>
          </div>

          {mostrarBuscadorClientes && (
            <div className="buscador-content">
              <form onSubmit={ejecutarBusqueda} className="buscador-form">
                <div className="buscador-input-group">
                  <input
                    type="text"
                    placeholder="Buscar por nombre, email o apellido..."
                    value={busquedaClientes}
                    onChange={handleBusquedaClientesChange}
                    className="buscador-input"
                  />
                  <button type="submit" className="btn-buscar">
                    <FaSearch /> Buscar
                  </button>
                </div>
              </form>

              {resultadosClientes.length > 0 && (
                <div className="resultados-clientes">
                  <h4>Resultados ({resultadosClientes.length})</h4>
                  <div className="clientes-grid">
                    {resultadosClientes.map(cliente => (
                      <div key={cliente.id} className="cliente-card-resultado">
                        <div className="cliente-info">
                          <h5>{cliente.user.first_name} {cliente.user.last_name}</h5>
                          <p className="cliente-email">{cliente.user.email}</p>
                          <div className="cliente-stats">
                            <span className="stat">{cliente.estadisticas.total_pedidos} pedidos</span>
                            <span className="stat">${cliente.estadisticas.total_gastado.toLocaleString('es-CL')} gastado</span>
                          </div>
                        </div>
                        <button
                          className="btn-ver-detalle"
                          onClick={() => verDetalleCliente(cliente.id)}
                        >
                          Ver Detalle
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {busquedaClientes && resultadosClientes.length === 0 && (
                <div className="no-resultados">
                  <p>No se encontraron clientes que coincidan con "{busquedaClientes}"</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Gestión de Pedidos */}
        <div className="gestion-pedidos-section">
          <div className="section-header">
            <h2>
              <FaClipboard /> Gestión de Pedidos
            </h2>
            <button
              className="btn-actualizar"
              onClick={cargarPedidos}
              disabled={cargandoPedidos}
            >
              {cargandoPedidos ? 'Cargando...' : 'Actualizar'}
            </button>
          </div>

          <div className="filtros-pedidos">
            <div className="filtro-group">
              <label htmlFor="filtro-estado">Estado del Pedido</label>
              <select
                id="filtro-estado"
                value={filtroEstadoPedido}
                onChange={(e) => setFiltroEstadoPedido(e.target.value)}
              >
                <option value="todos">Todos los estados</option>
                <option value="pendiente">Pendiente</option>
                <option value="pagado">Pagado</option>
                <option value="en_preparacion">En Preparación</option>
                <option value="enviado">Enviado</option>
                <option value="entregado">Entregado</option>
                <option value="cancelado">Cancelado</option>
              </select>
            </div>
            <button
              className="btn-filtrar"
              onClick={cargarPedidos}
            >
              Filtrar
            </button>
          </div>

          {cargandoPedidos ? (
            <div className="loading">
              <div className="spinner"></div>
              <p>Cargando pedidos...</p>
            </div>
          ) : pedidos.length === 0 ? (
            <div className="empty-state">
              <FaClipboard className="empty-icon" />
              <h3>No hay pedidos</h3>
              <p>No se encontraron pedidos con el filtro seleccionado.</p>
            </div>
          ) : (
            <div className="pedidos-table-container">
              <table className="pedidos-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Número</th>
                    <th>Cliente</th>
                    <th>Total</th>
                    <th>Estado</th>
                    <th>Fecha</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {pedidos.map((pedido) => (
                    <tr key={pedido.id}>
                      <td>{pedido.id}</td>
                      <td>{pedido.numero_pedido}</td>
                      <td>{pedido.cliente_email}</td>
                      <td>${pedido.total?.toFixed(2)}</td>
                      <td>
                        <span className={`estado-badge estado-${pedido.estado}`}>
                          {pedido.estado_display}
                        </span>
                      </td>
                      <td>{new Date(pedido.fecha_pedido).toLocaleDateString('es-CL')}</td>
                      <td>
                        <div className="acciones-pedido">
                          {pedido.estado === 'pendiente' && (
                            <button
                              className="btn-accion btn-pagado"
                              onClick={() => cambiarEstadoPedido(pedido.id, 'pagado')}
                              title="Marcar como pagado"
                            >
                              💰 Pagar
                            </button>
                          )}
                          {pedido.estado === 'pagado' && (
                            <button
                              className="btn-accion btn-preparacion"
                              onClick={() => cambiarEstadoPedido(pedido.id, 'en_preparacion')}
                              title="Marcar como en preparación"
                            >
                              📦 Preparar
                            </button>
                          )}
                          {(pedido.estado === 'pagado' || pedido.estado === 'en_preparacion') && (
                            <button
                              className="btn-accion btn-enviado"
                              onClick={() => cambiarEstadoPedido(pedido.id, 'enviado')}
                              title="Marcar como enviado"
                            >
                              🚚 Enviar
                            </button>
                          )}
                          {pedido.estado === 'enviado' && (
                            <button
                              className="btn-accion btn-entregado"
                              onClick={() => cambiarEstadoPedido(pedido.id, 'entregado')}
                              title="Marcar como entregado"
                            >
                              ✅ Entregar
                            </button>
                          )}
                          {pedido.estado !== 'entregado' && pedido.estado !== 'cancelado' && (
                            <button
                              className="btn-accion btn-cancelar"
                              onClick={() => cambiarEstadoPedido(pedido.id, 'cancelado')}
                              title="Cancelar pedido"
                            >
                              ❌ Cancelar
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
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

        {/* Filtros Avanzados de Ventas - HU 50 */}
        <div className="filtros-ventas-section">
          <div className="section-header">
            <h2>
              <FaFilter /> Filtros Avanzados de Ventas
            </h2>
            <button
              className="btn-filtros"
              onClick={() => setMostrarFiltros(!mostrarFiltros)}
            >
              <FaEye /> {mostrarFiltros ? 'Ocultar Filtros' : 'Mostrar Filtros'}
            </button>
          </div>

          {mostrarFiltros && (
            <div className="filtros-container">
              <div className="filtros-grid">
                <div className="filtro-group">
                  <label htmlFor="fecha_inicio">Fecha Inicio</label>
                  <input
                    type="date"
                    id="fecha_inicio"
                    name="fecha_inicio"
                    value={filtros.fecha_inicio}
                    onChange={handleFiltroChange}
                  />
                </div>
                <div className="filtro-group">
                  <label htmlFor="fecha_fin">Fecha Fin</label>
                  <input
                    type="date"
                    id="fecha_fin"
                    name="fecha_fin"
                    value={filtros.fecha_fin}
                    onChange={handleFiltroChange}
                  />
                </div>
                <div className="filtro-group">
                  <label htmlFor="vendedor_id">Vendedor</label>
                  <select
                    id="vendedor_id"
                    name="vendedor_id"
                    value={filtros.vendedor_id}
                    onChange={handleFiltroChange}
                  >
                    <option value="">Todos los vendedores</option>
                    {vendedores.map(vendedor => (
                      <option key={vendedor.usuario_id} value={vendedor.usuario_id}>
                        {vendedor.nombre}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="filtro-group">
                  <label htmlFor="estado">Estado del Pedido</label>
                  <select
                    id="estado"
                    name="estado"
                    value={filtros.estado}
                    onChange={handleFiltroChange}
                  >
                    <option value="">Todos los estados</option>
                    <option value="pagado">Pagado</option>
                    <option value="en_preparacion">En Preparación</option>
                    <option value="enviado">Enviado</option>
                    <option value="entregado">Entregado</option>
                    <option value="cancelado">Cancelado</option>
                  </select>
                </div>
                <div className="filtro-group">
                  <label htmlFor="agrupar_por">Agrupar Por</label>
                  <select
                    id="agrupar_por"
                    name="agrupar_por"
                    value={filtros.agrupar_por}
                    onChange={handleFiltroChange}
                  >
                    <option value="dia">Día</option>
                    <option value="semana">Semana</option>
                    <option value="mes">Mes</option>
                  </select>
                </div>
              </div>
              <div className="filtros-actions">
                <button className="btn-aplicar" onClick={aplicarFiltros}>
                  <FaFilter /> Aplicar Filtros
                </button>
                <button className="btn-limpiar" onClick={limpiarFiltros}>
                  <FaDownload /> Limpiar Filtros
                </button>
              </div>
            </div>
          )}

          {/* Resultados de Ventas Filtradas */}
          {ventasFiltradas && (
            <div className="ventas-filtradas-resultados">
              <div className="estadisticas-filtradas">
                <div className="metrica-card">
                  <h4>Pedidos Filtrados</h4>
                  <p className="metrica-valor">{ventasFiltradas.estadisticas.total_pedidos}</p>
                </div>
                <div className="metrica-card">
                  <h4>Ventas Totales</h4>
                  <p className="metrica-valor">
                    ${ventasFiltradas.estadisticas.total_ventas.toLocaleString('es-CL')}
                  </p>
                </div>
                <div className="metrica-card">
                  <h4>Productos Vendidos</h4>
                  <p className="metrica-valor">{ventasFiltradas.estadisticas.total_productos}</p>
                </div>
                <div className="metrica-card">
                  <h4>Promedio por Pedido</h4>
                  <p className="metrica-valor">
                    ${ventasFiltradas.estadisticas.promedio_pedido.toLocaleString('es-CL')}
                  </p>
                </div>
              </div>

              {/* Ventas por Período */}
              <div className="ventas-periodo-section">
                <h3>Ventas por {filtros.agrupar_por === 'dia' ? 'Día' : filtros.agrupar_por === 'semana' ? 'Semana' : 'Mes'}</h3>
                <div className="ventas-periodo-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Período</th>
                        <th>Ventas Totales</th>
                        <th>Cantidad Pedidos</th>
                        <th>Promedio por Pedido</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ventasFiltradas.ventas_por_periodo.map((venta, index) => (
                        <tr key={index}>
                          <td>{new Date(venta.periodo).toLocaleDateString('es-CL')}</td>
                          <td>${venta.total_ventas.toLocaleString('es-CL')}</td>
                          <td>{venta.cantidad_pedidos}</td>
                          <td>${venta.promedio_pedido.toLocaleString('es-CL')}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Productos Más Vendidos */}
              {ventasFiltradas.productos_mas_vendidos.length > 0 && (
                <div className="productos-vendidos-section">
                  <h3>Productos Más Vendidos</h3>
                  <div className="productos-vendidos-table">
                    <table>
                      <thead>
                        <tr>
                          <th>Producto</th>
                          <th>Cantidad Vendida</th>
                          <th>Ventas Totales</th>
                          <th>Precio Promedio</th>
                        </tr>
                      </thead>
                      <tbody>
                        {ventasFiltradas.productos_mas_vendidos.map((producto, index) => (
                          <tr key={index}>
                            <td>{producto.producto_nombre}</td>
                            <td>{producto.cantidad_total}</td>
                            <td>${producto.ventas_total.toLocaleString('es-CL')}</td>
                            <td>${producto.precio_promedio.toLocaleString('es-CL')}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
