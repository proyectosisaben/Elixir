import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { registroCliente } from "../api";
import "../styles/globals.css";

function InicioRegistro() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [fechaNacimiento, setFechaNacimiento] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [exito, setExito] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setExito(false);
    setLoading(true);

    // Validaciones
    if (password !== passwordConfirm) {
      setError("Las contraseñas no coinciden");
      setLoading(false);
      return;
    }

    if (password.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres");
      setLoading(false);
      return;
    }

    try {
      const resultado = await registroCliente({
        email,
        password,
        password_confirm: passwordConfirm,
        fecha_nacimiento: fechaNacimiento,
      });

      setExito(true);
      
      // Redirigir a login después de 2 segundos
      setTimeout(() => {
        navigate("/login");
      }, 2000);
    } catch (err) {
      setError(err.message || "Error al registrarse");
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
                <i className="fas fa-user-plus"></i> Registro Elixir
              </h2>

              {exito && (
                <div className="alert alert-success alert-dismissible fade show" role="alert">
                  <i className="fas fa-check-circle"></i> ¡Registro exitoso!
                  <br />
                  <small>Redirigiendo a login...</small>
                  <button type="button" className="btn-close"></button>
                </div>
              )}

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
                    placeholder="Mínimo 8 caracteres"
                    minLength={8}
                    required
                  />
                </div>

                <div className="mb-3">
                  <label className="form-label">
                    <i className="fas fa-lock"></i> Confirmar Contraseña
                  </label>
                  <input
                    type="password"
                    className="form-control"
                    value={passwordConfirm}
                    onChange={(e) => setPasswordConfirm(e.target.value)}
                    placeholder="Repite tu contraseña"
                    minLength={8}
                    required
                  />
                </div>

                <div className="mb-3">
                  <label className="form-label">
                    <i className="fas fa-calendar"></i> Fecha de nacimiento
                  </label>
                  <input
                    type="date"
                    className="form-control"
                    value={fechaNacimiento}
                    onChange={(e) => setFechaNacimiento(e.target.value)}
                    required
                  />
                </div>

                <button
                  className="btn btn-primary w-100 mb-3"
                  type="submit"
                  disabled={loading || exito}
                >
                  {loading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2"></span>
                      Registrando...
                    </>
                  ) : exito ? (
                    <>
                      <i className="fas fa-check-circle"></i> Registro Completado
                    </>
                  ) : (
                    <>
                      <i className="fas fa-user-plus"></i> Registrarse
                    </>
                  )}
                </button>
              </form>

              <hr />

              <div className="text-center">
                <p className="mb-0">
                  ¿Ya tienes cuenta?{" "}
                  <a href="/login" className="btn btn-link btn-sm p-0">
                    Inicia sesión aquí
                  </a>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default InicioRegistro;
