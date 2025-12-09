import React from "react";

function ContenidoBlog() {
  return (
    <section className="container py-5">
      <h2 className="fw-bold text-primary text-center mb-5">
        <i className="fas fa-book-open"></i> Blog Elixir: Novedades & Cócteles
      </h2>
      <div className="row g-4">
        <div className="col-md-4">
          <div className="card h-100 shadow">
            <div className="card-body">
              <h5 className="card-title">Recetas de cócteles clásicos</h5>
              <p className="card-text">
                Aprende a preparar el mejor pisco sour, mojito y gin tonic usando nuestros destilados exclusivos de Elixir.
              </p>
            </div>
            <div className="card-footer bg-white border-0">
              <small className="text-muted"><i className="fas fa-cocktail text-warning"></i> Cómpralos en Elixir</small>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card h-100 shadow">
            <div className="card-body">
              <h5 className="card-title">Novedades y lanzamientos</h5>
              <p className="card-text">
                Descubre las nuevas cervezas artesanales y exclusivos vinos que acaban de llegar a Elixir.
              </p>
            </div>
            <div className="card-footer bg-white border-0">
              <small className="text-muted"><i className="fas fa-plus-circle text-success"></i> Actualización semanal</small>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card h-100 shadow">
            <div className="card-body">
              <h5 className="card-title">Tips para elegir tu vino</h5>
              <p className="card-text">
                Consejos para seleccionar la botella ideal según la ocasión y tu gusto, directo de nuestros sommeliers Elixir.
              </p>
            </div>
            <div className="card-footer bg-white border-0">
              <small className="text-muted"><i className="fas fa-wine-glass text-primary"></i> Blog Elixir</small>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default ContenidoBlog;
