import React, { useState, useEffect } from "react";
import Slider from "../components/Slider";
import { useNavigate } from "react-router-dom";
import "../styles/globals.css";

function Home() {
  const navigate = useNavigate();
  const [carrito, setCarrito] = useState(() => {
    const saved = localStorage.getItem('carrito');
    return saved ? JSON.parse(saved) : [];
  });

  return (
    <div>
      <Slider />
      <section className="container py-5">
        <h1 className="display-4 fw-bold mb-4 text-center text-primary">
          Bienvenido a Elixir
        </h1>
        <p className="lead text-center mb-5">
          Tu botillería premium online. Los mejores vinos, cervezas y destilados a un solo clic, con envío rápido y seguro.
        </p>
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <button 
            onClick={() => navigate('/catalogo')}
            className="btn btn-primary btn-lg"
          >
            <i className="fas fa-shopping-cart"></i> Ver Catálogo Completo
          </button>
        </div>
      </section>

      <section style={{ backgroundColor: 'var(--light-bg)', padding: '60px 0' }}>
        <div className="container">
          <h2 className="fw-bold mb-4 text-center text-primary">
            ¿Por qué elegirnos?
          </h2>
          <div className="row g-4">
            <div className="col-md-4 text-center">
              <i className="fas fa-shipping-fast fs-1 text-primary mb-3"></i>
              <h5>Envío Rápido</h5>
              <p>Entrega en 24-48 horas en toda la región metropolitana</p>
            </div>
            <div className="col-md-4 text-center">
              <i className="fas fa-lock fs-1 text-primary mb-3"></i>
              <h5>Compra Segura</h5>
              <p>Transacciones encriptadas y protegidas con los mejores estándares</p>
            </div>
            <div className="col-md-4 text-center">
              <i className="fas fa-headset fs-1 text-primary mb-3"></i>
              <h5>Soporte 24/7</h5>
              <p>Nuestro equipo siempre disponible para ayudarte</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Home;
