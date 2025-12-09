import React from 'react';

export default function TestPage() {
  return (
    <div style={{ padding: '40px', textAlign: 'center', backgroundColor: 'var(--light-bg)', minHeight: '100vh' }}>
      <h1>✅ React Está Funcionando</h1>
      <p>Si ves este mensaje, React se cargó correctamente.</p>
      <a href="/" style={{
        display: 'inline-block',
        marginTop: '20px',
        padding: '10px 20px',
        background: 'var(--primary-color)',
        color: 'white',
        textDecoration: 'none',
        borderRadius: '5px'
      }}>Ir a Home</a>
    </div>
  );
}
