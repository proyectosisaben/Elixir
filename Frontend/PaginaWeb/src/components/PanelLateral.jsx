import React from "react";

function PanelLateral({ categorias, onFiltrarCategoria, selected }) {
  return (
    <aside className="bg-white border rounded p-3 mb-4 shadow-sm">
      <h5 className="fw-bold text-primary mb-3"><i className="fas fa-filter"></i> Categorías</h5>
      <ul className="list-group">
        {categorias.map(cat => (
          <li key={cat.id} className={`list-group-item ${selected === cat.id ? 'active' : ''}`}
              style={{ cursor: "pointer" }}
              onClick={() => onFiltrarCategoria(cat.id)}>
            <i className="fas fa-wine-bottle"></i> {cat.nombre}
          </li>
        ))}
        <li className={`list-group-item ${!selected ? 'active' : ''}`} style={{ cursor: "pointer" }} onClick={() => onFiltrarCategoria(null)}>
          <i className="fas fa-list"></i> Todos los productos
        </li>
      </ul>
    </aside>
  );
}

export default PanelLateral;
