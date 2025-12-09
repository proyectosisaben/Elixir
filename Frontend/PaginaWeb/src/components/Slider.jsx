import React, { useState, useEffect } from "react";
import "../styles/globals.css";
import { useRol } from "../contexts/RolContext";

function Slider() {
  const { usuario } = useRol();
  const [slides, setSlides] = useState([
    { id: 1, title: "🍷 Los Mejores Vinos Chilenos", description: "Selección premium de los valles más reconocidos de Chile. Envío rápido a domicilio.", imagen_url: "" },
    { id: 2, title: "🍺 Cervezas Artesanales", description: "Marcas exclusivas y artesanales. Desde Kunstmann hasta Heineken, ¡todas en Elixir!", imagen_url: "" },
    { id: 3, title: "🥃 Piscos y Destilados Premium", description: "Los mejores piscos, whiskys y rones para tus celebraciones. Calidad garantizada.", imagen_url: "" }
  ]);
  const [editando, setEditando] = useState(false);
  const [slideEditado, setSlideEditado] = useState(null);
  const [formData, setFormData] = useState({});

  useEffect(() => {
    // Cargar slides del backend
    const cargarSliders = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/sliders/');
        const data = await response.json();
        if (data.success && data.sliders) {
          setSlides(data.sliders);
        }
      } catch (error) {
        console.error('Error al cargar sliders:', error);
        // Si hay error, usar valores por defecto que ya están en estado
      }
    };
    
    cargarSliders();
  }, []);

  const handleEditarSlide = (slide) => {
    if (usuario?.rol !== 'vendedor' && usuario?.rol !== 'admin_sistema') return;
    setEditando(true);
    setSlideEditado(slide);
    setFormData({ ...slide });
  };

  const handleGuardar = async () => {
    if (!formData.title || !formData.description) {
      alert('Completa todos los campos');
      return;
    }
    
    try {
      // Obtener usuario del localStorage
      const usuarioJson = localStorage.getItem('usuario');
      const usuario = usuarioJson ? JSON.parse(usuarioJson) : null;
      
      const slidesActualizados = slides.map(s => s.id === slideEditado.id ? formData : s);
      
      // Enviar al backend
      const response = await fetch('http://localhost:8000/api/sliders/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          sliders: slidesActualizados,
          usuario_id: usuario?.id
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setSlides(slidesActualizados);
        setEditando(false);
        setSlideEditado(null);
        alert('Slide actualizado correctamente en la base de datos');
      } else {
        alert(`Error: ${data.message || 'No se pudo actualizar el slide'}`);
      }
    } catch (error) {
      console.error('Error al guardar slider:', error);
      alert('Error al guardar en la base de datos: ' + error.message);
    }
  };

  return (
    <>
      {editando && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '15px',
            maxWidth: '500px',
            width: '90%',
            boxShadow: 'var(--shadow-lg)'
          }}>
            <h3 style={{ color: 'var(--primary-color)' }}>Editar Slide</h3>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: 'var(--primary-color)' }}>Título:</label>
              <input
                type="text"
                value={formData.title || ''}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '2px solid var(--border-color)',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  boxSizing: 'border-box'
                }}
              />
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: 'var(--primary-color)' }}>Descripción:</label>
              <textarea
                value={formData.description || ''}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                rows="4"
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '2px solid var(--border-color)',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  fontFamily: 'inherit',
                  boxSizing: 'border-box'
                }}
              />
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: 'var(--primary-color)' }}>URL de Imagen:</label>
              <input
                type="text"
                value={formData.imagen_url || ''}
                onChange={(e) => setFormData({...formData, imagen_url: e.target.value})}
                placeholder="https://ejemplo.com/imagen.jpg"
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '2px solid var(--border-color)',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  boxSizing: 'border-box'
                }}
              />
            </div>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setEditando(false)}
                style={{
                  padding: '10px 20px',
                  backgroundColor: 'var(--muted-color)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: '600'
                }}
              >
                Cancelar
              </button>
              <button
                onClick={handleGuardar}
                style={{
                  padding: '10px 20px',
                  backgroundColor: 'var(--secondary-color)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: '600'
                }}
              >
                Guardar
              </button>
            </div>
          </div>
        </div>
      )}
      <div id="sliderElixir" className="carousel slide mb-5" data-bs-ride="carousel">
        <div className="carousel-inner">
          {slides.map((slide, index) => (
            <div key={slide.id} className={`carousel-item ${index === 0 ? 'active' : ''}`}>
              <div
                className="text-white p-5 text-center"
                style={{
                  minHeight: "300px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "center",
                  backgroundImage: slide.imagen_url ? `url(${slide.imagen_url})` : 'linear-gradient(135deg, var(--primary-color), var(--secondary-color))',
                  backgroundSize: 'cover',
                  backgroundPosition: 'center',
                  backgroundColor: 'var(--primary-color)',
                  cursor: (usuario?.rol === 'vendedor' || usuario?.rol === 'admin_sistema') ? 'pointer' : 'default',
                  transition: 'all 0.3s ease',
                  textShadow: '2px 2px 4px rgba(0,0,0,0.7)'
                }}
                onClick={() => handleEditarSlide(slide)}
              >
                <h3 className="mb-3 fw-bold">{slide.title}</h3>
                <p className="fs-5">{slide.description}</p>
                {(usuario?.rol === 'vendedor' || usuario?.rol === 'admin_sistema') && (
                  <p style={{ marginTop: '15px', fontSize: '0.9rem', opacity: 0.8 }}>
                    <i className="fas fa-edit"></i> Haz clic para editar
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
        <button className="carousel-control-prev" type="button" data-bs-target="#sliderElixir" data-bs-slide="prev">
          <span className="carousel-control-prev-icon"></span>
        </button>
        <button className="carousel-control-next" type="button" data-bs-target="#sliderElixir" data-bs-slide="next">
          <span className="carousel-control-next-icon"></span>
        </button>
      </div>
    </>
  );
}

export default Slider;
