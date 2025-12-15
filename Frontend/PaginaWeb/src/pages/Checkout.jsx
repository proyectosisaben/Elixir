import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import '../styles/globals.css';
import { enviarEmailConfirmacionPedido } from '../services/emailService';

export default function Checkout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [usuario, setUsuario] = useState(null);
  const [carrito, setCarrito] = useState([]);
  const [loading, setLoading] = useState(false);
  const [procesando, setProcessando] = useState(false);
  const [message, setMessage] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [metodo_pago, setMetodo] = useState('transferencia');
  const [codigo_cupon, setCodigoCupon] = useState('');
  const [cuponValidado, setCuponValidado] = useState(null);
  const [validandoCupon, setValidandoCupon] = useState(false);
  const [errorCupon, setErrorCupon] = useState('');
  
  // Estados para dirección y envío
  const [direcciones, setDirecciones] = useState([]);
  const [cargandoDirecciones, setCargandoDirecciones] = useState(true);
  const [direccionSeleccionada, setDireccionSeleccionada] = useState(null);
  const [mostrarFormDireccion, setMostrarFormDireccion] = useState(false);
  const [nuevaDireccion, setNuevaDireccion] = useState({
    nombre: '',
    calle: '',
    numero: '',
    comuna: '',
    ciudad: '',
    region: '',
    codigo_postal: '',
    telefono: '',
    es_principal: false
  });
  const [metodosEnvio, setMetodosEnvio] = useState([]);
  const [metodoEnvioSeleccionado, setMetodoEnvioSeleccionado] = useState('estandar');
  const [costoEnvio, setCostoEnvio] = useState(0);
  const [calculandoEnvio, setCalculandoEnvio] = useState(false);
  const [regiones, setRegiones] = useState([]);
  const [comunasPorRegion, setComunasPorRegion] = useState({});

  useEffect(() => {
    const usuarioGuardado = localStorage.getItem('usuario');
    const carritoGuardado = localStorage.getItem('carrito');

    if (!usuarioGuardado) {
      navigate('/');
      return;
    }

    const usuarioParsed = JSON.parse(usuarioGuardado);
    
    // Solo clientes pueden hacer checkout
    if (usuarioParsed.rol !== 'cliente') {
      setErrorMsg('❌ Solo los clientes pueden realizar compras');
      return;
    }

    setUsuario(usuarioParsed);
    
    if (carritoGuardado) {
      try {
        setCarrito(JSON.parse(carritoGuardado));
      } catch (err) {
        setCarrito([]);
      }
    }

    cargarDirecciones();
    cargarMetodosEnvio();
    cargarRegionesComunas();
    setLoading(false);
  }, [navigate]);

  const cargarDirecciones = async () => {
    setCargandoDirecciones(true);
    try {
      // Obtener token del localStorage
      const token = localStorage.getItem('token');
      const headers = {
        'Content-Type': 'application/json'
      };
      
      // Agregar token al header si existe
      if (token) {
        headers['Authorization'] = `Token ${token}`;
      }
      
      // Agregar usuario_id como query param como fallback
      let url = `${window.API_BASE_URL}/api/direcciones/`;
      if (usuario?.id) {
        url += `?usuario_id=${usuario.id}`;
      }
      
      const response = await fetch(url, {
        headers: headers,
        credentials: 'include'
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Error desconocido' }));
        console.error('Error cargando direcciones:', response.status, errorData);
        setCargandoDirecciones(false);
        return;
      }
      
      const data = await response.json();
      if (data.success) {
        setDirecciones(data.direcciones || []);
        // Seleccionar dirección principal si existe
        const principal = data.direcciones?.find(d => d.es_principal);
        if (principal) {
          setDireccionSeleccionada(principal);
          calcularCostoEnvio(principal.region);
        }
      }
      setCargandoDirecciones(false);
    } catch (error) {
      console.error('Error cargando direcciones:', error);
      setErrorMsg('Error al cargar direcciones: ' + error.message);
      setCargandoDirecciones(false);
    }
  };

  const cargarMetodosEnvio = async () => {
    try {
      const response = await fetch(`${window.API_BASE_URL}/api/envio/metodos/`);
      const data = await response.json();
      if (data.success) {
        setMetodosEnvio(data.metodos || []);
      }
    } catch (error) {
      console.error('Error cargando métodos de envío:', error);
    }
  };

  const cargarRegionesComunas = async () => {
    try {
      const response = await fetch(`${window.API_BASE_URL}/api/direcciones/regiones-comunas/`);
      if (!response.ok) {
        console.error('Error en respuesta de regiones:', response.status);
        return;
      }
      const data = await response.json();
      console.log('Datos de regiones recibidos:', data);
      if (data.success) {
        setRegiones(data.regiones || []);
        setComunasPorRegion(data.comunas_por_region || {});
        console.log('Regiones cargadas:', data.regiones?.length || 0);
      } else {
        console.error('Error en respuesta de regiones:', data.message);
      }
    } catch (error) {
      console.error('Error cargando regiones:', error);
    }
  };

  const calcularCostoEnvio = async (region, metodo = metodoEnvioSeleccionado) => {
    if (!region) return;
    
    setCalculandoEnvio(true);
    try {
      const subtotal = calcularSubtotal();
      const response = await fetch(`${window.API_BASE_URL}/api/envio/calcular-costo/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          region: region,
          metodo_envio: metodo,
          monto_compra: subtotal
        })
      });
      const data = await response.json();
      if (data.success) {
        setCostoEnvio(data.costo_envio || 0);
      }
    } catch (error) {
      console.error('Error calculando costo de envío:', error);
      setCostoEnvio(0);
    } finally {
      setCalculandoEnvio(false);
    }
  };

  const handleSeleccionarDireccion = (direccion) => {
    setDireccionSeleccionada(direccion);
    calcularCostoEnvio(direccion.region, metodoEnvioSeleccionado);
  };

  const handleCambiarMetodoEnvio = (metodo) => {
    setMetodoEnvioSeleccionado(metodo);
    if (direccionSeleccionada) {
      calcularCostoEnvio(direccionSeleccionada.region, metodo);
    }
  };

  const handleCrearDireccion = async () => {
    setErrorMsg(''); // Limpiar errores anteriores
    try {
      // Validar campos requeridos
      if (!nuevaDireccion.nombre || !nuevaDireccion.calle || !nuevaDireccion.numero || 
          !nuevaDireccion.comuna || !nuevaDireccion.ciudad || !nuevaDireccion.region || 
          !nuevaDireccion.telefono) {
        setErrorMsg('Por favor completa todos los campos requeridos');
        return;
      }
      
      // Obtener token del localStorage
      const token = localStorage.getItem('token');
      const headers = {
        'Content-Type': 'application/json'
      };
      
      // Agregar token al header si existe
      if (token) {
        headers['Authorization'] = `Token ${token}`;
      }
      
      // Agregar usuario_id al body como fallback
      const bodyData = {
        ...nuevaDireccion,
        usuario_id: usuario?.id
      };
      
      console.log('Enviando dirección:', bodyData);
      
      const response = await fetch(`${window.API_BASE_URL}/api/direcciones/`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(bodyData),
        credentials: 'include'
      });
      
      console.log('Respuesta status:', response.status);
      
      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch (e) {
          errorData = { message: `Error ${response.status}: ${response.statusText}` };
        }
        console.error('Error en respuesta:', errorData);
        
        // Mostrar errores de validación si existen
        if (errorData.errors) {
          const errorMessages = Object.entries(errorData.errors).map(([field, messages]) => {
            if (Array.isArray(messages)) {
              return `${field}: ${messages.join(', ')}`;
            }
            return `${field}: ${messages}`;
          }).join('; ');
          throw new Error(errorMessages || errorData.message || `Error ${response.status}`);
        }
        
        throw new Error(errorData.message || errorData.error_detail || `Error ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Datos recibidos:', data);
      
      if (data.success) {
        await cargarDirecciones();
        setDireccionSeleccionada(data.direccion);
        setMostrarFormDireccion(false);
        setNuevaDireccion({
          nombre: '',
          calle: '',
          numero: '',
          comuna: '',
          ciudad: '',
          region: '',
          codigo_postal: '',
          telefono: '',
          es_principal: false
        });
        calcularCostoEnvio(data.direccion.region);
        setErrorMsg(''); // Limpiar errores anteriores
      } else {
        // Mostrar errores de validación si existen
        if (data.errors) {
          const errorMessages = Object.entries(data.errors).map(([field, messages]) => {
            if (Array.isArray(messages)) {
              return `${field}: ${messages.join(', ')}`;
            }
            return `${field}: ${messages}`;
          }).join('; ');
          setErrorMsg('Error al crear dirección: ' + errorMessages);
        } else {
          setErrorMsg('Error al crear dirección: ' + (data.message || 'Error desconocido'));
        }
      }
    } catch (error) {
      console.error('Error completo:', error);
      if (error.message === 'Failed to fetch') {
        setErrorMsg('Error de conexión: No se pudo conectar al servidor. Verifica que el backend esté corriendo.');
      } else {
        setErrorMsg('Error al crear dirección: ' + (error.message || 'Error de conexión'));
      }
    }
  };

  const calcularTotal = () => {
    const subtotal = carrito.reduce((total, item) => {
      const precio = item.precio_con_descuento || item.precio;
      return total + (precio * item.cantidad);
    }, 0);
    
    let total = subtotal;
    
    // Aplicar descuento del cupón si está validado
    if (cuponValidado && cuponValidado.descuento) {
      total = total - cuponValidado.descuento;
    }
    
    // Agregar costo de envío
    total = total + costoEnvio;
    
    return total;
  };

  const calcularSubtotal = () => {
    return carrito.reduce((total, item) => {
      const precio = item.precio_con_descuento || item.precio;
      return total + (precio * item.cantidad);
    }, 0);
  };

  const validarCupon = async () => {
    if (!codigo_cupon.trim()) {
      setErrorCupon('Por favor ingresa un código de cupón');
      return;
    }

    setValidandoCupon(true);
    setErrorCupon('');
    setCuponValidado(null);

    try {
      const subtotal = calcularSubtotal();
      const response = await fetch(`${window.API_BASE_URL}/api/cupones/validar/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          codigo: codigo_cupon.trim().toUpperCase(),
          monto_total: subtotal
        })
      });

      const data = await response.json();

      if (data.success && data.valido) {
        setCuponValidado({
          codigo: data.cupon.codigo,
          descuento: data.descuento,
          monto_original: data.monto_original,
          monto_final: data.monto_final,
          tipo: data.cupon.tipo_descuento,
          porcentaje: data.cupon.descuento_porcentaje,
          monto: data.cupon.descuento_monto
        });
        setErrorCupon('');
      } else {
        setErrorCupon(data.message || 'Cupón inválido');
        setCuponValidado(null);
      }
    } catch (err) {
      setErrorCupon('Error al validar cupón: ' + err.message);
      setCuponValidado(null);
    } finally {
      setValidandoCupon(false);
    }
  };

  const removerCupon = () => {
    setCodigoCupon('');
    setCuponValidado(null);
    setErrorCupon('');
  };

  const handleCrearPedido = async () => {
    if (carrito.length === 0) {
      setErrorMsg('⚠️ El carrito está vacío');
      return;
    }

    if (!direccionSeleccionada) {
      setErrorMsg('⚠️ Por favor selecciona una dirección de envío');
      return;
    }

    setProcessando(true);
    setErrorMsg('');
    setMessage('');

    try {
      const items = carrito.map(item => ({
        producto_id: item.id,
        cantidad: item.cantidad,
        precio: item.precio
      }));

      const response = await fetch(`${window.API_BASE_URL}/api/crear-pedido/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          usuario_id: usuario.id,
          items: items,
          metodo_pago: metodo_pago,
          codigo_cupon: cuponValidado ? cuponValidado.codigo : null,
          direccion_envio_id: direccionSeleccionada.id,
          metodo_envio: metodoEnvioSeleccionado,
          costo_envio: costoEnvio
        })
      });

      const data = await response.json();

      if (data.success) {
        setMessage(`✅ ¡Pedido creado exitosamente!\n\nNúmero de Pedido: ${data.numero_pedido}\nTotal: $${data.total.toFixed(2)}`);
        
        // Enviar email de confirmación al cliente
        try {
          const direccionCompleta = direccionSeleccionada 
            ? `${direccionSeleccionada.calle} ${direccionSeleccionada.numero}, ${direccionSeleccionada.comuna}, ${direccionSeleccionada.ciudad}, ${direccionSeleccionada.region_display || direccionSeleccionada.region}`
            : 'Por confirmar';
          
          await enviarEmailConfirmacionPedido({
            clienteEmail: usuario.email,
            clienteNombre: usuario.nombre || usuario.email.split('@')[0],
            numeroPedido: data.numero_pedido,
            items: carrito.map(item => ({
              nombre: item.nombre,
              cantidad: item.cantidad,
              precio_unitario: item.precio
            })),
            subtotal: subtotal,
            costoEnvio: costoEnvio,
            total: data.total,
            metodoPago: metodo_pago === 'transferencia' ? 'Transferencia Bancaria' : 'Tarjeta',
            direccion: direccionCompleta,
            fechaPedido: new Date()
          });
          console.log('✅ Email de confirmación enviado al cliente');
        } catch (emailError) {
          console.error('Error enviando email:', emailError);
          // No bloquear el flujo si falla el email
        }
        
        // Limpiar carrito
        localStorage.removeItem('carrito');
        setCarrito([]);

        // Redirigir a la página de confirmación de pago según el método elegido
        setTimeout(() => {
          const metodoPagoMap = {
            'transferencia': 'transferencia',
            'tarjeta': 'qr'
          };
          
          navigate('/confirmacion-pago-detalle', {
            state: {
              metodoPago: metodoPagoMap[metodo_pago],
              pedidoData: {
                numero_pedido: data.numero_pedido,
                total: data.total,
                detalles: carrito
              },
              usuario: usuario
            }
          });
        }, 2000);
      } else {
        setErrorMsg('❌ Error: ' + data.message);
      }
    } catch (err) {
      setErrorMsg('❌ Error al crear pedido: ' + err.message);
    } finally {
      setProcessando(false);
    }
  };

  const total = calcularTotal();
  const subtotal = calcularSubtotal();

  return (
    <div className="checkout-container">
      {/* Header */}
      <div className="checkout-header">
        <h1>🛒 Carrito de Compras</h1>
        <p>Completa tu compra de forma segura</p>
      </div>

      {errorMsg && <div className="alert alert-danger">{errorMsg}</div>}
      {message && (
        <div className="alert alert-success">
          {message.split('\n').map((line, idx) => (
            <div key={idx}>{line}</div>
          ))}
        </div>
      )}

      <div className="checkout-content">
        {/* Resumen del carrito */}
        <div className="carrito-section">
          <h2>📦 Resumen de tu Compra</h2>
          
          {carrito.length > 0 ? (
            <div className="carrito-items">
              <div className="items-table">
                <div className="table-header">
                  <div className="col-producto">Producto</div>
                  <div className="col-cantidad">Cantidad</div>
                  <div className="col-precio">Precio Unitario</div>
                  <div className="col-subtotal">Subtotal</div>
                </div>

                {carrito.map((item) => (
                  <div key={item.id} className="table-row">
                    <div className="col-producto">
                      <div className="producto-info">
                        {item.imagen && (
                          <img src={item.imagen} alt={item.nombre} className="producto-img" />
                        )}
                        <div>
                          <p className="producto-nombre">{item.nombre}</p>
                          <p className="producto-sku">SKU: {item.sku}</p>
                        </div>
                      </div>
                    </div>
                    <div className="col-cantidad">{item.cantidad}</div>
                    <div className="col-precio">${item.precio?.toFixed(2)}</div>
                    <div className="col-subtotal">${(item.precio * item.cantidad)?.toFixed(2)}</div>
                  </div>
                ))}
              </div>

              {/* Cupón de descuento */}
              <div className="cupon-section" style={{ marginTop: '20px', padding: '15px', border: '1px solid #ddd', borderRadius: '5px' }}>
                <h3 style={{ marginBottom: '10px', fontSize: '16px' }}>🎟️ Cupón de Descuento</h3>
                {!cuponValidado ? (
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                    <input
                      type="text"
                      placeholder="Ingresa tu código de cupón"
                      value={codigo_cupon}
                      onChange={(e) => setCodigoCupon(e.target.value.toUpperCase())}
                      style={{
                        flex: 1,
                        padding: '10px',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '14px'
                      }}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          validarCupon();
                        }
                      }}
                    />
                    <button
                      onClick={validarCupon}
                      disabled={validandoCupon || !codigo_cupon.trim()}
                      style={{
                        padding: '10px 20px',
                        backgroundColor: '#007bff',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: validandoCupon || !codigo_cupon.trim() ? 'not-allowed' : 'pointer',
                        opacity: validandoCupon || !codigo_cupon.trim() ? 0.6 : 1
                      }}
                    >
                      {validandoCupon ? 'Validando...' : 'Aplicar'}
                    </button>
                  </div>
                ) : (
                  <div style={{ 
                    padding: '10px', 
                    backgroundColor: '#d4edda', 
                    border: '1px solid #c3e6cb', 
                    borderRadius: '4px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <div>
                      <strong style={{ color: '#155724' }}>✅ Cupón aplicado: {cuponValidado.codigo}</strong>
                      <p style={{ margin: '5px 0 0 0', color: '#155724', fontSize: '14px' }}>
                        Descuento: ${cuponValidado.descuento.toFixed(2)}
                        {cuponValidado.porcentaje && ` (${cuponValidado.porcentaje}%)`}
                      </p>
                    </div>
                    <button
                      onClick={removerCupon}
                      style={{
                        padding: '5px 10px',
                        backgroundColor: '#dc3545',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                    >
                      Remover
                    </button>
                  </div>
                )}
                {errorCupon && (
                  <div style={{ 
                    marginTop: '10px', 
                    padding: '10px', 
                    backgroundColor: '#f8d7da', 
                    border: '1px solid #f5c6cb', 
                    borderRadius: '4px',
                    color: '#721c24',
                    fontSize: '14px'
                  }}>
                    {errorCupon}
                  </div>
                )}
              </div>

              {/* Totales */}
              <div className="carrito-totales">
                <div className="total-row">
                  <span>Subtotal:</span>
                  <span>${subtotal?.toFixed(2)}</span>
                </div>
                {cuponValidado && (
                  <div className="total-row" style={{ color: '#28a745', fontWeight: 'bold' }}>
                    <span>Descuento (Cupón {cuponValidado.codigo}):</span>
                    <span>-${cuponValidado.descuento?.toFixed(2)}</span>
                  </div>
                )}
                <div className="total-row">
                  <span>Costo de Envío:</span>
                  <span>
                    {calculandoEnvio ? 'Calculando...' : `$${costoEnvio.toFixed(2)}`}
                  </span>
                </div>
                <div className="total-row">
                  <span>Impuesto (0%):</span>
                  <span>$0.00</span>
                </div>
                <div className="total-row total-final">
                  <span>Total a Pagar:</span>
                  <span>${total?.toFixed(2)}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="empty-carrito">
              <p>🛒 Tu carrito está vacío</p>
              <button onClick={() => navigate('/')} className="btn btn-primary">
                👉 Ir a Comprar
              </button>
            </div>
          )}
        </div>

        {/* Información de pago y envío */}
        {carrito.length > 0 && (
          <div className="pago-section">
            <h2>📦 Dirección de Envío</h2>

            {/* Selección de dirección */}
            {direcciones.length > 0 && !mostrarFormDireccion && (
              <div className="direcciones-section" style={{ marginBottom: '20px' }}>
                <h3>📍 Direcciones Guardadas</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {direcciones.map((dir) => (
                    <div
                      key={dir.id}
                      onClick={() => handleSeleccionarDireccion(dir)}
                      style={{
                        padding: '15px',
                        border: direccionSeleccionada?.id === dir.id ? '2px solid #007bff' : '1px solid #ddd',
                        borderRadius: '5px',
                        cursor: 'pointer',
                        backgroundColor: direccionSeleccionada?.id === dir.id ? '#e7f3ff' : '#fff'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                        <div>
                          <strong>{dir.nombre} {dir.es_principal && '(Principal)'}</strong>
                          <p style={{ margin: '5px 0', fontSize: '14px', color: '#666' }}>
                            {dir.calle} {dir.numero}, {dir.comuna}, {dir.ciudad}, {dir.region_display}
                          </p>
                          <p style={{ margin: '5px 0', fontSize: '12px', color: '#999' }}>
                            Tel: {dir.telefono}
                          </p>
                        </div>
                        {direccionSeleccionada?.id === dir.id && (
                          <span style={{ color: '#007bff', fontSize: '20px' }}>✓</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                <button
                  onClick={() => setMostrarFormDireccion(true)}
                  style={{
                    marginTop: '10px',
                    padding: '10px 20px',
                    backgroundColor: '#28a745',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  + Agregar Nueva Dirección
                </button>
              </div>
            )}

            {/* Formulario de nueva dirección */}
            {mostrarFormDireccion && (
              <div className="nueva-direccion-form" style={{ marginBottom: '20px', padding: '20px', border: '1px solid #ddd', borderRadius: '5px' }}>
                <h3>➕ Nueva Dirección</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginTop: '15px' }}>
                  <div>
                    <label>Nombre (ej: Casa, Trabajo)</label>
                    <input
                      type="text"
                      value={nuevaDireccion.nombre}
                      onChange={(e) => setNuevaDireccion({...nuevaDireccion, nombre: e.target.value})}
                      style={{ width: '100%', padding: '8px', marginTop: '5px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                  <div>
                    <label>Teléfono</label>
                    <input
                      type="text"
                      value={nuevaDireccion.telefono}
                      onChange={(e) => setNuevaDireccion({...nuevaDireccion, telefono: e.target.value})}
                      style={{ width: '100%', padding: '8px', marginTop: '5px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                  <div>
                    <label>Calle</label>
                    <input
                      type="text"
                      value={nuevaDireccion.calle}
                      onChange={(e) => setNuevaDireccion({...nuevaDireccion, calle: e.target.value})}
                      style={{ width: '100%', padding: '8px', marginTop: '5px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                  <div>
                    <label>Número</label>
                    <input
                      type="text"
                      value={nuevaDireccion.numero}
                      onChange={(e) => setNuevaDireccion({...nuevaDireccion, numero: e.target.value})}
                      style={{ width: '100%', padding: '8px', marginTop: '5px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                  <div>
                    <label>Región</label>
                    <select
                      value={nuevaDireccion.region}
                      onChange={(e) => setNuevaDireccion({...nuevaDireccion, region: e.target.value, comuna: ''})}
                      style={{ width: '100%', padding: '8px', marginTop: '5px', border: '1px solid #ddd', borderRadius: '4px' }}
                    >
                      <option value="">Selecciona una región</option>
                      {regiones.map((r) => (
                        <option key={r.codigo} value={r.codigo}>{r.nombre}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label>Comuna</label>
                    <select
                      value={nuevaDireccion.comuna}
                      onChange={(e) => setNuevaDireccion({...nuevaDireccion, comuna: e.target.value})}
                      disabled={!nuevaDireccion.region}
                      style={{ width: '100%', padding: '8px', marginTop: '5px', border: '1px solid #ddd', borderRadius: '4px' }}
                    >
                      <option value="">Selecciona una comuna</option>
                      {nuevaDireccion.region && comunasPorRegion[nuevaDireccion.region]?.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label>Ciudad</label>
                    <input
                      type="text"
                      value={nuevaDireccion.ciudad}
                      onChange={(e) => setNuevaDireccion({...nuevaDireccion, ciudad: e.target.value})}
                      style={{ width: '100%', padding: '8px', marginTop: '5px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                  <div>
                    <label>Código Postal (opcional)</label>
                    <input
                      type="text"
                      value={nuevaDireccion.codigo_postal}
                      onChange={(e) => setNuevaDireccion({...nuevaDireccion, codigo_postal: e.target.value})}
                      style={{ width: '100%', padding: '8px', marginTop: '5px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                  </div>
                </div>
                <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
                  <button
                    onClick={handleCrearDireccion}
                    style={{
                      padding: '10px 20px',
                      backgroundColor: '#007bff',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Guardar Dirección
                  </button>
                  <button
                    onClick={() => {
                      setMostrarFormDireccion(false);
                      setNuevaDireccion({
                        nombre: '',
                        calle: '',
                        numero: '',
                        comuna: '',
                        ciudad: '',
                        region: '',
                        codigo_postal: '',
                        telefono: '',
                        es_principal: false
                      });
                    }}
                    style={{
                      padding: '10px 20px',
                      backgroundColor: '#6c757d',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            )}

            {/* Si no hay direcciones guardadas (solo mostrar cuando ya terminó de cargar) */}
            {!cargandoDirecciones && direcciones.length === 0 && !mostrarFormDireccion && (
              <div style={{ marginBottom: '20px' }}>
                <p>No tienes direcciones guardadas. Por favor agrega una:</p>
                <button
                  onClick={() => setMostrarFormDireccion(true)}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  + Agregar Dirección
                </button>
              </div>
            )}

            {/* Mostrar loading mientras carga */}
            {cargandoDirecciones && !mostrarFormDireccion && (
              <div style={{ marginBottom: '20px', textAlign: 'center', padding: '20px' }}>
                <p>Cargando direcciones...</p>
              </div>
            )}

            {/* Método de envío */}
            {direccionSeleccionada && (
              <div className="metodos-envio-section" style={{ marginTop: '20px', padding: '15px', border: '1px solid #ddd', borderRadius: '5px' }}>
                <h3>🚚 Método de Envío</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '10px' }}>
                  {metodosEnvio.map((metodo) => (
                    <label
                      key={metodo.codigo}
                      style={{
                        padding: '15px',
                        border: metodoEnvioSeleccionado === metodo.codigo ? '2px solid #007bff' : '1px solid #ddd',
                        borderRadius: '5px',
                        cursor: 'pointer',
                        backgroundColor: metodoEnvioSeleccionado === metodo.codigo ? '#e7f3ff' : '#fff',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <input
                          type="radio"
                          name="metodo_envio"
                          value={metodo.codigo}
                          checked={metodoEnvioSeleccionado === metodo.codigo}
                          onChange={() => handleCambiarMetodoEnvio(metodo.codigo)}
                        />
                        <div>
                          <strong>{metodo.nombre}</strong>
                          {calculandoEnvio && metodoEnvioSeleccionado === metodo.codigo && (
                            <p style={{ margin: '5px 0 0 0', fontSize: '12px', color: '#666' }}>Calculando costo...</p>
                          )}
                        </div>
                      </div>
                      {metodoEnvioSeleccionado === metodo.codigo && !calculandoEnvio && (
                        <div style={{ fontWeight: 'bold', color: '#007bff' }}>
                          {costoEnvio === 0 ? 'GRATIS' : `$${costoEnvio.toFixed(2)}`}
                        </div>
                      )}
                    </label>
                  ))}
                </div>
              </div>
            )}

            <h2 style={{ marginTop: '30px' }}>💳 Información de Pago</h2>

            {/* Información del cliente */}
            <div className="info-cliente">
              <h3>👤 Datos del Cliente</h3>
              <div className="info-fields">
                <div className="info-field">
                  <span className="label">Email</span>
                  <span className="value">{usuario?.email}</span>
                </div>
                <div className="info-field">
                  <span className="label">Nombre</span>
                  <span className="value">{usuario?.nombre || 'No registrado'}</span>
                </div>
              </div>
            </div>

            {/* Método de pago */}
            <div className="metodos-pago">
              <h3>Método de Pago</h3>
              <div className="pago-options">
                <label className="pago-option active">
                  <input
                    type="radio"
                    name="metodo_pago"
                    value="transferencia"
                    checked={metodo_pago === 'transferencia'}
                    onChange={(e) => setMetodo(e.target.value)}
                  />
                  <span className="option-content">
                    <span className="option-icon">🏦</span>
                    <span className="option-text">
                      <strong>Transferencia Bancaria</strong>
                      <small>Transferencia directa a nuestra cuenta bancaria</small>
                    </span>
                  </span>
                </label>
              </div>
            </div>

            {/* Información de método seleccionado */}
            {metodo_pago === 'transferencia' && (
              <div className="metodo-info">
                <div className="info-box success-info">
                  <h4>🏦 Transferencia Bancaria Seleccionada</h4>
                  <p>Se te mostrará una página con:</p>
                  <ul>
                    <li>Datos bancarios profesionales</li>
                    <li>Instrucciones paso a paso</li>
                    <li>Números copiables con un clic</li>
                    <li>Referencia del pedido</li>
                  </ul>
                  <p className="info-nota">
                    ℹ️ Después de confirmar, verás todos los detalles en la siguiente página.
                  </p>
                </div>
              </div>
            )}

            {/* Términos y condiciones */}
            <div className="terminos">
              <label className="terminos-checkbox">
                <input type="checkbox" required />
                <span>Acepto los términos y condiciones de la compra</span>
              </label>
              <label className="terminos-checkbox">
                <input type="checkbox" required />
                <span>He revisado que mi información sea correcta</span>
              </label>
            </div>

            {/* Botones de acción */}
            <div className="checkout-actions">
              <button
                onClick={handleCrearPedido}
                disabled={procesando || carrito.length === 0 || !direccionSeleccionada}
                className="btn btn-primary btn-lg"
              >
                {procesando ? '⏳ Procesando...' : '✅ Confirmar Compra'}
              </button>
              <button
                onClick={() => navigate('/')}
                className="btn btn-secondary"
              >
                🛍️ Seguir Comprando
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Información de seguridad */}
      <div className="seguridad-info">
        <div className="seguridad-item">
          <span className="seguridad-icon">🔒</span>
          <span className="seguridad-text">Compra 100% Segura</span>
        </div>
        <div className="seguridad-item">
          <span className="seguridad-icon">🚚</span>
          <span className="seguridad-text">Envío Rápido</span>
        </div>
        <div className="seguridad-item">
          <span className="seguridad-icon">💬</span>
          <span className="seguridad-text">Soporte 24/7</span>
        </div>
        <div className="seguridad-item">
          <span className="seguridad-icon">↩️</span>
          <span className="seguridad-text">Devoluciones Gratis</span>
        </div>
      </div>
    </div>
  );
}
