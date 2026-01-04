import React, { useState, useEffect, useRef } from 'react';
import { FaSearch, FaBarcode, FaPlus, FaMinus, FaTrash, FaCashRegister, FaMoneyBillWave, FaPrint, FaTimes } from 'react-icons/fa';
import { useRol } from '../contexts/RolContext';
import '../styles/globals.css';

function POS() {
  const { usuario } = useRol();
  const [busqueda, setBusqueda] = useState('');
  const [productos, setProductos] = useState([]);
  const [carrito, setCarrito] = useState([]);
  const [mostrarResultados, setMostrarResultados] = useState(false);
  const [loading, setLoading] = useState(false);
  const [metodoPago, setMetodoPago] = useState('efectivo');
  const [mostrarCierreCaja, setMostrarCierreCaja] = useState(false);
  const [cierreCaja, setCierreCaja] = useState(null);
  const busquedaRef = useRef(null);

  useEffect(() => {
    if (busqueda.length >= 2) {
      buscarProductos();
    } else {
      setProductos([]);
      setMostrarResultados(false);
    }
  }, [busqueda]);

  useEffect(() => {
    // Enfocar el input de búsqueda al cargar
    if (busquedaRef.current) {
      busquedaRef.current.focus();
    }
  }, []);

  const buscarProductos = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `http://localhost:8000/api/pos/buscar-producto/?q=${encodeURIComponent(busqueda)}&usuario_id=${usuario?.id}`,
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      const data = await response.json();

      if (response.ok && data.success) {
        setProductos(data.productos || []);
        setMostrarResultados(true);
      } else {
        setProductos([]);
      }
    } catch (error) {
      console.error('Error buscando productos:', error);
      setProductos([]);
    } finally {
      setLoading(false);
    }
  };

  const agregarAlCarrito = (producto) => {
    const itemExistente = carrito.find(item => item.id === producto.id);
    
    if (itemExistente) {
      // Si ya existe, aumentar cantidad
      setCarrito(carrito.map(item =>
        item.id === producto.id
          ? { ...item, cantidad: item.cantidad + 1 }
          : item
      ));
    } else {
      // Si no existe, agregar nuevo item
      setCarrito([...carrito, {
        ...producto,
        cantidad: 1
      }]);
    }
    
    // Limpiar búsqueda y resultados
    setBusqueda('');
    setProductos([]);
    setMostrarResultados(false);
    if (busquedaRef.current) {
      busquedaRef.current.focus();
    }
  };

  const actualizarCantidad = (productoId, nuevaCantidad) => {
    if (nuevaCantidad <= 0) {
      eliminarDelCarrito(productoId);
      return;
    }
    
    setCarrito(carrito.map(item =>
      item.id === productoId
        ? { ...item, cantidad: nuevaCantidad }
        : item
    ));
  };

  const eliminarDelCarrito = (productoId) => {
    setCarrito(carrito.filter(item => item.id !== productoId));
  };

  const calcularTotal = () => {
    return carrito.reduce((total, item) => {
      return total + (item.precio_con_descuento * item.cantidad);
    }, 0);
  };

  const procesarVenta = async () => {
    if (carrito.length === 0) {
      alert('Debe agregar al menos un producto');
      return;
    }

    if (!window.confirm(`¿Confirmar venta por $${calcularTotal().toFixed(2)}?`)) {
      return;
    }

    try {
      const items = carrito.map(item => ({
        producto_id: item.id,
        cantidad: item.cantidad
      }));

      const response = await fetch('http://localhost:8000/api/pos/crear-venta/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          items: items,
          metodo_pago: metodoPago,
          usuario_id: usuario?.id
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        alert(`Venta procesada exitosamente!\nBoleta: ${data.pedido.numero_boleta}\nTotal: $${data.pedido.total.toFixed(2)}`);
        setCarrito([]);
        setMetodoPago('efectivo');
        if (busquedaRef.current) {
          busquedaRef.current.focus();
        }
      } else {
        throw new Error(data.message || 'Error al procesar venta');
      }
    } catch (error) {
      console.error('Error procesando venta:', error);
      alert('Error al procesar la venta: ' + error.message);
    }
  };

  const cargarCierreCaja = async () => {
    try {
      const hoy = new Date().toISOString().split('T')[0];
      const response = await fetch(
        `http://localhost:8000/api/pos/cierre-caja/?fecha_inicio=${hoy}&fecha_fin=${hoy}&usuario_id=${usuario?.id}`,
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      const data = await response.json();

      if (response.ok && data.success) {
        setCierreCaja(data.cierre_caja);
        setMostrarCierreCaja(true);
      } else {
        throw new Error(data.message || 'Error al cargar cierre de caja');
      }
    } catch (error) {
      console.error('Error cargando cierre de caja:', error);
      alert('Error al cargar el cierre de caja: ' + error.message);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && productos.length > 0) {
      // Si hay resultados, agregar el primero
      agregarAlCarrito(productos[0]);
    }
  };

  if (usuario && usuario.rol !== 'vendedor' && usuario.rol !== 'gerente' && usuario.rol !== 'admin_sistema') {
    return (
      <div className="pos-container" style={{ padding: '20px', textAlign: 'center' }}>
        <h2>Acceso Denegado</h2>
        <p>Solo vendedores, gerentes y administradores pueden usar el POS.</p>
      </div>
    );
  }

  return (
    <div className="pos-container" style={{ 
      display: 'flex', 
      height: 'calc(100vh - 100px)',
      gap: '20px',
      padding: '20px',
      backgroundColor: '#f5f5f5'
    }}>
      {/* Panel izquierdo - Búsqueda y productos */}
      <div style={{ 
        flex: '1', 
        display: 'flex', 
        flexDirection: 'column',
        backgroundColor: '#fff',
        borderRadius: '8px',
        padding: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <div style={{ marginBottom: '20px' }}>
          <h2 style={{ margin: '0 0 15px 0' }}>Punto de Venta</h2>
          
          {/* Buscador */}
          <div style={{ position: 'relative', marginBottom: '10px' }}>
            <FaSearch style={{ 
              position: 'absolute', 
              left: '15px', 
              top: '50%', 
              transform: 'translateY(-50%)', 
              color: '#666' 
            }} />
            <input
              ref={busquedaRef}
              type="text"
              placeholder="Buscar producto por nombre o SKU (o escanear código de barras)..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              onKeyPress={handleKeyPress}
              style={{
                width: '100%',
                padding: '15px 15px 15px 45px',
                fontSize: '1.1rem',
                border: '2px solid #ddd',
                borderRadius: '8px',
                outline: 'none'
              }}
            />
            {busqueda && (
              <button
                onClick={() => {
                  setBusqueda('');
                  setProductos([]);
                  setMostrarResultados(false);
                  if (busquedaRef.current) {
                    busquedaRef.current.focus();
                  }
                }}
                style={{
                  position: 'absolute',
                  right: '10px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#666'
                }}
              >
                <FaTimes />
              </button>
            )}
          </div>

          {/* Resultados de búsqueda */}
          {mostrarResultados && productos.length > 0 && (
            <div style={{
              position: 'absolute',
              zIndex: 1000,
              backgroundColor: '#fff',
              border: '1px solid #ddd',
              borderRadius: '8px',
              boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
              maxHeight: '300px',
              overflowY: 'auto',
              width: 'calc(100% - 40px)',
              marginTop: '5px'
            }}>
              {productos.map((producto) => (
                <div
                  key={producto.id}
                  onClick={() => agregarAlCarrito(producto)}
                  style={{
                    padding: '12px 15px',
                    borderBottom: '1px solid #eee',
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseEnter={(e) => e.target.style.backgroundColor = '#f5f5f5'}
                  onMouseLeave={(e) => e.target.style.backgroundColor = '#fff'}
                >
                  <div>
                    <div style={{ fontWeight: 'bold' }}>{producto.nombre}</div>
                    <div style={{ fontSize: '0.9rem', color: '#666' }}>
                      SKU: {producto.sku} | Stock: {producto.stock}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: 'bold', color: 'var(--primary-color)' }}>
                      ${producto.precio_con_descuento.toFixed(2)}
                    </div>
                    {producto.tiene_promocion && (
                      <div style={{ fontSize: '0.8rem', color: '#4caf50' }}>
                        -{producto.descuento_porcentaje}%
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {loading && (
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <p>Buscando productos...</p>
            </div>
          )}
        </div>

        {/* Carrito */}
        <div style={{ flex: '1', overflowY: 'auto' }}>
          <h3 style={{ margin: '0 0 15px 0' }}>Carrito de Venta</h3>
          {carrito.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
              <FaBarcode style={{ fontSize: '3rem', marginBottom: '10px' }} />
              <p>El carrito está vacío</p>
              <p style={{ fontSize: '0.9rem' }}>Busque productos para agregarlos</p>
            </div>
          ) : (
            <div>
              {carrito.map((item) => (
                <div
                  key={item.id}
                  style={{
                    padding: '15px',
                    border: '1px solid #eee',
                    borderRadius: '8px',
                    marginBottom: '10px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <div style={{ flex: '1' }}>
                    <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>{item.nombre}</div>
                    <div style={{ fontSize: '0.9rem', color: '#666' }}>
                      SKU: {item.sku} | ${item.precio_con_descuento.toFixed(2)} c/u
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <button
                      onClick={() => actualizarCantidad(item.id, item.cantidad - 1)}
                      className="btn btn-sm btn-secondary"
                      style={{ padding: '5px 10px' }}
                    >
                      <FaMinus />
                    </button>
                    <span style={{ 
                      minWidth: '30px', 
                      textAlign: 'center',
                      fontWeight: 'bold',
                      fontSize: '1.1rem'
                    }}>
                      {item.cantidad}
                    </span>
                    <button
                      onClick={() => actualizarCantidad(item.id, item.cantidad + 1)}
                      className="btn btn-sm btn-secondary"
                      style={{ padding: '5px 10px' }}
                      disabled={item.cantidad >= item.stock}
                    >
                      <FaPlus />
                    </button>
                    <button
                      onClick={() => eliminarDelCarrito(item.id)}
                      className="btn btn-sm btn-danger"
                      style={{ padding: '5px 10px', marginLeft: '10px' }}
                    >
                      <FaTrash />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Panel derecho - Total y pago */}
      <div style={{ 
        width: '400px',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px'
      }}>
        {/* Total */}
        <div style={{
          backgroundColor: '#fff',
          borderRadius: '8px',
          padding: '30px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 20px 0', color: '#666' }}>Total</h3>
          <div style={{
            fontSize: '3rem',
            fontWeight: 'bold',
            color: 'var(--primary-color)',
            marginBottom: '20px'
          }}>
            ${calcularTotal().toFixed(2)}
          </div>
          <div style={{ color: '#666', fontSize: '0.9rem' }}>
            {carrito.length} {carrito.length === 1 ? 'producto' : 'productos'}
          </div>
        </div>

        {/* Métodos de pago */}
        <div style={{
          backgroundColor: '#fff',
          borderRadius: '8px',
          padding: '20px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ margin: '0 0 15px 0' }}>Método de Pago</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <button
              onClick={() => setMetodoPago('efectivo')}
              className={`btn ${metodoPago === 'efectivo' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '10px',
                justifyContent: 'center',
                padding: '15px'
              }}
            >
              <FaMoneyBillWave /> Efectivo
            </button>
            <button
              onClick={() => setMetodoPago('transferencia')}
              className={`btn ${metodoPago === 'transferencia' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '10px',
                justifyContent: 'center',
                padding: '15px'
              }}
            >
              <FaCashRegister /> Transferencia
            </button>
          </div>
        </div>

        {/* Botones de acción */}
        <div style={{
          backgroundColor: '#fff',
          borderRadius: '8px',
          padding: '20px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px'
        }}>
          <button
            onClick={procesarVenta}
            className="btn btn-success"
            style={{
              padding: '20px',
              fontSize: '1.2rem',
              fontWeight: 'bold',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px'
            }}
            disabled={carrito.length === 0}
          >
            <FaCashRegister /> Procesar Venta
          </button>
          <button
            onClick={cargarCierreCaja}
            className="btn btn-info"
            style={{
              padding: '15px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px'
            }}
          >
            <FaPrint /> Cierre de Caja
          </button>
        </div>
      </div>

      {/* Modal de Cierre de Caja */}
      {mostrarCierreCaja && cierreCaja && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2000
        }}>
          <div style={{
            backgroundColor: '#fff',
            borderRadius: '8px',
            padding: '30px',
            maxWidth: '800px',
            maxHeight: '90vh',
            overflowY: 'auto',
            width: '90%'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2>Cierre de Caja</h2>
              <button
                onClick={() => setMostrarCierreCaja(false)}
                className="btn btn-secondary"
                style={{ padding: '5px 10px' }}
              >
                <FaTimes />
              </button>
            </div>
            
            <div style={{ marginBottom: '20px' }}>
              <p><strong>Fecha:</strong> {new Date(cierreCaja.fecha_inicio).toLocaleDateString('es-CL')}</p>
              <p><strong>Vendedor:</strong> {cierreCaja.vendedor}</p>
            </div>

            <div style={{ 
              backgroundColor: '#f5f5f5', 
              padding: '20px', 
              borderRadius: '8px',
              marginBottom: '20px'
            }}>
              <h3>Estadísticas</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px' }}>
                <div>
                  <div style={{ fontSize: '0.9rem', color: '#666' }}>Total Ventas</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{cierreCaja.estadisticas.total_ventas}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.9rem', color: '#666' }}>Total Ingresos</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--primary-color)' }}>
                    ${cierreCaja.estadisticas.total_ingresos.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.9rem', color: '#666' }}>Promedio Venta</div>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
                    ${cierreCaja.estadisticas.promedio_venta.toFixed(2)}
                  </div>
                </div>
              </div>
            </div>

            {cierreCaja.por_metodo_pago && cierreCaja.por_metodo_pago.length > 0 && (
              <div style={{ marginBottom: '20px' }}>
                <h3>Por Método de Pago</h3>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#f5f5f5' }}>
                      <th style={{ padding: '10px', textAlign: 'left' }}>Método</th>
                      <th style={{ padding: '10px', textAlign: 'right' }}>Cantidad</th>
                      <th style={{ padding: '10px', textAlign: 'right' }}>Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cierreCaja.por_metodo_pago.map((item, index) => (
                      <tr key={index} style={{ borderBottom: '1px solid #eee' }}>
                        <td style={{ padding: '10px' }}>{item.metodo_pago}</td>
                        <td style={{ padding: '10px', textAlign: 'right' }}>{item.cantidad}</td>
                        <td style={{ padding: '10px', textAlign: 'right' }}>${parseFloat(item.total).toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {cierreCaja.ventas_del_dia && cierreCaja.ventas_del_dia.length > 0 && (
              <div>
                <h3>Ventas del Día</h3>
                <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ backgroundColor: '#f5f5f5' }}>
                        <th style={{ padding: '10px', textAlign: 'left' }}>Boleta</th>
                        <th style={{ padding: '10px', textAlign: 'left' }}>Hora</th>
                        <th style={{ padding: '10px', textAlign: 'right' }}>Total</th>
                        <th style={{ padding: '10px', textAlign: 'left' }}>Método</th>
                      </tr>
                    </thead>
                    <tbody>
                      {cierreCaja.ventas_del_dia.map((venta, index) => (
                        <tr key={index} style={{ borderBottom: '1px solid #eee' }}>
                          <td style={{ padding: '10px' }}>{venta.numero_boleta}</td>
                          <td style={{ padding: '10px' }}>
                            {new Date(venta.fecha).toLocaleTimeString('es-CL')}
                          </td>
                          <td style={{ padding: '10px', textAlign: 'right' }}>${venta.total.toFixed(2)}</td>
                          <td style={{ padding: '10px' }}>{venta.metodo_pago}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default POS;

