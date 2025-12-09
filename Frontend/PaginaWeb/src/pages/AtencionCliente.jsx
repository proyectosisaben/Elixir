import React from "react";
import "../styles/globals.css";

function AtencionCliente() {
  return (
    <div className="container py-5">
      <h2 className="fw-bold text-primary mb-4 text-center">
        <i className="fas fa-headset"></i> Atención al Cliente Elixir
      </h2>
      <div className="row justify-content-center">
        <div className="col-md-8 text-center">
          <p className="lead mb-4">
            ¿Tienes consultas sobre tu compra, entrega, métodos de pago o productos? Nuestro equipo está listo para ayudarte.
          </p>
          <ul className="list-unstyled mb-4">
            <li><i className="fas fa-wine-bottle text-warning"></i> Dudas sobre cervezas, vinos y licores</li>
            <li><i className="fas fa-truck text-info"></i> Problemas o dudas de despacho</li>
            <li><i className="fas fa-user text-success"></i> Soporte post-venta personalizado</li>
          </ul>
          <a href="https://wa.me/56999999999" className="btn btn-primary btn-lg" target="_blank" rel="noopener noreferrer">
            <i className="fab fa-whatsapp"></i> Contáctanos por WhatsApp
          </a>
        </div>
      </div>
    </div>
  );
}

export default AtencionCliente;
