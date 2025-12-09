import React from "react";

function BarraBuscadoraProductos({ onBuscar }) {
  return (
    <div className="container mt-4">
      <div className="row justify-content-center">
        <div className="col-md-8">
          <form className="input-group shadow-sm" onSubmit={e => e.preventDefault()}>
            <input
              type="search"
              className="form-control form-control-lg"
              placeholder="Buscar vinos, cervezas, destilados, promociones..."
              aria-label="Buscar productos de Elixir"
              onChange={e => onBuscar(e.target.value)}
            />
            <button className="btn btn-primary btn-lg" type="submit">
              <i className="fas fa-search"></i> Buscar
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default BarraBuscadoraProductos;
