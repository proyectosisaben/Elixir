import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { loginCliente } from "../api";
import "../styles/globals.css";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const resultado = await loginCliente({ email, password });
      
      // Guardar token en localStorage
      localStorage.setItem("token", resultado.token);
      localStorage.setItem("usuario", JSON.stringify(resultado.usuario));
      
      // Emitir evento para actualizar contexto
      window.dispatchEvent(new Event("usuario-actualizado"));
      
      // Redirigir según el rol
      const usuario = resultado.usuario;
      if (usuario.rol === 'admin_sistema') {
        navigate("/dashboard-admin");
      } else if (usuario.rol === 'gerente') {
        navigate("/dashboard");
      } else if (usuario.rol === 'vendedor') {
        navigate("/dashboard-vendedor");
      } else if (usuario.rol === 'cliente') {
        navigate("/dashboard-cliente");
      } else {
        navigate("/");
      }
    } catch (err) {
      console.error('Error de login:', err);
      
      if (err.message === 'Failed to fetch') {
        setError("❌ No se puede conectar al servidor. Verifica que el backend esté corriendo en http://localhost:8000");
      } else {
        setError(err.message || "Error al iniciar sesión");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container my-5">
      <div className="row justify-content-center">
        <div className="col-md-6">
          <div className="card shadow">
            <div className="card-body">
              <h2 className="fw-bold mb-4 text-primary text-center">
                <i className="fas fa-sign-in-alt"></i> Inicia Sesión
              </h2>

              {error && (
                <div className="alert alert-danger alert-dismissible fade show" role="alert">
                  <i className="fas fa-exclamation-circle"></i> {error}
                  <button
                    type="button"
                    className="btn-close"
                    onClick={() => setError("")}
                  ></button>
                </div>
              )}

              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label className="form-label">
                    <i className="fas fa-envelope"></i> Correo electrónico
                  </label>
                  <input
                    type="email"
                    className="form-control"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="tu@email.com"
                    required
                  />
                </div>

                <div className="mb-3">
                  <label className="form-label">
                    <i className="fas fa-lock"></i> Contraseña
                  </label>
                  <input
                    type="password"
                    className="form-control"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Ingresa tu contraseña"
                    required
                  />
                </div>

                <button
                  className="btn btn-primary w-100 mb-3"
                  type="submit"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2"></span>
                      Iniciando sesión...
                    </>
                  ) : (
                    <>
                      <i className="fas fa-sign-in-alt"></i> Iniciar Sesión
                    </>
                  )}
                </button>
              </form>

              <hr />

              <div className="text-center">
                <p className="mb-0">
                  ¿No tienes cuenta?{" "}
                  <Link to="/registro" className="btn btn-link btn-sm p-0">
                    Regístrate aquí
                  </Link>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login;
