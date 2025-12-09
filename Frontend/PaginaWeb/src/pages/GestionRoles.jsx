import React, { useState, useEffect } from "react";
import { useRol } from "../contexts/RolContext";
import { useNavigate } from "react-router-dom";
import "../styles/globals.css";

function GestionRoles() {
  const { usuario } = useRol();
  const navigate = useNavigate();
  const [clientes, setClientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filtro, setFiltro] = useState("");
  const [rolSeleccionado, setRolSeleccionado] = useState({});
  const [actualizando, setActualizando] = useState(false);

  const ROLES = [
    { valor: "cliente", nombre: "Cliente", color: "primary", icono: "fas fa-user" },
    { valor: "vendedor", nombre: "Vendedor", color: "success", icono: "fas fa-store" },
    { valor: "gerente", nombre: "Gerente", color: "warning", icono: "fas fa-chart-bar" },
    { valor: "admin_sistema", nombre: "Admin Sistema", color: "danger", icono: "fas fa-crown" }
  ];

  useEffect(() => {
    cargarClientes();
  }, []);

  const cargarClientes = async () => {
    try {
      setLoading(true);
      const response = await fetch("http://localhost:8000/api/listar-clientes/");
      if (!response.ok) throw new Error("Error al cargar clientes");
      const data = await response.json();
      setClientes(data.clientes || []);
      
      // Inicializar rol seleccionado para cada cliente
      const rolesInit = {};
      data.clientes.forEach(c => {
        rolesInit[c.usuario_id] = c.rol;
      });
      setRolSeleccionado(rolesInit);
      setError(null);
    } catch (err) {
      console.error("Error:", err);
      setError("No se pudieron cargar los clientes");
    } finally {
      setLoading(false);
    }
  };

  const cambiarRol = async (usuarioId, nuevoRol) => {
    if (rolSeleccionado[usuarioId] === nuevoRol) return;

    setActualizando(true);
    try {
      const response = await fetch("http://localhost:8000/api/cambiar-rol/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          usuario_id: usuarioId,
          rol: nuevoRol
        })
      });

      const data = await response.json();
      
      if (!response.ok) throw new Error(data.message || "Error al cambiar rol");

      // Actualizar el estado local
      setRolSeleccionado({
        ...rolSeleccionado,
        [usuarioId]: nuevoRol
      });

      // Si el usuario que cambió rol es el usuario logueado actualmente
      const usuarioLogueado = JSON.parse(localStorage.getItem("usuario") || '{}');
      if (usuarioLogueado.id === usuarioId) {
        console.log('Cambiando rol del usuario logueado de:', usuarioLogueado.rol, 'a:', nuevoRol);
        const usuarioActualizado = {
          ...usuarioLogueado,
          rol: nuevoRol
        };
        localStorage.setItem("usuario", JSON.stringify(usuarioActualizado));
        
        // Emitir eventos de actualización
        setTimeout(() => {
          window.dispatchEvent(new Event("usuario-actualizado"));
          window.dispatchEvent(new StorageEvent('storage', {
            key: 'usuario',
            newValue: JSON.stringify(usuarioActualizado)
          }));
        }, 50);

        // Alert y redireccionamiento
        alert(`Rol actualizado a ${data.rol_display || nuevoRol}\n\nLa página se actualizará automáticamente para mostrar tus nuevos permisos.`);
        
        // Redirigir al dashboard correspondiente según el nuevo rol
        setTimeout(() => {
          if (nuevoRol === 'cliente') {
            navigate('/dashboard-cliente');
          } else if (nuevoRol === 'vendedor') {
            navigate('/dashboard-vendedor');
          } else if (nuevoRol === 'gerente') {
            navigate('/dashboard');
          } else if (nuevoRol === 'admin_sistema') {
            navigate('/dashboard-admin');
          }
        }, 500);
      } else {
        alert(`Rol actualizado a ${data.rol_display || nuevoRol}`);
        // Recargar clientes para asegurar sincronización
        await cargarClientes();
      }
    } catch (err) {
      console.error("Error:", err);
      alert(`Error: ${err.message}`);
      // Revertir cambio
      setRolSeleccionado({
        ...rolSeleccionado,
        [usuarioId]: rolSeleccionado[usuarioId]
      });
    } finally {
      setActualizando(false);
    }
  };

  const clientesFiltrados = clientes.filter(c =>
    c.email.toLowerCase().includes(filtro.toLowerCase()) ||
    c.nombre.toLowerCase().includes(filtro.toLowerCase())
  );

  const getRolInfo = (rol) => {
    return ROLES.find(r => r.valor === rol) || ROLES[0];
  };

  if (loading) {
    return (
      <div className="container mt-5">
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Cargando...</span>
          </div>
          <p className="mt-3">Cargando clientes...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container-fluid py-5 bg-light min-vh-100">
      <div className="container">
        {/* Header */}
        <div className="mb-5">
          <h1 className="fw-bold text-primary mb-2">
            <i className="fas fa-users-cog"></i> Gestión de Roles
          </h1>
          <p className="text-muted">
            Administra los roles de los usuarios del sistema (Solo Administradores)
          </p>
        </div>

        {/* Filtro */}
        <div className="row mb-4">
          <div className="col-md-6">
            <div className="input-group input-group-lg">
              <span className="input-group-text bg-white">
                <i className="fas fa-search text-muted"></i>
              </span>
              <input
                type="text"
                className="form-control border-start-0"
                placeholder="Buscar por email o nombre..."
                value={filtro}
                onChange={(e) => setFiltro(e.target.value)}
              />
            </div>
          </div>
          <div className="col-md-6 text-end">
            <button
              className="btn btn-primary btn-lg"
              onClick={cargarClientes}
              disabled={actualizando}
            >
              <i className="fas fa-sync"></i> Recargar
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="alert alert-danger alert-dismissible fade show">
            <i className="fas fa-exclamation-circle"></i> {error}
            <button
              type="button"
              className="btn-close"
              onClick={() => setError(null)}
            ></button>
          </div>
        )}

        {/* Tabla de clientes */}
        {clientesFiltrados.length === 0 ? (
          <div className="alert alert-info text-center">
            <i className="fas fa-info-circle"></i> No hay clientes para mostrar
          </div>
        ) : (
          <div className="row">
            {clientesFiltrados.map((cliente) => {
              const rolActual = getRolInfo(rolSeleccionado[cliente.usuario_id]);
              return (
                <div key={cliente.usuario_id} className="col-lg-6 col-xl-4 mb-4">
                  <div className="card shadow-sm border-0 h-100 cliente-card">
                    {/* Header con rol actual */}
                    <div className={`card-header bg-${rolActual.color} text-white border-0`}>
                      <div className="d-flex justify-content-between align-items-center">
                        <span>
                          <i className={rolActual.icono}></i> {rolActual.nombre}
                        </span>
                        <span className={`badge bg-${rolActual.color} badge-status`}>
                          {cliente.usuario_id}
                        </span>
                      </div>
                    </div>

                    {/* Body */}
                    <div className="card-body">
                      {/* Email */}
                      <div className="mb-3">
                        <h6 className="card-subtitle text-muted mb-1">Email</h6>
                        <p className="card-text fw-bold">
                          <i className="fas fa-envelope text-primary me-2"></i>
                          {cliente.email}
                        </p>
                      </div>

                      {/* Nombre */}
                      <div className="mb-3">
                        <h6 className="card-subtitle text-muted mb-1">Nombre</h6>
                        <p className="card-text">
                          <i className="fas fa-user text-info me-2"></i>
                          {cliente.nombre || "Sin nombre"}
                        </p>
                      </div>

                      {/* Fecha de nacimiento */}
                      <div className="mb-3">
                        <h6 className="card-subtitle text-muted mb-1">Fecha de Nacimiento</h6>
                        <p className="card-text">
                          <i className="fas fa-birthday-cake text-warning me-2"></i>
                          {new Date(cliente.fecha_nacimiento).toLocaleDateString("es-CL")}
                        </p>
                      </div>

                      {/* Email confirmado */}
                      <div className="mb-4">
                        <h6 className="card-subtitle text-muted mb-1">Estado de Email</h6>
                        <p className="card-text">
                          {cliente.email_confirmado ? (
                            <span className="badge bg-success">
                              <i className="fas fa-check-circle"></i> Confirmado
                            </span>
                          ) : (
                            <span className="badge bg-secondary">
                              <i className="fas fa-clock"></i> Pendiente
                            </span>
                          )}
                        </p>
                      </div>

                      {/* Selector de rol */}
                      <div className="mb-3">
                        <h6 className="card-subtitle text-muted mb-2">Cambiar Rol</h6>
                        <div className="btn-group-vertical w-100" role="group">
                          {ROLES.map((rol) => (
                            <button
                              key={rol.valor}
                              type="button"
                              className={`btn btn-outline-${rol.color} text-start ${
                                rolSeleccionado[cliente.usuario_id] === rol.valor
                                  ? `btn-${rol.color} active`
                                  : ""
                              }`}
                              onClick={() => cambiarRol(cliente.usuario_id, rol.valor)}
                              disabled={actualizando}
                            >
                              <i className={`${rol.icono} me-2`}></i>
                              {rol.nombre}
                              {rolSeleccionado[cliente.usuario_id] === rol.valor && (
                                <span className="ms-2">
                                  <i className="fas fa-check-circle"></i>
                                </span>
                              )}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Footer */}
                    <div className="card-footer bg-light text-muted small border-0">
                      <i className="fas fa-clock me-1"></i>
                      {new Date(cliente.fecha_creacion).toLocaleDateString("es-CL")}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Resumen */}
        <div className="row mt-5">
          <div className="col-12">
            <div className="card border-0 shadow-sm bg-white">
              <div className="card-body">
                <h5 className="card-title fw-bold text-primary mb-3">
                  <i className="fas fa-chart-pie"></i> Resumen de Roles
                </h5>
                <div className="row text-center">
                  {ROLES.map((rol) => {
                    const count = clientes.filter(
                      c => rolSeleccionado[c.usuario_id] === rol.valor
                    ).length;
                    return (
                      <div key={rol.valor} className="col-md-3 mb-3">
                        <div className={`bg-${rol.color} bg-opacity-10 p-3 rounded`} style={{ border: `2px solid var(--${rol.color}-color)` }}>
                          <h3 className={`text-${rol.color} fw-bold`} style={{ fontSize: '2.5rem', margin: '10px 0' }}>{count}</h3>
                          <p className={`text-${rol.color} small mb-0`} style={{ fontWeight: '600', opacity: '0.9' }}>{rol.nombre}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default GestionRoles;
