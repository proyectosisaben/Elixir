import React, { useState, useEffect } from "react";
import { useRol } from "../contexts/RolContext";
import { useNavigate } from "react-router-dom";
import "../styles/globals.css";
import {
  FaServer,
  FaUserShield,
  FaDatabase,
  FaShieldAlt,
  FaUsers,
  FaTools,
  FaChartPie,
  FaLock,
  FaSync,
  FaExclamationTriangle,
  FaBox,
} from "react-icons/fa";

function DashboardAdmin() {
  const { usuario } = useRol();
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalUsuarios: 0,
    totalClientes: 0,
    totalVendedores: 0,
    totalGerentes: 0,
    totalAdmin: 0,
    totalPedidos: 0,
    ventasTotales: 0,
  });
  const [usuarios, setUsuarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Verificar que el usuario sea admin
    if (usuario && usuario.rol !== "admin_sistema") {
      navigate("/dashboard-admin");
      return;
    }
    cargarDatos();
    
    // Recargar datos cada 30 segundos para actualizar ventas en tiempo real
    const intervalo = setInterval(cargarDatos, 30000);
    
    return () => clearInterval(intervalo);
  }, [usuario, navigate]);

  const cargarDatos = async () => {
    try {
      setLoading(true);

      // Obtener token para autenticación
      const token = localStorage.getItem('token');
      const headers = token ? { Authorization: `Token ${token}` } : {};

      // Obtener estadísticas del dashboard admin (endpoint específico)
      const statsResponse = await fetch(`${window.API_BASE_URL}/api/dashboard-admin/estadisticas/`, {
        headers: headers,
        credentials: 'include'
      });

      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        if (statsData.success && statsData.estadisticas) {
          const est = statsData.estadisticas;
          setStats({
            totalUsuarios: est.usuarios.total,
            totalClientes: est.usuarios.por_rol.cliente,
            totalVendedores: est.usuarios.por_rol.vendedor,
            totalGerentes: est.usuarios.por_rol.gerente,
            totalAdmin: est.usuarios.por_rol.admin_sistema,
            totalPedidos: est.ventas.total_pedidos,
            ventasTotales: est.ventas.total_ventas,
          });
        }
      } else {
        console.log('Error en respuesta de estadísticas:', statsResponse.status);
        // Fallback: obtener datos básicos
        await cargarDatosFallback();
      }

      // Obtener lista de clientes para gestión de roles
      const clientesResponse = await fetch(`${window.API_BASE_URL}/api/listar-clientes/`, {
        headers: headers,
        credentials: 'include'
      });
      const clientesData = clientesResponse.ok ? await clientesResponse.json() : null;

      if (clientesData && clientesData.clientes) {
        setUsuarios(clientesData.clientes);
      }

      setError(null);
    } catch (err) {
      console.error("Error cargando datos:", err);
      setError("Error al cargar datos del sistema");
      // Intentar fallback
      await cargarDatosFallback();
    } finally {
      setLoading(false);
    }
  };

  // Método fallback para obtener datos básicos si falla el endpoint principal
  const cargarDatosFallback = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { Authorization: `Token ${token}` } : {};

      // Obtener lista de clientes
      const clientesResponse = await fetch(`${window.API_BASE_URL}/api/listar-clientes/`, {
        headers: headers,
        credentials: 'include'
      });
      const clientesData = clientesResponse.ok ? await clientesResponse.json() : null;

      if (clientesData && clientesData.clientes) {
        const listaUsuarios = clientesData.clientes;
        setUsuarios(listaUsuarios);

        // Contar usuarios por rol
        const conteos = {
          cliente: 0,
          vendedor: 0,
          gerente: 0,
          admin_sistema: 0,
        };

        listaUsuarios.forEach(u => {
          const rol = u.rol || 'cliente';
          if (conteos.hasOwnProperty(rol)) {
            conteos[rol]++;
          }
        });

        // Obtener ventas si tenemos usuario
        let ventasTotales = 0;
        let totalPedidos = 0;

        if (usuario?.id) {
          try {
            const ventasResponse = await fetch(`${API_BASE_URL}/api/ventas-totales/?usuario_id=${usuario.id}`, {
              headers: headers,
              credentials: 'include'
            });
            if (ventasResponse.ok) {
              const ventasData = await ventasResponse.json();
              if (ventasData.success && ventasData.ventas) {
                ventasTotales = ventasData.ventas.total_ventas || 0;
                totalPedidos = ventasData.ventas.total_pedidos || 0;
              }
            }
          } catch (err) {
            console.log('Error cargando ventas totales:', err);
          }
        }

        setStats({
          totalUsuarios: listaUsuarios.length,
          totalClientes: conteos.cliente,
          totalVendedores: conteos.vendedor,
          totalGerentes: conteos.gerente,
          totalAdmin: conteos.admin_sistema,
          totalPedidos: totalPedidos,
          ventasTotales: ventasTotales,
        });
      }
    } catch (err) {
      console.error("Error en fallback:", err);
    }
  };

  const handleBackup = async () => {
    if (window.confirm("¿Estás seguro de que deseas hacer un backup de la base de datos?\n\nEsto puede tomar algunos minutos.")) {
      try {
        const response = await fetch(`${window.API_BASE_URL}/api/backup-sistema/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" }
        });
        
        const data = await response.json();
        
        if (response.ok) {
          alert("✓ Backup realizado exitosamente\n\nArchivo guardado en el servidor");
        } else {
          alert(`Error: ${data.message || 'No se pudo completar el backup'}`);
        }
      } catch (err) {
        alert(`Error al hacer backup: ${err.message}`);
      }
    }
  };

  const handleSeguridad = () => {
    const mensaje = `
CONFIGURACIÓN DE SEGURIDAD DEL SISTEMA

Estado actual:
✓ Autenticación habilitada
✓ Conexión HTTPS (en producción)
✓ Validación de permisos activa
✓ Logs de sistema registrados

Opciones disponibles:
1. Ver logs de seguridad
2. Gestionar sesiones activas
3. Configurar 2FA
4. Auditoría de acceso

Selecciona una opción o cancela.
    `.trim();
    
    const opcion = prompt(mensaje);
    if (opcion === "1") {
      alert("Función de logs disponible en próximas actualizaciones");
    } else if (opcion === "2") {
      alert("Hay 1 sesión activa del administrador actual");
    } else if (opcion === "3") {
      alert("2FA disponible en próximas actualizaciones");
    } else if (opcion === "4") {
      alert("Auditoría disponible en próximas actualizaciones");
    }
  };

  if (loading) {
    return (
      <div className="dashboard-admin-container">
        <div className="loading">
          <p>Cargando panel de administración...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-admin-container">
        <div className="alertas-section">
          <h2><FaExclamationTriangle /> Error</h2>
          <p>{error}</p>
          <button onClick={cargarDatos} className="btn btn-primary">Reintentar</button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-admin-container">
      {/* Header */}
      <div className="gerente-header">
        <div className="gerente-header-content">
          <div className="gerente-welcome">
            <FaUserShield className="header-icon" />
            <div>
              <h1>Panel de Administrador del Sistema</h1>
              <p>Control total del sistema, usuarios, ventas y base de datos</p>
            </div>
          </div>
        </div>
      </div>

      <div className="gerente-main-container">
        {/* Metricas Principales */}
        <div className="metricas-grid">
          <div className="metrica-card ventas-totales">
            <div className="metrica-header">
              <h3>Usuarios Totales</h3>
              <FaUsers className="metrica-icon" />
            </div>
            <p className="metrica-valor">{stats.totalUsuarios}</p>
            <p className="metrica-periodo">Registrados en el sistema</p>
            <div className="metrica-bar">
              <div className="bar-fill" style={{ width: "85%", transition: "width 0.8s ease" }}></div>
            </div>
          </div>

          <div className="metrica-card productos-total">
            <div className="metrica-header">
              <h3>Pedidos Totales</h3>
              <FaChartPie className="metrica-icon" />
            </div>
            <p className="metrica-valor">{stats.totalPedidos}</p>
            <p className="metrica-periodo">Órdenes procesadas</p>
            <div className="metrica-bar">
              <div className="bar-fill" style={{ width: "60%", transition: "width 0.8s ease" }}></div>
            </div>
          </div>

          <div className="metrica-card clientes">
            <div className="metrica-header">
              <h3>Ventas Totales</h3>
              <FaDatabase className="metrica-icon" />
            </div>
            <p className="metrica-valor">${stats.ventasTotales.toLocaleString('es-CL')}</p>
            <p className="metrica-periodo">Ingresos acumulados</p>
            <div className="metrica-bar">
              <div className="bar-fill" style={{ width: "45%", transition: "width 0.8s ease" }}></div>
            </div>
          </div>

          <div className="metrica-card margen">
            <div className="metrica-header">
              <h3>Estado Sistema</h3>
              <FaServer className="metrica-icon" />
            </div>
            <p className="metrica-valor">✓ Online</p>
            <p className="metrica-periodo">Funcionando normalmente</p>
            <div className="metrica-bar">
              <div className="bar-fill" style={{ width: "100%", transition: "width 0.8s ease" }}></div>
            </div>
          </div>
        </div>

        {/* Distribución de Roles */}
        <div className="productos-section">
          <h2>
            <FaUserShield /> Distribución de Usuarios por Rol
          </h2>
          <div className="productos-table">
            <table>
              <thead>
                <tr>
                  <th>Rol</th>
                  <th>Cantidad</th>
                  <th>Porcentaje</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Clientes</strong></td>
                  <td>{stats.totalClientes}</td>
                  <td>{stats.totalUsuarios > 0 ? ((stats.totalClientes / stats.totalUsuarios) * 100).toFixed(1) : 0}%</td>
                  <td><span style={{ background: 'rgba(72, 187, 120, 0.1)', color: 'var(--success-color)', padding: '4px 8px', borderRadius: '4px', fontWeight: 'bold' }}>Activo</span></td>
                </tr>
                <tr>
                  <td><strong>Vendedores</strong></td>
                  <td>{stats.totalVendedores}</td>
                  <td>{stats.totalUsuarios > 0 ? ((stats.totalVendedores / stats.totalUsuarios) * 100).toFixed(1) : 0}%</td>
                  <td><span style={{ background: 'rgba(72, 187, 120, 0.1)', color: 'var(--success-color)', padding: '4px 8px', borderRadius: '4px', fontWeight: 'bold' }}>Activo</span></td>
                </tr>
                <tr>
                  <td><strong>Gerentes</strong></td>
                  <td>{stats.totalGerentes}</td>
                  <td>{stats.totalUsuarios > 0 ? ((stats.totalGerentes / stats.totalUsuarios) * 100).toFixed(1) : 0}%</td>
                  <td><span style={{ background: 'rgba(72, 187, 120, 0.1)', color: 'var(--success-color)', padding: '4px 8px', borderRadius: '4px', fontWeight: 'bold' }}>Activo</span></td>
                </tr>
                <tr>
                  <td><strong>Administradores</strong></td>
                  <td>{stats.totalAdmin}</td>
                  <td>{stats.totalUsuarios > 0 ? ((stats.totalAdmin / stats.totalUsuarios) * 100).toFixed(1) : 0}%</td>
                  <td><span style={{ background: 'rgba(245, 101, 101, 0.1)', color: 'var(--danger-color)', padding: '4px 8px', borderRadius: '4px', fontWeight: 'bold' }}>Crítico</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Botones de Administración */}
        <div className="productos-section">
          <h2>
            <FaTools /> Herramientas Administrativas
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
            <button 
              onClick={() => navigate('/admin/roles')}
              style={{
                padding: '20px',
                borderRadius: '10px',
                border: 'none',
                background: 'var(--primary-color)',
                color: 'white',
                fontWeight: 'bold',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={(e) => e.target.style.transform = 'translateY(-3px)'}
              onMouseLeave={(e) => e.target.style.transform = 'translateY(0)'}
            >
              <FaLock style={{ marginRight: '10px' }} />
              Gestionar Roles
            </button>
            <button 
              onClick={() => navigate('/dashboard-vendedor')}
              style={{
                padding: '20px',
                borderRadius: '10px',
                border: 'none',
                background: '#2ecc71',
                color: 'white',
                fontWeight: 'bold',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={(e) => e.target.style.transform = 'translateY(-3px)'}
              onMouseLeave={(e) => e.target.style.transform = 'translateY(0)'}
            >
              <FaBox style={{ marginRight: '10px' }} />
              Crear Bebida
            </button>
            <button 
              onClick={cargarDatos}
              style={{
                padding: '20px',
                borderRadius: '10px',
                border: 'none',
                background: 'var(--success-color)',
                color: 'white',
                fontWeight: 'bold',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={(e) => e.target.style.transform = 'translateY(-3px)'}
              onMouseLeave={(e) => e.target.style.transform = 'translateY(0)'}
            >
              <FaSync style={{ marginRight: '10px' }} />
              Recargar Datos
            </button>
            <button 
              onClick={handleBackup}
              style={{
                padding: '20px',
                borderRadius: '10px',
                border: 'none',
                background: 'var(--warning-color)',
                color: 'white',
                fontWeight: 'bold',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={(e) => e.target.style.transform = 'translateY(-3px)'}
              onMouseLeave={(e) => e.target.style.transform = 'translateY(0)'}
            >
              <FaDatabase style={{ marginRight: '10px' }} />
              Backup Sistema
            </button>
            <button
              onClick={() => navigate('/monitoreo-sistema')}
              style={{
                padding: '20px',
                borderRadius: '10px',
                border: 'none',
                background: '#17a2b8',
                color: 'white',
                fontWeight: 'bold',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={(e) => e.target.style.transform = 'translateY(-3px)'}
              onMouseLeave={(e) => e.target.style.transform = 'translateY(0)'}
            >
              <FaServer style={{ marginRight: '10px' }} />
              Monitoreo Sistema
            </button>
            <button
              onClick={handleSeguridad}
              style={{
                padding: '20px',
                borderRadius: '10px',
                border: 'none',
                background: 'var(--secondary-color)',
                color: 'white',
                fontWeight: 'bold',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
              }}
              onMouseEnter={(e) => e.target.style.transform = 'translateY(-3px)'}
              onMouseLeave={(e) => e.target.style.transform = 'translateY(0)'}
            >
              <FaShieldAlt style={{ marginRight: '10px' }} />
              Seguridad
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DashboardAdmin;
