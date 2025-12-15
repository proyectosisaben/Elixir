import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useRol } from '../contexts/RolContext';
import { FaStar, FaTag } from 'react-icons/fa';

function ProductosRecomendados({ titulo = "Recomendado para ti", limite = 12, productoId = null, tipo = 'personalizado' }) {
  const { usuario } = useRol();
  const navigate = useNavigate();
  const [productos, setProductos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    cargarRecomendaciones();
  }, [usuario, productoId, tipo]);

  const cargarRecomendaciones = async () => {
    try {
      setLoading(true);
      setError(false);
      let url = '';
      
      if (productoId) {
        url = `${API_BASE_URL}/api/productos/${productoId}/relacionados/?limite=${limite}`;
        if (usuario && usuario.id) {
          url += `&usuario_id=${usuario.id}`;
        }
      } else {
        url = `${API_BASE_URL}/api/recomendaciones/?limite=${limite}&tipo=${tipo}`;
        if (usuario && usuario.id && tipo === 'personalizado') {
          url += `&usuario_id=${usuario.id}`;
        }
      }

      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Error en la respuesta');
      }

      const data = await response.json();

      if (data.success && Array.isArray(data.recomendaciones || data.productos)) {
        const productosData = productoId ? data.productos : data.recomendaciones;
        setProductos(productosData || []);
      } else {
        setProductos([]);
      }
    } catch (error) {
      console.error('Error cargando recomendaciones:', error);
      setError(true);
      setProductos([]);
    } finally {
      setLoading(false);
    }
  };

  const scrollLeft = () => {
    const container = document.getElementById('productos-recomendados-container');
    if (container) {
      container.scrollBy({ left: -300, behavior: 'smooth' });
    }
  };

  const scrollRight = () => {
    const container = document.getElementById('productos-recomendados-container');
    if (container) {
      container.scrollBy({ left: 300, behavior: 'smooth' });
    }
  };

  // Si hay error o no hay productos, no mostrar nada (evitar pantalla blanca)
  if (error || (!loading && (!productos || productos.length === 0))) {
    return null;
  }

  if (loading) {
    return (
      <section className="container py-5">
        <h2 className="fw-bold mb-4 text-primary">{titulo}</h2>
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Cargando recomendaciones...</span>
          </div>
        </div>
      </section>
    );
  }

  if (!Array.isArray(productos) || productos.length === 0) {
    return null;
  }

  return (
    <section className="container py-5">
      <div style={{ position: 'relative' }}>
        <h2 className="fw-bold mb-4 text-primary">{titulo}</h2>
        
        <div style={{ position: 'relative' }}>
          <button
            onClick={scrollLeft}
            className="btn btn-outline-primary"
            style={{
              position: 'absolute',
              left: '-50px',
              top: '50%',
              transform: 'translateY(-50%)',
              zIndex: 10,
              borderRadius: '50%',
              width: '40px',
              height: '40px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            ‹
          </button>
          
          <div
            id="productos-recomendados-container"
            style={{
              display: 'flex',
              overflowX: 'auto',
              gap: '20px',
              padding: '10px 0',
              scrollBehavior: 'smooth',
              scrollbarWidth: 'thin'
            }}
          >
            {productos.map((producto) => {
              if (!producto || !producto.id) {
                return null;
              }

              const precio = producto.precio || 0;
              const precioConDescuento = producto.precio_con_descuento || precio;
              const tienePromocion = producto.tiene_promocion || false;

              return (
                <div
                  key={producto.id}
                  onClick={() => navigate(`/producto/${producto.id}`)}
                  style={{
                    minWidth: '250px',
                    maxWidth: '250px',
                    cursor: 'pointer',
                    border: '1px solid #ddd',
                    borderRadius: '8px',
                    overflow: 'hidden',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    backgroundColor: '#fff'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-5px)';
                    e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  <div style={{ position: 'relative', height: '200px', overflow: 'hidden' }}>
                    {producto.imagen_url ? (
                      <img
                        src={producto.imagen_url}
                        alt={producto.nombre || 'Producto'}
                        style={{
                          width: '100%',
                          height: '100%',
                          objectFit: 'cover'
                        }}
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
                    ) : (
                      <div style={{
                        width: '100%',
                        height: '100%',
                        backgroundColor: '#f0f0f0',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#999'
                      }}>
                        <i className="fas fa-image fa-3x"></i>
                      </div>
                    )}
                    {tienePromocion && (
                      <div style={{
                        position: 'absolute',
                        top: '10px',
                        right: '10px',
                        backgroundColor: '#4caf50',
                        color: '#fff',
                        padding: '5px 10px',
                        borderRadius: '4px',
                        fontSize: '0.85rem',
                        fontWeight: 'bold',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '5px'
                      }}>
                        <FaTag /> OFERTA
                      </div>
                    )}
                  </div>
                  <div style={{ padding: '15px' }}>
                    <h5 style={{
                      margin: '0 0 10px 0',
                      fontSize: '1rem',
                      fontWeight: 'bold',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {producto.nombre || 'Sin nombre'}
                    </h5>
                    <div style={{ marginBottom: '10px', fontSize: '0.9rem', color: '#666' }}>
                      {producto.categoria_nombre || producto.categoria?.nombre || 'Sin categoría'}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        {tienePromocion ? (
                          <>
                            <div style={{ fontSize: '0.85rem', color: '#999', textDecoration: 'line-through' }}>
                              ${precio.toFixed(2)}
                            </div>
                            <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--primary-color)' }}>
                              ${precioConDescuento.toFixed(2)}
                            </div>
                          </>
                        ) : (
                          <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--primary-color)' }}>
                            ${precio.toFixed(2)}
                          </div>
                        )}
                      </div>
                      {producto.razon_recomendacion && (
                        <div style={{
                          fontSize: '0.75rem',
                          color: '#666',
                          backgroundColor: '#f0f0f0',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          maxWidth: '100px',
                          textAlign: 'center'
                        }} title={producto.razon_recomendacion}>
                          <FaStar style={{ color: '#ffc107' }} />
                        </div>
                      )}
                    </div>
                    {producto.stock !== undefined && producto.stock <= (producto.stock_minimo || 0) && producto.stock > 0 && (
                      <div style={{
                        marginTop: '10px',
                        fontSize: '0.85rem',
                        color: '#ff9800',
                        fontWeight: 'bold'
                      }}>
                        ¡Últimas unidades!
                      </div>
                    )}
                    {producto.stock !== undefined && producto.stock === 0 && (
                      <div style={{
                        marginTop: '10px',
                        fontSize: '0.85rem',
                        color: '#f44336',
                        fontWeight: 'bold'
                      }}>
                        Sin stock
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          
          <button
            onClick={scrollRight}
            className="btn btn-outline-primary"
            style={{
              position: 'absolute',
              right: '-50px',
              top: '50%',
              transform: 'translateY(-50%)',
              zIndex: 10,
              borderRadius: '50%',
              width: '40px',
              height: '40px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            ›
          </button>
        </div>
      </div>
    </section>
  );
}

export default ProductosRecomendados;
