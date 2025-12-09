import React from "react";

function SeccionComentarios({ comentarios }) {
  return (
    <section className="bg-light py-5">
      <div className="container">
        <h2 className="fw-bold text-primary text-center mb-4">Comentarios de Clientes</h2>
        <div className="row g-4">
          {comentarios && comentarios.length > 0 ? comentarios.map((c, i) => (
            <div key={i} className="col-md-4">
              <div className="card h-100 shadow-sm">
                <div className="card-body">
                  <blockquote className="blockquote mb-0">
                    <p>{c.texto}</p>
                    <footer className="blockquote-footer">{c.nombre}, <cite>{c.fecha}</cite></footer>
                  </blockquote>
                </div>
              </div>
            </div>
          )) : (
            <div className="col">
              <div className="alert alert-info text-center">
                Aún no hay comentarios. ¡Compra en Elixir y sé el primero en opinar!
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

export default SeccionComentarios;
