import React from "react";
import "../styles/globals.css";

function Footer() {
  return (
    <footer style={{ backgroundColor: "var(--primary-color)", color: "white", marginTop: "auto", paddingTop: "40px", paddingBottom: "20px" }}>
      <div className="container">
        <div className="row mb-5">
          {/* Sección Elixir */}
          <div className="col-md-3 mb-4 mb-md-0">
            <h5 className="fw-bold mb-3" style={{ color: "var(--secondary-color)" }}>
              <i className="fas fa-wine-bottle"></i> Elixir
            </h5>
            <p style={{ color: "var(--muted-color)", fontSize: "0.9rem" }}>
              Tu botillería premium de confianza. Los mejores productos alcohólicos con garantía de calidad.
            </p>
          </div>

          {/* Sección Contacto */}
          <div className="col-md-3 mb-4 mb-md-0">
            <h6 className="fw-bold mb-3">Contacto</h6>
            <p style={{ fontSize: "0.9rem", marginBottom: "8px" }}>
              <i className="fas fa-map-marker-alt" style={{ marginRight: "8px" }}></i>
              Av. Providencia 1234, Santiago
            </p>
            <p style={{ fontSize: "0.9rem", marginBottom: "8px" }}>
              <i className="fas fa-phone" style={{ marginRight: "8px" }}></i>
              +56 2 2345 6789
            </p>
            <p style={{ fontSize: "0.9rem", marginBottom: "8px" }}>
              <i className="fas fa-envelope" style={{ marginRight: "8px" }}></i>
              <a href="mailto:contacto@elixir.cl" style={{ color: "var(--secondary-color)", textDecoration: "none" }}>
                contacto@elixir.cl
              </a>
            </p>
            <p style={{ fontSize: "0.9rem" }}>
              <i className="fab fa-whatsapp" style={{ marginRight: "8px", color: "#25D366" }}></i>
              <a href="https://wa.me/56987654321" style={{ color: "var(--secondary-color)", textDecoration: "none" }} target="_blank" rel="noopener noreferrer">
                +56 9 8765 4321
              </a>
            </p>
          </div>

          {/* Sección Horarios */}
          <div className="col-md-3 mb-4 mb-md-0">
            <h6 className="fw-bold mb-3">Horarios de Atención</h6>
            <p style={{ fontSize: "0.9rem", marginBottom: "5px" }}>
              <strong>Lunes a Viernes:</strong> 9:00 - 21:00
            </p>
            <p style={{ fontSize: "0.9rem", marginBottom: "5px" }}>
              <strong>Sábados:</strong> 9:00 - 20:00
            </p>
            <p style={{ fontSize: "0.9rem", marginBottom: "15px" }}>
              <strong>Domingos:</strong> 10:00 - 18:00
            </p>
            <p style={{ fontSize: "0.85rem", color: "var(--secondary-color)", fontWeight: "bold" }}>
              <i className="fas fa-truck" style={{ marginRight: "5px" }}></i>
              Despacho gratis sobre $25.000
            </p>
          </div>

          {/* Sección Redes Sociales */}
          <div className="col-md-3 mb-4 mb-md-0">
            <h6 className="fw-bold mb-3">Síguenos</h6>
            <div style={{ display: "flex", gap: "15px", marginBottom: "20px" }}>
              <a 
                href="https://facebook.com" 
                target="_blank" 
                rel="noopener noreferrer"
                style={{ 
                  color: "white", 
                  fontSize: "1.5rem",
                  transition: "color 0.3s ease"
                }}
                className="social-link"
              >
                <i className="fab fa-facebook"></i>
              </a>
              <a 
                href="https://instagram.com" 
                target="_blank" 
                rel="noopener noreferrer"
                style={{ 
                  color: "white", 
                  fontSize: "1.5rem",
                  transition: "color 0.3s ease"
                }}
                className="social-link"
              >
                <i className="fab fa-instagram"></i>
              </a>
              <a 
                href="https://twitter.com" 
                target="_blank" 
                rel="noopener noreferrer"
                style={{ 
                  color: "white", 
                  fontSize: "1.5rem",
                  transition: "color 0.3s ease"
                }}
                className="social-link"
              >
                <i className="fab fa-twitter"></i>
              </a>
              <a 
                href="https://wa.me/56987654321" 
                target="_blank" 
                rel="noopener noreferrer"
                style={{ 
                  color: "#25D366", 
                  fontSize: "1.5rem",
                  transition: "color 0.3s ease"
                }}
                className="social-link"
              >
                <i className="fab fa-whatsapp"></i>
              </a>
            </div>
          </div>
        </div>

        {/* Línea divisoria */}
        <hr style={{ borderColor: "rgba(255, 255, 255, 0.1)", margin: "30px 0" }} />

        {/* Footer inferior */}
        <div className="row align-items-center">
          <div className="col-md-6 text-center text-md-start mb-3 mb-md-0">
            <p style={{ fontSize: "0.85rem", color: "var(--muted-color)", marginBottom: "5px" }}>
              © 2025 Elixir - Botillería Premium. Todos los derechos reservados.
            </p>
            <p style={{ fontSize: "0.8rem", color: "var(--muted-color)" }}>
              Consumo responsable - Solo para mayores de 18 años | RUT: 76.123.456-7
            </p>
          </div>
          <div className="col-md-6 text-center text-md-end">
            <a href="#" style={{ color: "var(--secondary-color)", textDecoration: "none", fontSize: "0.85rem", marginRight: "15px" }}>
              Política de Privacidad
            </a>
            <a href="#" style={{ color: "var(--secondary-color)", textDecoration: "none", fontSize: "0.85rem", marginRight: "15px" }}>
              Términos y Condiciones
            </a>
            <a href="#" style={{ color: "var(--secondary-color)", textDecoration: "none", fontSize: "0.85rem" }}>
              Preguntas Frecuentes
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
