import React from 'react';
import { FaDollarSign } from "react-icons/fa6";
import { IoHomeSharp } from "react-icons/io5";
import { FaFileInvoiceDollar } from "react-icons/fa";
import { FaBoxesPacking } from "react-icons/fa6";
import { IoMdAnalytics } from "react-icons/io";
import { FaArrowRight } from "react-icons/fa";
import { FaArrowLeft } from "react-icons/fa";
import '../styles/contenidodashboard.css';
import { Link } from 'react-router-dom';

function ContenidoDashboard() {
  return (
    <main className='seccion-panel-lateral-tarjetas-seguimiento-de-compras'>
      <div className='todo-el-contenido-de-la-dashboard'>
        
        {/* PANEL LATERAL */}
        <section className='todo-contenido-panel-lateral'>
          <div className='primera-seccion-panel-lateral'>
            <div className='contenedor-logo-panel-lateral'>
              <img src='LogoEcommerce Dashboard.jpg' alt='logo' className='estilo-logo-panel-lateral' />
              <h1 className='titulo-panel-lateral-logo'>Ecommerce TodoCarros</h1>
            </div>
          </div>
          <div className='raya-panel-lateral'></div>
          <div className='contenedor-parte-2-dashboard'>
            <div className='panel-lateral-interior-titulos'>
              <div className='contenedor-panel-lateral-interior-y-icono'>
                <IoHomeSharp className='icono-parte-lateral-interior' />
                <h1 className='titulo-panel-lateral-interior'>Dashboard</h1>
              </div>
              <div className='contenedor-panel-lateral-interior-y-icono'>
                <FaFileInvoiceDollar className='icono-parte-lateral-interior' />
                <h1 className='titulo-panel-lateral-interior'><Link to='/generar_facturas'>Generar facturas</Link></h1>
              </div>
              <div className='contenedor-panel-lateral-interior-y-icono'>
                <FaBoxesPacking className='icono-parte-lateral-interior' />
                <h1 className='titulo-panel-lateral-interior'>Añadir productos</h1>
              </div>
              <div className='contenedor-panel-lateral-interior-y-icono'>
                <IoMdAnalytics className='icono-parte-lateral-interior' />
                <h1 className='titulo-panel-lateral-interior'>Analítica y datos</h1>
              </div>
            </div>
            <div className='contenedor-parte-inferior-panel-lateral'>
              <p className='parrafo-parte-inferior-panel-lateral'>¿Le gustó nuestro Ecommerce?</p>
              <p className='parrafo-parte-inferior-panel-lateral-2'>Contactenos <span><FaArrowRight className='icono-flecha-verde-panel-interior-dashboard'/></span></p>
            </div> 
          </div>
        </section>

        {/* TARJETAS DE INGRESO POR FECHAS */}
        <section className='todo-contenido-tarjetas-ingreso-dashboard'>
          <div className='contenedor-interno-contenido-tarjetas-ingreso-dashboard'>
            <h1 className='titulo-para-dashboard-inicio'>Dashboard Ecommerce TodoCarros.</h1>
            <h2 className='descripcion-para-dashboard'>Bienvenidos a la Dashboard del Ecommerce de TodoCarros.</h2>
            <div className='contenedor-tres-tarjetas-ingreso-dashboard'>
              <div className='contenedor-tarjeta-general-ingreso-dashboard'>
                <h3 className='titulo-ingresos-tarjeta'>Ingresos por día</h3>
                <div className='contenedor-precio-ingreso-dashboard'>
                  <FaDollarSign className='estilos-signo-peso-dashboard-1'/>
                  <h1 className='valor-ingreso-dashboard'> 1.000.000 <FaDollarSign className='estilos-signo-peso-dashboard-2' /></h1>
                </div>
                <h3 className='descripcion-año-dashboard'>Año 2020</h3>
                <div className='contenedor-olas-tarjeta'>
                  <img src='wave.png' alt='wave' className='estilos-onda-tarjeta-ingresos' />
                </div>
              </div>
              <div className='contenedor-tarjeta-general-ingreso-dashboard-2'>
                <h3 className='titulo-ingresos-tarjeta'>Ingresos por mes</h3>
                <div className='contenedor-precio-ingreso-dashboard'>
                  <FaDollarSign className='estilos-signo-peso-dashboard-1'/>
                  <h1 className='valor-ingreso-dashboard'> 20.000.000 <FaDollarSign className='estilos-signo-peso-dashboard-2' /></h1>
                </div>
                <h3 className='descripcion-año-dashboard'>Año 2020</h3>
                <div className='contenedor-olas-tarjeta'>
                  <img src='wave.png' alt='wave' className='estilos-onda-tarjeta-ingresos' />
                </div>
              </div>
              <div className='contenedor-tarjeta-general-ingreso-dashboard-3'>
                <h3 className='titulo-ingresos-tarjeta'>Ingresos por año</h3>
                <div className='contenedor-precio-ingreso-dashboard'>
                  <FaDollarSign className='estilos-signo-peso-dashboard-1'/>
                  <h1 className='valor-ingreso-dashboard'> 350.000.000 <FaDollarSign className='estilos-signo-peso-dashboard-2' /></h1>
                </div>
                <h3 className='descripcion-año-dashboard'>Año 2020</h3>
                <div className='contenedor-olas-tarjeta'>
                  <img src='wave.png' alt='wave' className='estilos-onda-tarjeta-ingresos' />
                </div>
              </div>
            </div>
          </div>
          {/* SEGUIMIENTO DE VENTAS DE LOS USUARIOS */}
          <div className='seccion-seguimiento-compras'>
            <div className='contenido-seguimiento-compras'>
              <h1 className='titulo-seguimiento-ventas'>Seguimiento de las ventas</h1>
              <div className='contenedor-seguimiento-compras-usuarios'>
                <img src='Profesional1.jpg' alt='' className='estilos-logos-usuario-compra' />
                <h3 className='nombre-usuario-compra'>Alan John</h3>
                <h3 className='fecha-usuario-compra'>10/12/2023</h3>
                <h3 className='cantidad-productos-usuario-compra'>5 Productos</h3>
                <h3 className='estado-confirmado-rechazado'>Confirmado</h3>
                <div className='valor-compra-y-icono-peso'>
                  <h3 className='valor-compra-usuario-compra'><FaDollarSign className='estilos-valor-compra' /> 350.000</h3>
                </div>
              </div>
              <div className='contenedor-seguimiento-compras-usuarios'>
                <img src='Foto de Hoja de Vida.jpeg' alt='' className='estilos-logos-usuario-compra' />
                <h3 className='nombre-usuario-compra'>Jonathan Fernandez</h3>
                <h3 className='fecha-usuario-compra'>1/06/2022</h3>
                <h3 className='cantidad-productos-usuario-compra'>10 Productos</h3>
                <h3 className='estado-confirmado-rechazado'>Confirmado</h3>
                <div className='valor-compra-y-icono-peso'>
                  <h3 className='valor-compra-usuario-compra'><FaDollarSign className='estilos-valor-compra' /> 1.200.000</h3>
                </div>
              </div>
              <div className='contenedor-seguimiento-compras-usuarios'>
                <img src='Adolfo Betin.jpeg' alt='' className='estilos-logos-usuario-compra' />
                <h3 className='nombre-usuario-compra'>Adolfo Betin</h3>
                <h3 className='fecha-usuario-compra'>21/11/2023</h3>
                <h3 className='cantidad-productos-usuario-compra'>3 Productos</h3>
                <h3 className='estado-confirmado-rechazado'>Confirmado</h3>
                <div className='valor-compra-y-icono-peso'>
                  <h3 className='valor-compra-usuario-compra'><FaDollarSign className='estilos-valor-compra' /> 180.000</h3>
                </div>
              </div>
              <div className='contenedor-seguimiento-compras-usuarios'>
                <img src='Profesional2.jpg' alt='' className='estilos-logos-usuario-compra' />
                <h3 className='nombre-usuario-compra'>Martina Cortina</h3>
                <h3 className='fecha-usuario-compra'>10/12/2023</h3>
                <h3 className='cantidad-productos-usuario-compra'>9 Productos</h3>
                <h3 className='estado-confirmado-rechazado'>Confirmado</h3>
                <div className='valor-compra-y-icono-peso'>
                  <h3 className='valor-compra-usuario-compra'><FaDollarSign className='estilos-valor-compra' /> 270.000</h3>
                </div>
              </div>
              <div className='contenedor-seguimiento-compras-usuarios'>
                <img src='Profesional3.jpg' alt='' className='estilos-logos-usuario-compra' />
                <h3 className='nombre-usuario-compra'>Augusto Alfonso</h3>
                <h3 className='fecha-usuario-compra'>10/12/2023</h3>
                <h3 className='cantidad-productos-usuario-compra'>5 Productos</h3>
                <h3 className='estado-confirmado-rechazado'>Confirmado</h3>
                <div className='valor-compra-y-icono-peso'>
                  <h3 className='valor-compra-usuario-compra'><FaDollarSign className='estilos-valor-compra' /> 350.000</h3>
                </div>
              </div>
              <div className='div-iconos-ingresos-dashboard'>
                <FaArrowLeft />
                <FaArrowRight />
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}

export default ContenidoDashboard;
