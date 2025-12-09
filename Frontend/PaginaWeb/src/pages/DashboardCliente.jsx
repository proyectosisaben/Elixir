import React, { useState, useEffect } from "react";
import { useRol } from "../contexts/RolContext";
import "../styles/globals.css";
import { FaShoppingBag, FaHeart, FaTruck, FaRedo, FaStar, FaUser } from "react-icons/fa";

function DashboardCliente() {
  const { usuario } = useRol();
  const [pedidos, setPedidos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [estadisticas, setEstadisticas] = useState({
    totalCompras: 0,
    gastado: 0,
    pedidosPendientes: 0,
  });

  useEffect(() => {
    cargarPedidos();
  }, []);

  const cargarPedidos = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/mis-pedidos/");
      if (response.ok) {
        const data = await response.json();
        setPedidos(data.pedidos || []);
        
        // Calcular estadísticas
        const totalCompras = data.pedidos?.length || 0;
        const gastado = data.pedidos?.reduce((sum, p) => sum + (parseFloat(p.total) || 0), 0) || 0;
        const pendientes = data.pedidos?.filter(p => !["entregado", "cancelado"].includes(p.estado)).length || 0;
        
        setEstadisticas({
          totalCompras,
          gastado,
          pedidosPendientes: pendientes,
        });
      }
    } catch (error) {
      console.error("Error cargando pedidos:", error);
    } finally {
      setLoading(false);
    }
  };

  const obtenerColorEstado = (estado) => {
    const colores = {
      pendiente: "warning",
      pagado: "info",
      en_preparacion: "primary",
      enviado: "secondary",
      entregado: "success",
      cancelado: "danger",
    };
    return colores[estado] || "secondary";
  };

  const obtenerIconoEstado = (estado) => {
    const iconos = {
      pendiente: "⏳",
      pagado: "✓",
      en_preparacion: "📦",
      enviado: "🚚",
      entregado: "✅",
      cancelado: "❌",
    };
    return iconos[estado] || "📋";
  };

  return (
    <div className="dashboard-cliente-container">
      {/* Header */}
      <div className="cliente-header">
        <div className="cliente-header-content">
          <div className="cliente-welcome">
            <FaUser className="header-icon" />
            <div>
              <h1>¡Bienvenido, {usuario?.nombre}!</h1>
              <p>Aquí puedes ver tus compras y recomendaciones personalizadas</p>
            </div>
          </div>
        </div>
      </div>

      <div className="cliente-main-container">
        {/* Tarjetas de Estadísticas */}
        <div className="estadisticas-grid">
          <div className="estadistica-card compras">
            <div className="card-icon">
              <FaShoppingBag />
            </div>
            <div className="card-content">
              <h3>Compras Totales</h3>
              <p className="card-value">{estadisticas.totalCompras}</p>
              <span className="card-label">Desde tu registro</span>
            </div>
          </div>

          <div className="estadistica-card gastado">
            <div className="card-icon">
              <span>$</span>
            </div>
            <div className="card-content">
              <h3>Total Gastado</h3>
              <p className="card-value">${estadisticas.gastado.toLocaleString('es-CL')}</p>
              <span className="card-label">En todas tus compras</span>
            </div>
          </div>

          <div className="estadistica-card pendiente">
            <div className="card-icon">
              <FaTruck />
            </div>
            <div className="card-content">
              <h3>Pendientes</h3>
              <p className="card-value">{estadisticas.pedidosPendientes}</p>
              <span className="card-label">En proceso o por enviar</span>
            </div>
          </div>
        </div>

        {/* Historial de Compras */}
        <div className="compras-section">
          <div className="section-header">
            <h2>
              <FaShoppingBag /> Mis Compras
            </h2>
            <button className="btn-actualizar" onClick={cargarPedidos}>
              <FaRedo /> Actualizar
            </button>
          </div>

          {loading ? (
            <div className="loading">
              <div className="spinner"></div>
              <p>Cargando tus compras...</p>
            </div>
          ) : pedidos.length === 0 ? (
            <div className="empty-state">
              <FaShoppingBag className="empty-icon" />
              <h3>No tienes compras aún</h3>
              <p>Comienza a explorar nuestro catálogo y realiza tu primera compra</p>
              <a href="/catalogo" className="btn-catalogo">
                Ver Catálogo
              </a>
            </div>
          ) : (
            <div className="compras-list">
              {pedidos.map((pedido) => (
                <div key={pedido.id} className="compra-item">
                  <div className="compra-header">
                    <div className="compra-info-basica">
                      <span className="compra-numero">Pedido #{pedido.id}</span>
                      <span className="compra-fecha">
                        {new Date(pedido.fecha_creacion).toLocaleDateString('es-CL')}
                      </span>
                    </div>
                    <span className={`estado-badge ${obtenerColorEstado(pedido.estado)}`}>
                      {obtenerIconoEstado(pedido.estado)} {pedido.estado.replace('_', ' ')}
                    </span>
                  </div>

                  <div className="compra-detalles">
                    <div className="detalle-item">
                      <span className="detalle-label">Total:</span>
                      <span className="detalle-valor">${parseFloat(pedido.total).toLocaleString('es-CL')}</span>
                    </div>
                    <div className="detalle-item">
                      <span className="detalle-label">Articulos:</span>
                      <span className="detalle-valor">{pedido.cantidad_items || 0}</span>
                    </div>
                    <div className="detalle-item">
                      <span className="detalle-label">Dirección:</span>
                      <span className="detalle-valor">{pedido.direccion || "No especificada"}</span>
                    </div>
                  </div>

                  <div className="compra-acciones">
                    <button className="btn-detalle">Ver Detalles</button>
                    {["enviado", "entregado"].includes(pedido.estado) && (
                      <button className="btn-calificar">
                        <FaStar /> Calificar Compra
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Sección de Recomendaciones */}
        <div className="recomendaciones-section">
          <div className="section-header">
            <h2>
              <FaHeart /> Para Ti
            </h2>
            <span className="section-subtitle">Basado en tus compras anteriores</span>
          </div>

          <div className="recomendaciones-placeholder">
            <FaHeart className="placeholder-icon" />
            <p>Los productos recomendados aparecerán aquí según tu historial de compras</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DashboardCliente;
