import React from "react";
import "../styles/globals.css";

function Blog() {
  return (
    <div className="container py-5">
      <h2 className="fw-bold text-primary mb-5 text-center">
        <i className="fas fa-book-open"></i> Blog Elixir: Novedades y Cócteles
      </h2>
      <div className="row g-4">
        <div className="col-md-4">
          <div className="card h-100 shadow">
            <div className="card-body">
              <h5 className="card-title">Recetas de cócteles clásicos</h5>
              <p className="card-text">
                Aprende a preparar pisco sour, mojito y gin tonic con nuestras bebidas.
              </p>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card h-100 shadow">
            <div className="card-body">
              <h5 className="card-title">Nuevos lanzamientos</h5>
              <p className="card-text">
                Cervezas artesanales y vinos selectos recién llegados a la tienda.
              </p>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card h-100 shadow">
            <div className="card-body">
              <h5 className="card-title">Tips para maridar vino</h5>
              <p className="card-text">
                Consejos de sommeliers para elegir el mejor vino según tu ocasión.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Blog;
