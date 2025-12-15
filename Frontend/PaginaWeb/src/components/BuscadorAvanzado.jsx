import React, { useState, useEffect, useRef, useCallback } from 'react';
import './BuscadorAvanzado.css';
import { construirParametrosQueryFiltros, formatearPrecio } from '../utils/filtrosUtils';

function BuscadorAvanzado({
  categorias = [],
  proveedores = [],
  rangoPrecios = { minimo: 0, maximo: 1000000 },
  onFiltrosChange = () => {},
  mostrarFiltrosMobile = false,
  onToggleFiltrosMobile = () => {},
}) {
  const [busqueda, setBusqueda] = useState('');
  const [sugerencias, setSugerencias] = useState([]);
  const [mostrarSugerencias, setMostrarSugerencias] = useState(false);
  const [cargandoSugerencias, setCargandoSugerencias] = useState(false);
  const buscadorRef = useRef(null);

  // Filtros
  const [categoriasFiltro, setCategoriasFiltro] = useState([]);
  const [proveedorFiltro, setProveedorFiltro] = useState('');
  const [precioMin, setPrecioMin] = useState(rangoPrecios.minimo);
  const [precioMax, setPrecioMax] = useState(rangoPrecios.maximo);
  const [disponible, setDisponible] = useState(null); // null = todos, true = en stock, false = agotado

  // Chips de filtros aplicados
  const [filtrosAplicados, setFiltrosAplicados] = useState([]);

  // Debounce para autocompletado
  const debounceTimer = useRef(null);

  // Obtener sugerencias
  const obtenerSugerencias = useCallback(async (query) => {
    if (query.length < 2) {
      setSugerencias([]);
      return;
    }

    setCargandoSugerencias(true);
    try {
      const response = await fetch(`${window.API_BASE_URL}/api/productos/sugerencias/?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      setSugerencias(data.sugerencias || []);
      setMostrarSugerencias(true);
    } catch (error) {
      console.error('Error al obtener sugerencias:', error);
      setSugerencias([]);
    } finally {
      setCargandoSugerencias(false);
    }
  }, []);

  // Manejar cambio en búsqueda con debounce
  const handleBusquedaChange = (e) => {
    const valor = e.target.value;
    setBusqueda(valor);

    clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      obtenerSugerencias(valor);
    }, 300);
  };

  // Seleccionar sugerencia
  const seleccionarSugerencia = (sugerencia) => {
    setBusqueda(sugerencia.nombre);
    setSugerencias([]);
    setMostrarSugerencias(false);
    aplicarFiltros({
      busqueda: sugerencia.nombre,
      categorias: categoriasFiltro,
      proveedor: proveedorFiltro,
      precioMin,
      precioMax,
      disponible,
    });
  };

  // Manejar checkboxes de categorías
  const handleCategoriaChange = (categoriaId) => {
    setCategoriasFiltro((prev) => {
      const nuevas = prev.includes(categoriaId)
        ? prev.filter((id) => id !== categoriaId)
        : [...prev, categoriaId];
      aplicarFiltros({
        busqueda,
        categorias: nuevas,
        proveedor: proveedorFiltro,
        precioMin,
        precioMax,
        disponible,
      });
      return nuevas;
    });
  };

  // Aplicar filtros
  const aplicarFiltros = (filtros) => {
    const query = construirParametrosQueryFiltros(filtros);
    onFiltrosChange(filtros);

    // Actualizar chips de filtros aplicados
    const chips = [];
    if (filtros.busqueda) {
      chips.push({
        id: 'busqueda',
        tipo: 'busqueda',
        label: `Búsqueda: "${filtros.busqueda}"`,
      });
    }
    if (filtros.categorias?.length > 0) {
      filtros.categorias.forEach((catId) => {
        const cat = categorias.find((c) => c.id === parseInt(catId));
        if (cat) {
          chips.push({
            id: `cat-${catId}`,
            tipo: 'categoria',
            label: `${cat.nombre}`,
          });
        }
      });
    }
    if (filtros.proveedor) {
      const prov = proveedores.find((p) => p.id === parseInt(filtros.proveedor));
      if (prov) {
        chips.push({
          id: `prov-${filtros.proveedor}`,
          tipo: 'proveedor',
          label: `${prov.nombre}`,
        });
      }
    }
    if (filtros.disponible !== null) {
      chips.push({
        id: 'disponible',
        tipo: 'disponible',
        label: filtros.disponible ? 'En stock' : 'Agotado',
      });
    }

    setFiltrosAplicados(chips);
  };

  // Remover filtro
  const removerFiltro = (filtroId) => {
    const filtro = filtrosAplicados.find((f) => f.id === filtroId);
    if (!filtro) return;

    let nuevosFiltros = { busqueda, categorias: categoriasFiltro, proveedor: proveedorFiltro, precioMin, precioMax, disponible };

    switch (filtro.tipo) {
      case 'busqueda':
        setBusqueda('');
        nuevosFiltros.busqueda = '';
        break;
      case 'categoria':
        const newCats = categoriasFiltro.filter((id) => id !== parseInt(filtroId.split('-')[1]));
        setCategoriasFiltro(newCats);
        nuevosFiltros.categorias = newCats;
        break;
      case 'proveedor':
        setProveedorFiltro('');
        nuevosFiltros.proveedor = '';
        break;
      case 'disponible':
        setDisponible(null);
        nuevosFiltros.disponible = null;
        break;
      default:
        break;
    }

    aplicarFiltros(nuevosFiltros);
  };

  // Resetear todos los filtros
  const resetearFiltros = () => {
    setBusqueda('');
    setCategoriasFiltro([]);
    setProveedorFiltro('');
    setPrecioMin(rangoPrecios.minimo);
    setPrecioMax(rangoPrecios.maximo);
    setDisponible(null);
    setFiltrosAplicados([]);

    onFiltrosChange({
      busqueda: '',
      categorias: [],
      proveedor: '',
      precioMin: rangoPrecios.minimo,
      precioMax: rangoPrecios.maximo,
      disponible: null,
    });
  };

  // Cerrar sugerencias al hacer clic fuera
  useEffect(() => {
    const handleClickFuera = (e) => {
      if (buscadorRef.current && !buscadorRef.current.contains(e.target)) {
        setMostrarSugerencias(false);
      }
    };

    document.addEventListener('mousedown', handleClickFuera);
    return () => document.removeEventListener('mousedown', handleClickFuera);
  }, []);

  return (
    <div className="buscador-avanzado">
      {/* Búsqueda con autocompletado */}
      <div className="busqueda-container" ref={buscadorRef}>
        <div className="input-busqueda-wrapper">
          <input
            type="text"
            className="input-busqueda"
            placeholder="Buscar productos, marca, SKU..."
            value={busqueda}
            onChange={handleBusquedaChange}
            onFocus={() => busqueda.length >= 2 && setMostrarSugerencias(true)}
          />
          <svg className="icono-busqueda" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>

          {/* Dropdown de sugerencias */}
          {mostrarSugerencias && (sugerencias.length > 0 || cargandoSugerencias) && (
            <div className="sugerencias-dropdown">
              {cargandoSugerencias ? (
                <div className="sugerencia-item loading">Cargando...</div>
              ) : (
                sugerencias.map((sugerencia) => (
                  <div
                    key={sugerencia.id}
                    className="sugerencia-item"
                    onClick={() => seleccionarSugerencia(sugerencia)}
                  >
                    <div className="sugerencia-nombre">{sugerencia.nombre}</div>
                    <div className="sugerencia-info">
                      <span className="sugerencia-sku">{sugerencia.sku}</span>
                      <span className="sugerencia-precio">{formatearPrecio(sugerencia.precio)}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Botón para mostrar/ocultar filtros en mobile */}
        <button
          className="btn-filtros-mobile"
          onClick={onToggleFiltrosMobile}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <line x1="4" y1="6" x2="20" y2="6"></line>
            <line x1="4" y1="12" x2="20" y2="12"></line>
            <line x1="4" y1="18" x2="20" y2="18"></line>
          </svg>
          Filtros
        </button>
      </div>

      {/* Chips de filtros aplicados */}
      {filtrosAplicados.length > 0 && (
        <div className="chips-filtros">
          {filtrosAplicados.map((chip) => (
            <div key={chip.id} className="chip-filtro">
              <span className="chip-label">{chip.label}</span>
              <button
                className="chip-remover"
                onClick={() => removerFiltro(chip.id)}
                aria-label="Remover filtro"
              >
                ✕
              </button>
            </div>
          ))}
          {filtrosAplicados.length > 0 && (
            <button className="btn-limpiar-filtros" onClick={resetearFiltros}>
              Limpiar todo
            </button>
          )}
        </div>
      )}

      {/* Panel de filtros */}
      <div className={`panel-filtros ${mostrarFiltrosMobile ? 'visible' : ''}`}>
        {/* Filtro de Categorías */}
        <div className="filtro-seccion">
          <h3 className="filtro-titulo">Categorías</h3>
          <div className="filtro-checkboxes">
            {categorias.map((categoria) => (
              <label key={categoria.id} className="checkbox-item">
                <input
                  type="checkbox"
                  checked={categoriasFiltro.includes(categoria.id)}
                  onChange={() => handleCategoriaChange(categoria.id)}
                />
                <span className="checkbox-label">{categoria.nombre}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Filtro de Proveedor */}
        {proveedores.length > 0 && (
          <div className="filtro-seccion">
            <h3 className="filtro-titulo">Proveedor</h3>
            <select
              className="select-filtro"
              value={proveedorFiltro}
              onChange={(e) => {
                setProveedorFiltro(e.target.value);
                aplicarFiltros({
                  busqueda,
                  categorias: categoriasFiltro,
                  proveedor: e.target.value,
                  precioMin,
                  precioMax,
                  disponible,
                });
              }}
            >
              <option value="">Todos los proveedores</option>
              {proveedores.map((prov) => (
                <option key={prov.id} value={prov.id}>
                  {prov.nombre}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Filtro de Disponibilidad */}
        <div className="filtro-seccion">
          <h3 className="filtro-titulo">Disponibilidad</h3>
          <div className="filtro-disponibilidad">
            <label className="radio-item">
              <input
                type="radio"
                name="disponibilidad"
                value="todos"
                checked={disponible === null}
                onChange={() => {
                  setDisponible(null);
                  aplicarFiltros({
                    busqueda,
                    categorias: categoriasFiltro,
                    proveedor: proveedorFiltro,
                    precioMin,
                    precioMax,
                    disponible: null,
                  });
                }}
              />
              <span>Todos</span>
            </label>
            <label className="radio-item">
              <input
                type="radio"
                name="disponibilidad"
                value="stock"
                checked={disponible === true}
                onChange={() => {
                  setDisponible(true);
                  aplicarFiltros({
                    busqueda,
                    categorias: categoriasFiltro,
                    proveedor: proveedorFiltro,
                    precioMin,
                    precioMax,
                    disponible: true,
                  });
                }}
              />
              <span>En stock</span>
            </label>
            <label className="radio-item">
              <input
                type="radio"
                name="disponibilidad"
                value="agotado"
                checked={disponible === false}
                onChange={() => {
                  setDisponible(false);
                  aplicarFiltros({
                    busqueda,
                    categorias: categoriasFiltro,
                    proveedor: proveedorFiltro,
                    precioMin,
                    precioMax,
                    disponible: false,
                  });
                }}
              />
              <span>Agotado</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BuscadorAvanzado;
