import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchProductos } from '../api';
import { useRol } from '../contexts/RolContext';
import BuscadorAvanzado from '../components/BuscadorAvanzado';
import { construirParametrosQueryFiltros } from '../utils/filtrosUtils';
import "../styles/globals.css";

function CatalogoPorCategoria() {
  const [productos, setProductos] = useState([]);
  const [categorias, setCategorias] = useState([]);
  const [proveedores, setProveedores] = useState([]);
  const [categoriaSeleccionada, setCategoriaSeleccionada] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  const { usuario } = useRol();
  const [carrito, setCarrito] = useState(() => {
    const saved = localStorage.getItem('carrito');
    return saved ? JSON.parse(saved) : [];
  });
  
  // Estados para filtros avanzados
  const [filtrosAplicados, setFiltrosAplicados] = useState({
    busqueda: '',
    categorias: [],
    proveedor: null,
    precioMin: null,
    precioMax: null,
    disponible: null,
  });
  const [productosFiltrados, setProductosFiltrados] = useState([]);
  const [mostrarFiltrosMobile, setMostrarFiltrosMobile] = useState(false);
  const [rangoPrecios, setRangoPrecios] = useState({ minimo: 0, maximo: 1000000 });
  
  const [categoriasList, setCategoriasList] = useState([
    { id: 1, nombre: 'Vinos' },
    { id: 2, nombre: 'Cervezas' },
    { id: 3, nombre: 'Piscos' },
    { id: 4, nombre: 'Whiskys' },
    { id: 5, nombre: 'Ron' }
  ]);
  const [editando, setEditando] = useState(false);
  const [productoEditado, setProductoEditado] = useState(null);
  const [formData, setFormData] = useState({});
  const [creando, setCreando] = useState(false);
  const [formDataNuevo, setFormDataNuevo] = useState({
    nombre: "",
    descripcion: "",
    precio: 0,
    costo: 0,
    stock: 0,
    stock_minimo: 5,
    imagen_url: "",
    categoria_id: 1
  });

  useEffect(() => {
    const obtenerProductos = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${window.API_BASE_URL}/api/catalogo/`);
        const data = await response.json();
        
        setProductos(data.productos || []);
        setCategorias(data.categorias || []);
        setProveedores(data.proveedores || []);
        setProductosFiltrados(data.productos || []);
        
        // Calcular rango de precios
        if (data.rango_precios) {
          setRangoPrecios(data.rango_precios);
        }
        
        // Seleccionar la primera categoría por defecto
        if (data.categorias?.length > 0) {
          setCategoriaSeleccionada(data.categorias[0].id);
        }
        
        setError(null);
      } catch (err) {
        console.error('Error al obtener productos:', err);
        setError('No se pudieron cargar los productos');
      } finally {
        setLoading(false);
      }
    };

    obtenerProductos();
  }, []);

  const handleFiltrosChange = async (filtros) => {
    setFiltrosAplicados(filtros);
    setMostrarFiltrosMobile(false);

    try {
      const queryParams = construirParametrosQueryFiltros(filtros);
      const url = `${window.API_BASE_URL}/api/catalogo/?${queryParams}`;
      
      const response = await fetch(url);
      const data = await response.json();
      
      setProductosFiltrados(data.productos || []);
    } catch (error) {
      console.error('Error al filtrar productos:', error);
      setProductosFiltrados([]);
    }
  };

  const agregarAlCarrito = (producto) => {
    const productoExistente = carrito.find(p => p.id === producto.id);
    
    let nuevoCarrito;
    if (productoExistente) {
      nuevoCarrito = carrito.map(p =>
        p.id === producto.id ? { ...p, cantidad: p.cantidad + 1 } : p
      );
    } else {
      nuevoCarrito = [...carrito, { ...producto, cantidad: 1 }];
    }
    
    setCarrito(nuevoCarrito);
    localStorage.setItem('carrito', JSON.stringify(nuevoCarrito));
    alert(`${producto.nombre} agregado al carrito`);
  };

  const handleCrearProducto = async () => {
    if (!formDataNuevo.nombre || !formDataNuevo.precio) {
      alert('Completa los campos obligatorios (nombre, precio, stock)');
      return;
    }

    try {
      const usuarioJson = localStorage.getItem('usuario');
      const usuario = usuarioJson ? JSON.parse(usuarioJson) : null;

      const datosNuevoProducto = {
        nombre: formDataNuevo.nombre,
        descripcion: formDataNuevo.descripcion,
        precio: formDataNuevo.precio,
        costo: formDataNuevo.costo || 0,
        stock: formDataNuevo.stock,
        stock_minimo: formDataNuevo.stock_minimo || 5,
        imagen_url: formDataNuevo.imagen_url,
        usuario_id: usuario?.id,
        categoria_id: formDataNuevo.categoria_id || 1,
        proveedor_id: formDataNuevo.proveedor_id || 1,
        sku: formDataNuevo.nombre.replace(/\s+/g, '_').toUpperCase()
      };

      const response = await fetch(`${window.API_BASE_URL}/api/admin/catalogo/productos/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(datosNuevoProducto)
      });

      const data = await response.json();
      if (data.success) {
        setProductos([...productos, data.producto]);
        setCreando(false);
        setFormDataNuevo({
          nombre: "",
          descripcion: "",
          precio: 0,
          costo: 0,
          stock: 0,
          stock_minimo: 5,
          imagen_url: ""
        });
        alert('Producto creado correctamente');
        window.location.reload();
      } else {
        alert(`Error: ${data.message || 'No se pudo crear el producto'}`);
      }
    } catch (error) {
      console.error('Error al crear producto:', error);
      alert('Error: ' + error.message);
    }
  };

  const handleEliminarProducto = async (productoId) => {
    if (!window.confirm('¿Estás seguro de que deseas eliminar este producto?')) {
      return;
    }

    try {
      const usuarioJson = localStorage.getItem('usuario');
      const usuario = usuarioJson ? JSON.parse(usuarioJson) : null;

      const response = await fetch(`${API_BASE_URL}/api/admin/catalogo/productos/${productoId}/`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          usuario_id: usuario?.id
        })
      });

      const data = await response.json();
      if (data.success) {
        setProductos(productos.filter(p => p.id !== productoId));
        alert('Producto eliminado correctamente');
      } else {
        alert(`Error: ${data.message || 'No se pudo eliminar el producto'}`);
      }
    } catch (error) {
      console.error('Error al eliminar producto:', error);
      alert('Error: ' + error.message);
    }
  };

  const handleEditarProducto = (producto) => {
    if (usuario?.rol !== 'vendedor' && usuario?.rol !== 'admin_sistema') return;
    setEditando(true);
    setProductoEditado(producto);
    setFormData({
      nombre: producto.nombre,
      descripcion: producto.descripcion,
      precio: producto.precio,
      stock: producto.stock,
      imagen_url: producto.imagen_url || ''
    });
  };

  const handleGuardarProducto = async () => {
    if (!formData.nombre || !formData.precio) {
      alert('Completa los campos obligatorios (nombre, precio)');
      return;
    }
    
    try {
      // Obtener usuario del localStorage
      const usuarioJson = localStorage.getItem('usuario');
      const usuario = usuarioJson ? JSON.parse(usuarioJson) : null;
      
      // Preparar datos para enviar
      const datosActualizacion = {
        nombre: formData.nombre,
        descripcion: formData.descripcion,
        precio: formData.precio,
        stock: formData.stock,
        imagen_url: formData.imagen_url,
        usuario_id: usuario?.id
      };
      
      // Enviar al backend
      const response = await fetch(
        `${API_BASE_URL}/api/productos/${productoEditado.id}/actualizar/`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(datosActualizacion)
        }
      );
      
      const data = await response.json();
      
      if (data.success) {
        // Actualizar el producto en la lista local
        const productosActualizados = productos.map(p =>
          p.id === productoEditado.id ? { ...p, ...formData } : p
        );
        setProductos(productosActualizados);
        setEditando(false);
        setProductoEditado(null);
        alert('Producto actualizado correctamente en la base de datos');
      } else {
        alert(`Error: ${data.message || 'No se pudo actualizar el producto'}`);
      }
    } catch (error) {
      console.error('Error al actualizar producto:', error);
      alert('Error al guardar en la base de datos: ' + error.message);
    }
  };

  const productosPorCategoria = productos.filter(
    p => p.categoria?.nombre === categoriaSeleccionada
  );

  const getIconoCategoria = (categoria) => {
    const iconos = {
      'Vinos': 'fas fa-wine-glass-alt',
      'Cervezas': 'fas fa-beer',
      'Piscos': 'fas fa-glass-whiskey',
      'Whiskys': 'fas fa-glass-whiskey',
      'Ron': 'fas fa-glass-whiskey'
    };
    return iconos[categoria] || 'fas fa-bottle-water';
  };

  if (loading) {
    return (
      <div className="container py-5">
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Cargando...</span>
          </div>
          <p className="mt-3">Cargando catalogo...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container-fluid py-5" style={{ backgroundColor: 'var(--light-bg)' }}>
        {/* Botón para crear producto - Solo Admin Sistema */}
        {usuario?.rol === 'admin_sistema' && (
          <div className="mb-4" style={{ marginTop: '20px' }}>
            <button
              onClick={() => setCreando(true)}
              className="btn"
              style={{
                backgroundColor: '#28a745',
                color: 'white',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '8px',
                fontSize: '1rem',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#218838'}
              onMouseLeave={(e) => e.target.style.backgroundColor = '#28a745'}
            >
              <i className="fas fa-plus"></i> Crear Nuevo Producto
            </button>
          </div>
        )}

        {/* Modal de Creación */}
        {creando && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            overflowY: 'auto'
          }}>
            <div style={{
              backgroundColor: 'white',
              padding: '30px',
              borderRadius: '15px',
              maxWidth: '600px',
              width: '95%',
              boxShadow: '0 5px 15px rgba(0,0,0,0.3)',
              margin: '20px auto'
            }}>
              <h3 style={{ color: 'var(--primary-color)', marginBottom: '20px' }}>Crear Nuevo Producto</h3>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: 'var(--primary-color)' }}>Nombre del Producto:</label>
                <input
                  type="text"
                  value={formDataNuevo.nombre || ''}
                  onChange={(e) => setFormDataNuevo({...formDataNuevo, nombre: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '2px solid #ddd',
                    borderRadius: '8px',
                    fontSize: '1rem',
                    boxSizing: 'border-box'
                  }}
                  placeholder="Ingrese el nombre del producto"
                />
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: 'var(--primary-color)' }}>Descripción:</label>
                <textarea
                  value={formDataNuevo.descripcion || ''}
                  onChange={(e) => setFormDataNuevo({...formDataNuevo, descripcion: e.target.value})}
                  rows="4"
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '2px solid #ddd',
                    borderRadius: '8px',
                    fontSize: '1rem',
                    fontFamily: 'inherit',
                    boxSizing: 'border-box'
                  }}
                  placeholder="Ingrese la descripción del producto"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: 'var(--primary-color)' }}>Precio de Venta:</label>
                  <input
                    type="number"
                    value={formDataNuevo.precio || ''}
                    onChange={(e) => setFormDataNuevo({...formDataNuevo, precio: parseFloat(e.target.value) || 0})}
                    step="0.01"
                    min="0"
                    style={{
                      width: '100%',
                      padding: '10px',
                      border: '2px solid #ddd',
                      borderRadius: '8px',
                      fontSize: '1rem',
                      boxSizing: 'border-box'
                    }}
                    placeholder="Ingrese el precio"
                    required
                  />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: 'var(--primary-color)' }}>Costo Unitario:</label>
                  <input
                    type="number"
                    value={formDataNuevo.costo || ''}
                    onChange={(e) => setFormDataNuevo({...formDataNuevo, costo: parseFloat(e.target.value) || 0})}
                    step="0.01"
                    min="0"
                    style={{
                      width: '100%',
                      padding: '10px',
                      border: '2px solid #ddd',
                      borderRadius: '8px',
                      fontSize: '1rem',
                      boxSizing: 'border-box'
                    }}
                    placeholder="Ingrese el costo"
                    required
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: 'var(--primary-color)' }}>Stock Inicial:</label>
                  <input
                    type="number"
                    value={formDataNuevo.stock || ''}
                    onChange={(e) => setFormDataNuevo({...formDataNuevo, stock: parseInt(e.target.value) || 0})}
                    min="0"
                    style={{
                      width: '100%',
                      padding: '10px',
                      border: '2px solid #ddd',
                      borderRadius: '8px',
                      fontSize: '1rem',
                      boxSizing: 'border-box'
                    }}
                    placeholder="Ingrese la cantidad"
                    required
                  />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: 'var(--primary-color)' }}>Stock Mínimo:</label>
                  <input
                    type="number"
                    value={formDataNuevo.stock_minimo || ''}
                    onChange={(e) => setFormDataNuevo({...formDataNuevo, stock_minimo: parseInt(e.target.value) || 5})}
                    min="1"
                    style={{
                      width: '100%',
                      padding: '10px',
                      border: '2px solid #ddd',
                      borderRadius: '8px',
                      fontSize: '1rem',
                      boxSizing: 'border-box'
                    }}
                    placeholder="Stock mínimo (default: 5)"
                    required
                  />
                </div>
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: 'var(--primary-color)' }}>URL de Imagen:</label>
                <input
                  type="text"
                  value={formDataNuevo.imagen_url || ''}
                  onChange={(e) => setFormDataNuevo({...formDataNuevo, imagen_url: e.target.value})}
                  placeholder="https://ejemplo.com/imagen.jpg"
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '2px solid #ddd',
                    borderRadius: '8px',
                    fontSize: '1rem',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: 'var(--primary-color)' }}>Categoría:</label>
                <select
                  value={formDataNuevo.categoria_id || 1}
                  onChange={(e) => setFormDataNuevo({...formDataNuevo, categoria_id: parseInt(e.target.value)})}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '2px solid #ddd',
                    borderRadius: '8px',
                    fontSize: '1rem',
                    boxSizing: 'border-box'
                  }}
                >
                  <option value={1}>Vinos</option>
                  <option value={2}>Cervezas</option>
                  <option value={3}>Piscos</option>
                  <option value={4}>Whiskys</option>
                  <option value={5}>Ron</option>
                </select>
              </div>

              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button
                  onClick={() => setCreando(false)}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#6c757d',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600'
                  }}
                >
                  Cancelar
                </button>
                <button
                  onClick={handleCrearProducto}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#28a745',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontWeight: '600'
                  }}
                >
                  Crear Producto
                </button>
              </div>
            </div>
          </div>
        )}

      {/* Modal de ediciÃ³n */}
      {editando && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          overflowY: 'auto'
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '15px',
            maxWidth: '600px',
            width: '95%',
            boxShadow: 'var(--shadow-lg)',
            margin: '20px auto'
          }}>
            <h3 style={{ color: 'var(--primary-color)', marginBottom: '20px' }}>Editar Producto</h3>
            
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: 'var(--primary-color)' }}>Nombre del Producto:</label>
              <input
                type="text"
                value={formData.nombre || ''}
                onChange={(e) => setFormData({...formData, nombre: e.target.value})}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '2px solid var(--border-color)',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: 'var(--primary-color)' }}>DescripciÃ³n:</label>
              <textarea
                value={formData.descripcion || ''}
                onChange={(e) => setFormData({...formData, descripcion: e.target.value})}
                rows="4"
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '2px solid var(--border-color)',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  fontFamily: 'inherit',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: 'var(--primary-color)' }}>Precio:</label>
                <input
                  type="number"
                  value={formData.precio || ''}
                  onChange={(e) => setFormData({...formData, precio: parseFloat(e.target.value)})}
                  step="0.01"
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '2px solid var(--border-color)',
                    borderRadius: '8px',
                    fontSize: '1rem',
                    boxSizing: 'border-box'
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: 'var(--primary-color)' }}>Stock:</label>
                <input
                  type="number"
                  value={formData.stock || ''}
                  onChange={(e) => setFormData({...formData, stock: parseInt(e.target.value)})}
                  style={{
                    width: '100%',
                    padding: '10px',
                    border: '2px solid var(--border-color)',
                    borderRadius: '8px',
                    fontSize: '1rem',
                    boxSizing: 'border-box'
                  }}
                />
              </div>
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: 'var(--primary-color)' }}>URL de Imagen:</label>
              <input
                type="text"
                value={formData.imagen_url || ''}
                onChange={(e) => setFormData({...formData, imagen_url: e.target.value})}
                placeholder="https://ejemplo.com/imagen.jpg"
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '2px solid var(--border-color)',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: 'var(--primary-color)' }}>Categoría:</label>
              <select
                value={formData.categoria_id || 1}
                onChange={(e) => setFormData({...formData, categoria_id: parseInt(e.target.value)})}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '2px solid var(--border-color)',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  boxSizing: 'border-box'
                }}
              >
                <option value={1}>Vinos</option>
                <option value={2}>Cervezas</option>
                <option value={3}>Piscos</option>
                <option value={4}>Whiskys</option>
                <option value={5}>Ron</option>
              </select>
            </div>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setEditando(false)}
                style={{
                  padding: '10px 20px',
                  backgroundColor: 'var(--muted-color)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: '600'
                }}
              >
                Cancelar
              </button>
              <button
                onClick={handleGuardarProducto}
                style={{
                  padding: '10px 20px',
                  backgroundColor: 'var(--secondary-color)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: '600'
                }}
              >
                Guardar Cambios
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="container">
        <h1 className="fw-bold mb-5 text-center" style={{ color: 'var(--primary-color)' }}>
          <i className="fas fa-shop"></i> Catálogo de Licores
        </h1>

        {/* Buscador Avanzado */}
        <BuscadorAvanzado
          categorias={categorias}
          proveedores={proveedores}
          rangoPrecios={rangoPrecios}
          onFiltrosChange={handleFiltrosChange}
          mostrarFiltrosMobile={mostrarFiltrosMobile}
          onToggleFiltrosMobile={() => setMostrarFiltrosMobile(!mostrarFiltrosMobile)}
        />

        {/* Información de resultados */}
        {filtrosAplicados && Object.values(filtrosAplicados).some(v => v) && (
          <div className="alert alert-info mb-4">
            <strong>Resultados:</strong> Se encontraron {productosFiltrados.length} producto{productosFiltrados.length !== 1 ? 's' : ''} que coinciden con tu búsqueda
          </div>
        )}

        {/* Listado de Productos */}
        {productosFiltrados.length === 0 ? (
          <div className="alert alert-warning mt-5">
            <i className="fas fa-inbox"></i> No se encontraron productos que coincidan con tu búsqueda
          </div>
        ) : (
          <div className="row g-4">
            {productosFiltrados.map(producto => (
              <div key={producto.id} className="col-lg-3 col-md-4 col-sm-6">
                <div
                  className="card h-100 shadow-sm"
                  style={{
                    transition: 'all 0.3s',
                    cursor: 'pointer',
                    border: `2px solid var(--border-color)`,
                    position: 'relative'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-5px)'}
                  onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                >
                  <div style={{ position: 'relative', overflow: 'hidden', height: '250px' }}>
                    <img
                      src={producto.imagen_url || producto.imagen}
                      alt={producto.nombre}
                      style={{ height: '100%', objectFit: 'cover', width: '100%' }}
                      className="card-img-top"
                    />
                    {producto.stock <= 0 && (
                      <div
                        style={{
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          bottom: 0,
                          backgroundColor: 'rgba(0, 0, 0, 0.6)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}
                      >
                        <span className="text-white fw-bold">AGOTADO</span>
                      </div>
                    )}
                    {(usuario?.rol === 'vendedor' || usuario?.rol === 'admin_sistema') && (
                      <div style={{
                        position: 'absolute',
                        top: '10px',
                        right: '10px',
                        display: 'flex',
                        gap: '8px',
                        flexDirection: 'column'
                      }}>
                        <button
                          style={{
                            backgroundColor: 'var(--secondary-color)',
                            color: 'white',
                            border: 'none',
                            borderRadius: '50%',
                            width: '40px',
                            height: '40px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: 'pointer',
                            transition: 'all 0.3s'
                          }}
                          onClick={() => handleEditarProducto(producto)}
                          title="Editar producto"
                        >
                          <i className="fas fa-edit"></i>
                        </button>
                        {usuario?.rol === 'admin_sistema' && (
                          <button
                            style={{
                              backgroundColor: '#dc3545',
                              color: 'white',
                              border: 'none',
                              borderRadius: '50%',
                              width: '40px',
                              height: '40px',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              cursor: 'pointer',
                              transition: 'all 0.3s'
                            }}
                            onClick={() => handleEliminarProducto(producto.id)}
                            title="Eliminar producto"
                          >
                            <i className="fas fa-trash"></i>
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="card-body d-flex flex-column">
                    <h5 className="card-title" style={{ color: 'var(--primary-color)' }}>{producto.nombre}</h5>
                    <p className="card-text text-muted small">
                      {producto.descripcion?.substring(0, 80)}...
                    </p>
                    <div className="mb-3">
                      {producto.stock > 0 ? (
                        <span className="badge" style={{ backgroundColor: 'var(--success-color)' }}>Stock: {producto.stock}</span>
                      ) : (
                        <span className="badge" style={{ backgroundColor: 'var(--danger-color)' }}>Agotado</span>
                      )}
                    </div>
                    <p className="fw-bold fs-5 mb-3" style={{ color: 'var(--secondary-color)' }}>
                      ${producto.precio ? producto.precio.toLocaleString('es-CL') : '0'}
                    </p>
                    <div className="gap-2 d-flex mt-auto">
                      <button
                        className="btn btn-sm flex-grow-1"
                        style={{
                          color: 'var(--primary-color)',
                          border: `2px solid var(--primary-color)`,
                          backgroundColor: 'white'
                        }}
                        onClick={() => navigate(`/producto/${producto.id}`)}
                      >
                        Ver Detalle
                      </button>
                      <button
                        className="btn btn-sm flex-grow-1"
                        style={{
                          backgroundColor: 'var(--secondary-color)',
                          color: 'white',
                          border: 'none'
                        }}
                        onClick={() => agregarAlCarrito(producto)}
                        disabled={producto.stock <= 0}
                      >
                        <i className="fas fa-cart-plus"></i>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
export default CatalogoPorCategoria;
