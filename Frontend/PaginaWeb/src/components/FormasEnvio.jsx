import React from "react";

function FormasEnvio() {
  return (
    <section className="py-5 bg-light">
      <div className="container">
        <h2 className="fw-bold text-primary mb-4">
          <i className="fas fa-truck"></i> Formas de Envío
        </h2>
        <div className="row g-4">
          <div className="col-md-4">
            <div className="card h-100 border-primary">
              <div className="card-body text-center">
                <i className="fas fa-home fa-2x text-primary mb-3"></i>
                <h5 className="card-title">Despacho a Domicilio</h5>
                <p className="card-text">Recibe tus pedidos de vinos y licores directo en tu casa dentro de Santiago.</p>
              </div>
            </div>
          </div>
          <div className="col-md-4">
            <div className="card h-100 border-success">
              <div className="card-body text-center">
                <i className="fas fa-store fa-2x text-success mb-3"></i>
                <h5 className="card-title">Retiro en Tienda</h5>
                <p className="card-text">Elige tus productos online y retira en nuestra botillería Elixir sin costo.</p>
              </div>
            </div>
          </div>
          <div className="col-md-4">
            <div className="card h-100 border-warning">
              <div className="card-body text-center">
                <i className="fas fa-route fa-2x text-warning mb-3"></i>
                <h5 className="card-title">Envío a Regiones</h5>
                <p className="card-text">Consultanos por envíos a regiones a través de nuestro equipo de atención.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default FormasEnvio;
