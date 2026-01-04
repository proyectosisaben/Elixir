import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { RolProvider } from './contexts/RolContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { ConnectivityWarning } from './utils/connectivity.jsx';
import { RoleChangeNotification } from './components/RoleChangeNotification';
import Header from './components/Header';
import Footer from './components/Footer';
import Blog from './pages/Blog';
import Home from './pages/Home';
import CatalogoPorCategoria from './pages/CatalogoPorCategoria';
import AtencionCliente from './pages/AtencionCliente';
import InicioRegistro from './pages/InicioRegistro';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import TestPage from './pages/TestPage';
import Carrito from './pages/Carrito';
import DetalleProducto from './pages/DetalleProducto';
import GestionRoles from './pages/GestionRoles';
import GestionPerfil from './pages/GestionPerfil';
import Checkout from './pages/Checkout';
import ConfirmacionPago from './pages/ConfirmacionPago';
import ConfirmacionPagoDetalle from './pages/ConfirmacionPagoDetalle';
import Auditoria from './pages/Auditoria';
import AnalisisVentas from './pages/AnalisisVentas';
import MonitoreoSistema from './pages/MonitoreoSistema';
import AutorizacionesVendedor from './pages/AutorizacionesVendedor';
import AutorizacionesGerente from './pages/AutorizacionesGerente';
import DetalleCliente from './pages/DetalleCliente';
import GestionCupones from './pages/GestionCupones';
import GestionReclamos from './pages/GestionReclamos';
import POS from './pages/POS';

// Lazy load de dashboards nuevos (cargar bajo demanda)
const DashboardVendedor = React.lazy(() => import('./pages/DashboardVendedor'));
const DashboardAdmin = React.lazy(() => import('./pages/DashboardAdmin'));

function App() {
  return (
    <RolProvider>
      <ConnectivityWarning />
      <RoleChangeNotification />
      <Header />
      <main>
        <React.Suspense fallback={<div style={{padding: '20px', textAlign: 'center'}}>Cargando...</div>}>
          <Routes>
            <Route path='/test' element={<TestPage />} />
            <Route path='/' element={<Home />} />
            <Route path='/catalogo' element={<CatalogoPorCategoria />} />
            <Route path='/producto/:id' element={<DetalleProducto />} />
            <Route path='/registro' element={<InicioRegistro />} />
            <Route path='/login' element={<Login />} />
            
            {/* Rutas protegidas - Clientes */}
            <Route path='/carrito' element={<ProtectedRoute element={<Carrito />} requiredRoles={['cliente', 'vendedor', 'gerente', 'admin_sistema']} />} />
            <Route path='/checkout' element={<ProtectedRoute element={<Checkout />} requiredRoles={['cliente', 'vendedor', 'gerente', 'admin_sistema']} />} />
            <Route path='/confirmacion-pago' element={<ProtectedRoute element={<ConfirmacionPago />} requiredRoles={['cliente', 'vendedor', 'gerente', 'admin_sistema']} />} />
            <Route path='/confirmacion-pago-detalle' element={<ProtectedRoute element={<ConfirmacionPagoDetalle />} requiredRoles={['cliente', 'vendedor', 'gerente', 'admin_sistema']} />} />
            <Route path='/perfil' element={<ProtectedRoute element={<GestionPerfil />} requiredRoles={['cliente', 'vendedor', 'gerente', 'admin_sistema']} />} />
            
            {/* Dashboard por Rol */}
            <Route path='/dashboard' element={<ProtectedRoute element={<Dashboard />} requiredRoles={['vendedor', 'gerente', 'admin_sistema']} />} />
            <Route path='/dashboard-cliente' element={<ProtectedRoute element={<GestionPerfil />} requiredRoles={['cliente']} />} />
            <Route path='/dashboard-vendedor' element={<ProtectedRoute element={<DashboardVendedor />} requiredRoles={['vendedor']} />} />
            <Route path='/dashboard-admin' element={<ProtectedRoute element={<DashboardAdmin />} requiredRoles={['admin_sistema']} />} />

            {/* Ruta temporal sin protección para testing */}
            <Route path='/dashboard-admin-test' element={<DashboardAdmin />} />
            
            {/* Rutas protegidas - Admin */}
            <Route path='/admin/roles' element={<ProtectedRoute element={<GestionRoles />} requiredRoles={['admin_sistema']} />} />
            <Route path='/auditoria' element={<ProtectedRoute element={<Auditoria />} requiredRoles={['gerente', 'admin_sistema']} />} />
            <Route path='/analisis-ventas' element={<ProtectedRoute element={<AnalisisVentas />} requiredRoles={['gerente', 'admin_sistema']} />} />
            <Route path='/monitoreo-sistema' element={<ProtectedRoute element={<MonitoreoSistema />} requiredRoles={['admin_sistema']} />} />
            <Route path='/cupones' element={<ProtectedRoute element={<GestionCupones />} requiredRoles={['gerente', 'admin_sistema']} />} />
            <Route path='/reclamos' element={<ProtectedRoute element={<GestionReclamos />} requiredRoles={['cliente', 'vendedor', 'gerente', 'admin_sistema']} />} />
            <Route path='/pos' element={<ProtectedRoute element={<POS />} requiredRoles={['vendedor', 'gerente', 'admin_sistema']} />} />

            {/* Rutas de Autorizaciones - HU 50 */}
            <Route path='/autorizaciones/vendedor' element={<ProtectedRoute element={<AutorizacionesVendedor />} requiredRoles={['vendedor']} />} />
            <Route path='/autorizaciones/gerente' element={<ProtectedRoute element={<AutorizacionesGerente />} requiredRoles={['gerente', 'admin_sistema']} />} />

            {/* Rutas de Clientes - HU 23 */}
            <Route path='/clientes/:clienteId' element={<ProtectedRoute element={<DetalleCliente />} requiredRoles={['vendedor', 'gerente', 'admin_sistema']} />} />

            {/* Rutas públicas */}
            <Route path='/blog' element={<Blog />} />
            <Route path='/atencion_cliente' element={<AtencionCliente />} />
          </Routes>
        </React.Suspense>
      </main>
      <Footer />
    </RolProvider>
  );
}

export default App;


