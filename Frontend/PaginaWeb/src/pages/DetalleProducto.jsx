import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import ProductosRecomendados from "../components/ProductosRecomendados";
import "../styles/globals.css";

function DetalleProducto() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [producto, setProducto] = useState(null);
  const [cantidad, setCantidad] = useState(1);
  const [cargando, setCargando] = useState(true);
  const [imagenPrincipal, setImagenPrincipal] = useState("");
  const [carrito, setCarrito] = useState(() => {
    const saved = localStorage.getItem('carrito');
    return saved ? JSON.parse(saved) : [];
  });

useEffect(() => {
  const cargarProducto = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/producto/${id}/`);
      if (!response.ok) throw new Error("Producto no encontrado");
      const data = await response.json();

      const prod = data.producto || data;

      // log para ver qué trae
      console.log("Detalle producto API:", prod);

      setProducto(prod);

      const imagenUrl =
        prod.imagen_url ||    // si tu API manda imagen_url absoluta (como usa el carrito)
        prod.imagen ||        // si manda /media/...
        "https://via.placeholder.com/500x500?text=Sin+imagen";

      setImagenPrincipal(imagenUrl);
      setCargando(false);
    } catch (error) {
      console.error("Error cargando producto:", error);
      setCargando(false);
    }
  };

  cargarProducto();
}, [id]);


  const agregarAlCarrito = () => {
    const existente = carrito.find(p => p.id === producto.id);
    let nuevoCarrito;
    
    if (existente) {
      nuevoCarrito = carrito.map(p => 
        p.id === producto.id ? {...p, cantidad: p.cantidad + cantidad} : p
      );
    } else {
      nuevoCarrito = [...carrito, {
        id: producto.id,
        nombre: producto.nombre,
        precio: producto.precio,
        imagen: imagenPrincipal,
        imagen_url: producto.imagen_url,
        cantidad: cantidad
      }];
    }
    
    setCarrito(nuevoCarrito);
    localStorage.setItem('carrito', JSON.stringify(nuevoCarrito));
    
    // Mostrar notificación
    alert(`¡${cantidad} ${producto.nombre}(s) agregado(s) al carrito!`);
    setCantidad(1);
  };

  if (cargando) {
    return (
      <div className="container mt-5 text-center">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Cargando...</span>
        </div>
        <p className="mt-3">Cargando producto...</p>
      </div>
    );
  }

  if (!producto) {
    return (
      <div className="container mt-5 text-center">
        <h2>Producto no encontrado</h2>
        <p className="text-muted">Lo sentimos, el producto que buscas no existe.</p>
        <button className="btn btn-primary mt-3" onClick={() => navigate("/catalogo")}>
          Volver al catálogo
        </button>
      </div>
    );
  }

  return (
    <div className="container mt-4 mb-5">
      {/* Breadcrumb */}
      <nav aria-label="breadcrumb">
        <ol className="breadcrumb">
          <li className="breadcrumb-item"><a href="/" onClick={() => navigate("/")}>Inicio</a></li>
          <li className="breadcrumb-item"><a href="/catalogo" onClick={() => navigate("/catalogo")}>Catálogo</a></li>
          <li className="breadcrumb-item active">{producto.nombre}</li>
        </ol>
      </nav>

      <div className="row">
        {/* Columna de imagen */}
        <div className="col-lg-6 mb-4">
          <div className="sticky-top detalle-imagen" style={{ top: "100px" }}>
            <div className="card shadow-lg border-0">
              <div className="position-relative imagen-container">
                <img 
                  src={imagenPrincipal} 
                  alt={producto.nombre}
                  className="card-img-top imagen-principal"
                  style={{ height: "500px", objectFit: "cover", cursor: "zoom-in" }}
                />
                
                {/* Badges */}
                {producto.stock <= 5 && producto.stock > 0 && (
                  <span className="badge bg-warning text-dark position-absolute top-0 start-0 m-3">
                    <i className="fas fa-exclamation-triangle"></i> ¡Últimas {producto.stock}!
                  </span>
                )}
                
                {producto.stock === 0 && (
                  <span className="badge bg-danger position-absolute top-0 start-0 m-3">
                    <i className="fas fa-times-circle"></i> Agotado
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Columna de detalles */}
        <div className="col-lg-6">
          {/* Categoría y SKU */}
          <div className="mb-3">
            <span className="badge bg-primary fs-6">
              <i className="fas fa-tag"></i> {producto.categoria?.nombre || "Sin categoría"}
            </span>
            <span className="badge bg-secondary ms-2">SKU: {producto.sku || "N/A"}</span>
          </div>

          {/* Título */}
          <h1 className="display-6 fw-bold text-primary mb-3">
            {producto.nombre}
          </h1>

          {/* Rating simulado */}
          <div className="mb-3">
            <div className="d-flex align-items-center">
              <div className="text-warning me-2">
                <i className="fas fa-star"></i>
                <i className="fas fa-star"></i>
                <i className="fas fa-star"></i>
                <i className="fas fa-star"></i>
                <i className="fas fa-star-half-alt"></i>
              </div>
              <span className="text-muted">(4.8) · 127 reseñas</span>
            </div>
          </div>

          {/* Precio */}
          <div className="mb-4">
            <div className="d-flex align-items-center mb-3">
              <h2 className="display-5 text-primary fw-bold me-3">
                ${Number(producto.precio).toLocaleString('es-CL')}
              </h2>
            </div>
            <div className="d-flex flex-wrap gap-2 text-muted small">
              <span><i className="fas fa-check-circle text-success"></i> Precio incluye IVA</span>
              <span><i className="fas fa-truck text-info"></i> Envío gratis sobre $25.000</span>
              <span><i className="fas fa-shield-alt text-primary"></i> Compra protegida</span>
            </div>
          </div>

          {/* Descripción */}
          {producto.descripcion && (
            <div className="mb-4">
              <h5><i className="fas fa-info-circle text-primary"></i> Descripción</h5>
              <p className="lead">{producto.descripcion}</p>
            </div>
          )}

          {/* Disponibilidad y Entrega */}
          <div className="row mb-4">
            <div className="col-md-6">
              <div className="card bg-light border-0">
                <div className="card-body">
                  <h6><i className="fas fa-warehouse text-primary"></i> Disponibilidad</h6>
                  <div className="d-flex align-items-center">
                    {producto.stock > 10 ? (
                      <>
                        <span className="badge bg-success me-2">
                          <i className="fas fa-check-circle"></i> En Stock
                        </span>
                        <span className="fw-bold">{producto.stock} unidades disponibles</span>
                      </>
                    ) : producto.stock > 0 ? (
                      <>
                        <span className="badge bg-warning me-2">
                          <i className="fas fa-exclamation-triangle"></i> Pocas unidades
                        </span>
                        <span className="fw-bold text-warning">Solo quedan {producto.stock}</span>
                      </>
                    ) : (
                      <>
                        <span className="badge bg-danger me-2">
                          <i className="fas fa-times-circle"></i> Agotado
                        </span>
                        <span className="text-danger fw-bold">Sin stock</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="col-md-6">
              <div className="card bg-light border-0">
                <div className="card-body">
                  <h6><i className="fas fa-truck text-info"></i> Entrega</h6>
                  <div className="small">
                    <p className="mb-1">
                      <i className="fas fa-clock text-success"></i> 
                      <strong> Santiago:</strong> Entrega hoy si pidas antes de las 15:00
                    </p>
                    <p className="mb-0">
                      <i className="fas fa-map-marker-alt text-info"></i> 
                      <strong> Regiones:</strong> 24-48 horas hábiles
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Compra */}
          {producto.stock > 0 ? (
            <div className="mb-4">
              <div className="row g-3">
                <div className="col-md-4">
                  <label htmlFor="cantidadProducto" className="form-label fw-bold">
                    Cantidad:
                  </label>
                  <div className="input-group">
                    <button 
                      className="btn btn-outline-secondary"
                      onClick={() => setCantidad(Math.max(1, cantidad - 1))}
                      disabled={cantidad === 1}
                    >
                      −
                    </button>
                    <input 
                      type="number" 
                      className="form-control text-center fw-bold"
                      id="cantidadProducto"
                      value={cantidad}
                      onChange={(e) => setCantidad(Math.min(producto.stock, Math.max(1, parseInt(e.target.value) || 1)))}
                      max={producto.stock}
                      min="1"
                    />
                    <button 
                      className="btn btn-outline-secondary"
                      onClick={() => setCantidad(Math.min(producto.stock, cantidad + 1))}
                      disabled={cantidad === producto.stock}
                    >
                      +
                    </button>
                  </div>
                  <small className="text-muted">Máximo {producto.stock} unidades</small>
                </div>
                <div className="col-md-8 d-flex align-items-end">
                  <button 
                    className="btn btn-primary btn-lg w-100"
                    onClick={agregarAlCarrito}
                  >
                    <i className="fas fa-cart-plus"></i> Agregar al Carrito - ${(producto.precio * cantidad).toLocaleString('es-CL')}
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="alert alert-danger border-0 shadow-sm">
              <div className="d-flex align-items-center">
                <i className="fas fa-exclamation-triangle fa-2x me-3"></i>
                <div>
                  <h6 className="mb-1">Producto Agotado</h6>
                  <p className="mb-0">¿Quieres que te notifiquemos cuando esté disponible?</p>
                </div>
              </div>
              <div className="mt-3">
                <button className="btn btn-warning">
                  <i className="fas fa-bell"></i> Notificarme cuando esté disponible
                </button>
              </div>
            </div>
          )}

          {/* Garantías */}
          <div className="card bg-primary text-white border-0 shadow">
            <div className="card-body">
              <h6><i className="fas fa-shield-alt"></i> Garantías y Beneficios Elixir</h6>
              <div className="row">
                <div className="col-md-6">
                  <ul className="list-unstyled mb-0 small">
                    <li><i className="fas fa-check text-warning"></i> Productos 100% originales</li>
                    <li><i className="fas fa-check text-warning"></i> Garantía de satisfacción</li>
                  </ul>
                </div>
                <div className="col-md-6">
                  <ul className="list-unstyled mb-0 small">
                    <li><i className="fas fa-check text-warning"></i> Atención personalizada</li>
                    <li><i className="fas fa-check text-warning"></i> Devolución sin costo</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Proveedor */}
          <div className="mt-3">
            <small className="text-muted">
              <i className="fas fa-store"></i> Vendido y despachado por: 
              <strong> {producto.proveedor?.nombre || "Elixir Store"}</strong>
            </small>
          </div>
        </div>
      </div>

      {/* Productos Relacionados */}
      <div style={{ marginTop: '60px' }}>
        <ProductosRecomendados 
          titulo="🛍️ Productos Relacionados" 
          limite={6}
          productoId={id}
        />
      </div>
    </div>
  );
}

export default DetalleProducto;
