import React from "react";

function ContenidoAtencionCliente() {
  return (
    <section className="py-5 bg-light">
      <div className="container">
        <div className="row justify-content-center">
          <div className="col-lg-8 text-center">
            <h2 className="fw-bold text-primary mb-4">
              <i className="fas fa-headset"></i> Atención al Cliente Elixir
            </h2>
            <p className="lead mb-4">
              ¿Tienes dudas, necesitas ayuda con tu compra, despacho o productos? Nuestro equipo está listo para atenderte, ¡escríbenos por WhatsApp o por el formulario de contacto!
            </p>
            <ul className="list-unstyled mb-4">
              <li><i className="fas fa-wine-bottle text-warning"></i> Consulta por disponibilidad de vinos y promos</li>
              <li><i className="fas fa-truck text-info"></i> Dudas de entrega a domicilio en Santiago y regiones</li>
              <li><i className="fas fa-user text-success"></i> Atención personalizada</li>
            </ul>
            <a href="/contacto" className="btn btn-primary btn-lg">
              <i className="fab fa-whatsapp"></i> Contáctanos
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

export default ContenidoAtencionCliente;
