import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import "../styles/globals.css";

function Carrito() {
  const [items, setItems] = useState(() => {
    const saved = localStorage.getItem('carrito');
    return saved ? JSON.parse(saved) : [];
  });
  const navigate = useNavigate();

  useEffect(() => {
    localStorage.setItem('carrito', JSON.stringify(items));
  }, [items]);

  const actualizarCantidad = (productoId, nuevaCantidad) => {
    if (nuevaCantidad < 1) {
      eliminarProducto(productoId);
      return;
    }
    
    setItems(items.map(item =>
      item.id === productoId ? { ...item, cantidad: nuevaCantidad } : item
    ));
  };

  const eliminarProducto = (productoId) => {
    setItems(items.filter(item => item.id !== productoId));
  };

  const calcularSubtotal = (producto) => {
    return parseFloat(producto.precio) * producto.cantidad;
  };

  const calcularTotal = () => {
    return items.reduce((sum, item) => sum + calcularSubtotal(item), 0);
  };

  const procesarPago = () => {
    const usuario = localStorage.getItem('usuario');
    if (!usuario) {
      navigate('/login');
      return;
    }
    
    if (items.length === 0) {
      alert('Tu carrito está vacío');
      return;
    }

    // Redirigir a la página de checkout con los datos del carrito
    navigate('/checkout', { state: { items, total: calcularTotal() * 1.19 } });
  };

  if (items.length === 0) {
    return (
      <div className="container py-5">
        <div className="text-center">
          <i className="fas fa-shopping-cart" style={{ fontSize: '4rem', color: 'var(--border-color)', marginBottom: '20px' }}></i>
          <h2>Tu carrito está vacío</h2>
          <p className="text-muted">Agrega productos a tu carrito para continuar</p>
          <button
            className="btn btn-primary mt-3"
            onClick={() => navigate('/')}
          >
            Continuar comprando
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container py-5">
      <h1 className="fw-bold mb-4 text-primary">
        <i className="fas fa-shopping-cart"></i> Tu Carrito ({items.length} productos)
      </h1>

      <div className="row">
        <div className="col-lg-8">
          <div className="card shadow-sm mb-4">
            <div className="card-body p-0">
              <table className="table table-hover mb-0">
                <thead className="table-light">
                  <tr>
                    <th>Producto</th>
                    <th>Precio</th>
                    <th>Cantidad</th>
                    <th>Subtotal</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {items.map(item => (
                    <tr key={item.id} className="align-middle">
                      <td>
                        <div className="d-flex align-items-center gap-3">
                          <img
                            src={item.imagen_url || item.imagen}
                            alt={item.nombre}
                            style={{ width: '80px', height: '80px', objectFit: 'cover', borderRadius: '8px' }}
                          />
                          <div>
                            <h6 className="mb-1">{item.nombre}</h6>
                            <small className="text-muted">{item.categoria?.nombre}</small>
                          </div>
                        </div>
                      </td>
                      <td className="fw-bold">
                        ${parseFloat(item.precio).toLocaleString('es-CL')}
                      </td>
                      <td>
                        <div className="input-group" style={{ maxWidth: '100px' }}>
                          <button
                            className="btn btn-outline-secondary btn-sm"
                            onClick={() => actualizarCantidad(item.id, item.cantidad - 1)}
                          >
                            −
                          </button>
                          <input
                            type="number"
                            className="form-control form-control-sm text-center"
                            value={item.cantidad}
                            onChange={(e) => actualizarCantidad(item.id, parseInt(e.target.value) || 1)}
                            min="1"
                          />
                          <button
                            className="btn btn-outline-secondary btn-sm"
                            onClick={() => actualizarCantidad(item.id, item.cantidad + 1)}
                          >
                            +
                          </button>
                        </div>
                      </td>
                      <td className="fw-bold text-primary">
                        ${calcularSubtotal(item).toLocaleString('es-CL')}
                      </td>
                      <td>
                        <button
                          className="btn btn-sm btn-outline-danger"
                          onClick={() => eliminarProducto(item.id)}
                        >
                          <i className="fas fa-trash"></i>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <button
            className="btn btn-outline-primary"
            onClick={() => navigate('/')}
          >
            <i className="fas fa-arrow-left"></i> Continuar comprando
          </button>
        </div>

        <div className="col-lg-4">
          <div className="card shadow-sm sticky-top" style={{ top: '20px' }}>
            <div className="card-body">
              <h5 className="card-title mb-4">Resumen de Pedido</h5>

              <div className="d-flex justify-content-between mb-3 pb-3 border-bottom">
                <span>Subtotal:</span>
                <span>${calcularTotal().toLocaleString('es-CL', { minimumFractionDigits: 2 })}</span>
              </div>

              <div className="d-flex justify-content-between mb-3 pb-3 border-bottom">
                <span>Envío:</span>
                <span className="text-success">Gratis (por compra mayor a $50.000)</span>
              </div>

              <div className="d-flex justify-content-between mb-4">
                <span className="fw-bold">IVA (19%):</span>
                <span className="fw-bold">
                  ${(calcularTotal() * 0.19).toLocaleString('es-CL', { minimumFractionDigits: 2 })}
                </span>
              </div>

              <div className="bg-light p-3 rounded mb-4">
                <div className="d-flex justify-content-between align-items-center">
                  <span className="fs-5 fw-bold">Total:</span>
                  <span className="fs-4 fw-bold text-primary">
                    ${(calcularTotal() * 1.19).toLocaleString('es-CL', { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>

              <button
                className="btn btn-primary w-100 btn-lg mb-2"
                onClick={procesarPago}
              >
                <i className="fas fa-credit-card"></i> Proceder al Pago
              </button>

              <small className="text-muted d-block text-center">
                Se aplicará IVA al total
              </small>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Carrito;
