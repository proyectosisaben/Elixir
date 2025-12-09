import React from "react";

function ContenidoLogin({ onLogin, error }) {
  return (
    <div className="container my-5">
      <div className="row justify-content-center">
        <div className="col-md-5">
          <div className="card shadow">
            <div className="card-body">
              <h2 className="fw-bold mb-4 text-primary text-center">
                <i className="fas fa-user"></i> Ingreso a Elixir
              </h2>
              <form onSubmit={onLogin}>
                <div className="mb-3">
                  <label htmlFor="email" className="form-label">Correo electrónico</label>
                  <input type="email" className="form-control" id="email" name="email" required/>
                </div>
                <div className="mb-3">
                  <label htmlFor="password" className="form-label">Contraseña</label>
                  <input type="password" className="form-control" id="password" name="password" required/>
                </div>
                {error && <div className="alert alert-danger">{error}</div>}
                <button className="btn btn-primary w-100" type="submit">Ingresar</button>
              </form>
              <div className="text-center mt-3">
                <a href="/registro">¿No tienes cuenta? Regístrate aquí</a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ContenidoLogin;
