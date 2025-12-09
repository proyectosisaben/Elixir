import React from "react";

function PagaDesdeCasa() {
  return (
    <section className="container py-5">
      <div className="row align-items-center">
        <div className="col-lg-6 mb-4 mb-lg-0">
          <img src="/static/images/compra-online.jpg" className="img-fluid rounded shadow" alt="Compra online Elixir"/>
        </div>
        <div className="col-lg-6">
          <h2 className="fw-bold text-primary mb-3">
            <i className="fas fa-mobile-alt"></i> Compra Online y Recibe en Casa
          </h2>
          <p className="lead mb-4">
            Pide tus bebidas favoritas desde la comodidad de tu hogar, paga de manera segura y recibe en tu puerta.
          </p>
          <ul className="list-unstyled">
            <li><i className="fas fa-check text-success"></i> Pagos con tarjeta o transferencia</li>
            <li><i className="fas fa-check text-success"></i> Despacho express zona Santiago</li>
            <li><i className="fas fa-check text-success"></i> Retiro en tienda disponible</li>
          </ul>
          <a href="/catalogo" className="btn btn-primary btn-lg mt-3">Descubrir Catálogo</a>
        </div>
      </div>
    </section>
  );
}

export default PagaDesdeCasa;
