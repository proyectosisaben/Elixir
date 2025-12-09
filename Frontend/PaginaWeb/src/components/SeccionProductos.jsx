import React from "react";

function SeccionProductos({ productos, onVerDetalle }) {
  return (
    <div className="row g-4">
      {productos.map(producto => (
        <div key={producto.id} className="col-md-4">
          <div className="card h-100 shadow">
            <img src={producto.imagen} alt={producto.nombre} style={{height: "250px", objectFit: "cover"}} className="card-img-top"/>
            <div className="card-body text-center">
              <h5 className="card-title">{producto.nombre}</h5>
              <p className="card-text text-muted">{producto.categoria.nombre}</p>
              <p className="fw-bold text-primary">${producto.precio.toLocaleString('es-CL')}</p>
              <button className="btn btn-outline-primary" onClick={() => onVerDetalle(producto.id)}>
                Ver Detalle
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default SeccionProductos;
