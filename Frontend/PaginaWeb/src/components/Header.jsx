import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useRol } from "../contexts/RolContext";
import "../styles/globals.css";

function Header() {
  const navigate = useNavigate();
  const { usuario, logout, tieneRol, rolActualizado } = useRol();
  const [carritoCount, setCarritoCount] = useState(0);

  useEffect(() => {
    const carrito = localStorage.getItem("carrito");
    if (carrito) {
      const items = JSON.parse(carrito);
      setCarritoCount(items.length);
    }
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const getRolNavbarStyle = () => {
    if (!usuario) return {};
    switch (usuario.rol) {
      case "admin_sistema":
        return { backgroundColor: "var(--danger-color)" };
      case "gerente":
        return { backgroundColor: "var(--warning-color)" };
      case "vendedor":
        return { backgroundColor: "var(--success-color)" };
      case "cliente":
      default:
        return { backgroundColor: "var(--primary-color)" };
    }
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-dark shadow" style={getRolNavbarStyle()}>
      <div className="container">
        <a className="navbar-brand fw-bold" href="/">
          <i className="fas fa-wine-bottle"></i> Elixir
        </a>
        <button
          className="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarNav"
        >
          <span className="navbar-toggler-icon"></span>
        </button>
        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav ms-auto mb-2 mb-lg-0">
            <li className="nav-item">
              <a className="nav-link" href="/catalogo">Catálogo</a>
            </li>
            <li className="nav-item">
              <a className="nav-link" href="/blog">Blog</a>
            </li>
            <li className="nav-item">
              <a className="nav-link" href="/atencion_cliente">Contacto</a>
            </li>

            {usuario ? (
              <>
                {tieneRol("admin_sistema") && (
                  <li className="nav-item dropdown">
                    <a
                      className="nav-link dropdown-toggle"
                      href="#"
                      id="adminDropdown"
                      role="button"
                      data-bs-toggle="dropdown"
                    >
                      <i className="fas fa-crown"></i> Admin
                    </a>
                    <ul className="dropdown-menu dropdown-menu-end">
                      <li>
                        <a className="dropdown-item" href="/admin/roles">
                          <i className="fas fa-users-cog"></i> Gestionar Roles
                        </a>
                      </li>
                      <li><hr className="dropdown-divider" /></li>
                      <li>
                        <a className="dropdown-item" href="/perfil">
                          <i className="fas fa-user-circle"></i> Mi Perfil
                        </a>
                      </li>
                    </ul>
                  </li>
                )}

                {tieneRol("gerente") && !tieneRol("admin_sistema") && (
                  <li className="nav-item dropdown">
                    <a
                      className="nav-link dropdown-toggle"
                      href="#"
                      id="gerenteDropdown"
                      role="button"
                      data-bs-toggle="dropdown"
                    >
                      <i className="fas fa-chart-bar"></i> Gerencia
                    </a>
                    <ul className="dropdown-menu dropdown-menu-end">
                      <li>
                        <a className="dropdown-item" href="/dashboard">
                          <i className="fas fa-tachometer-alt"></i> Panel de Gerente
                        </a>
                      </li>
                      <li>
                        <a className="dropdown-item" href="/perfil">
                          <i className="fas fa-user-circle"></i> Mi Perfil
                        </a>
                      </li>
                    </ul>
                  </li>
                )}

                <li className="nav-item dropdown">
                  <a
                    className="nav-link dropdown-toggle"
                    href="#"
                    id="userDropdown"
                    role="button"
                    data-bs-toggle="dropdown"
                  >
                    <i className="fas fa-user-circle"></i> {usuario.email}
                  </a>
                  <ul className="dropdown-menu dropdown-menu-end">
                    <li>
                      <a className="dropdown-item" href="/perfil">
                        <i className="fas fa-user-circle"></i> Mi Perfil
                      </a>
                    </li>
                    <li><hr className="dropdown-divider" /></li>
                    <li>
                      <button className="dropdown-item" onClick={handleLogout}>
                        <i className="fas fa-sign-out-alt"></i> Cerrar Sesión
                      </button>
                    </li>
                  </ul>
                </li>
              </>
            ) : (
              <>
                <li className="nav-item">
                  <a className="nav-link" href="/registro">Registrarse</a>
                </li>
                <li className="nav-item">
                  <a className="nav-link" href="/login">Inicia Sesión</a>
                </li>
              </>
            )}

            <li className="nav-item position-relative">
              <a className="nav-link" href="/carrito">
                <i className="fas fa-shopping-cart"></i> Carrito
                {carritoCount > 0 && (
                  <span className="badge" style={{ backgroundColor: "var(--danger-color)" }} role="status" aria-hidden="true">
                    {carritoCount}
                  </span>
                )}
              </a>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
}

export default Header;
