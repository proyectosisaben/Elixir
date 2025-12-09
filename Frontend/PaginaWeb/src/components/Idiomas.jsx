import React from "react";

function Idiomas({ current, onIdiomaChange }) {
  return (
    <div className="d-flex align-items-center">
      <span className="me-2">Idioma:</span>
      <select value={current} onChange={e => onIdiomaChange(e.target.value)} className="form-select form-select-sm w-auto">
        <option value="es">Español</option>
        <option value="en">English</option>
      </select>
    </div>
  );
}

export default Idiomas;
