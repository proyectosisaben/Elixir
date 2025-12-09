import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx'

// Importar estilos en orden correcto
import './styles/globals.css'


// Ese "root" es el id de un div del html.
const root = ReactDOM.createRoot(document.getElementById('root'));

root.render (
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
)
