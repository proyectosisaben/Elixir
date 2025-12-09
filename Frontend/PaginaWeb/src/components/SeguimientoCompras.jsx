import React from "react";

function SeguimientoCompras() {
  return (
    <section className="container py-5">
      <h2 className="fw-bold text-primary text-center mb-4">
        <i className="fas fa-route"></i> Seguimiento de Compras
      </h2>
      <div className="row justify-content-center">
        <div className="col-md-7">
          <form className="mb-4">
            <label className="form-label" htmlFor="codigoPedido">Ingresa tu número de pedido:</label>
            <input type="text" className="form-control mb-3" id="codigoPedido" placeholder="Ej: ELX-20250005"/>
            <button className="btn btn-primary" type="submit">Buscar Pedido</button>
          </form>
          <div className="alert alert-info text-center">
            El seguimiento estará disponible tras la confirmación de tu compra. 
            Para ayuda, contacta a nuestro equipo Elixir.
          </div>
        </div>
      </div>
    </section>
  );
}

export default SeguimientoCompras;
