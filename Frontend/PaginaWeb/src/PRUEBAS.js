/**
 * GUÍA RÁPIDA DE PRUEBAS - Elixir Botillería
 * ============================================
 */

console.log("🚀 SISTEMA LISTO PARA PRUEBAS");

// 1. PRODUCTOS
console.log("\n✅ 1. CATÁLOGO Y PRODUCTOS");
console.log("   - Visita: http://localhost:5174");
console.log("   - Deberías ver 25 productos (5 de cada categoría)");
console.log("   - Categorías: Vinos, Cervezas, Piscos, Whiskys, Ron");

// 2. CARRITO
console.log("\n✅ 2. CARRITO DE COMPRAS");
console.log("   - Click en botones 'Carrito' para agregar productos");
console.log("   - Badge en navbar muestra cantidad de items");
console.log("   - Ir a /carrito para ver resumen y procesar pago");

// 3. REGISTRO
console.log("\n✅ 3. REGISTRO DE USUARIO");
console.log("   - URL: http://localhost:5174/registro");
console.log("   - Email: test@example.com");
console.log("   - Password: password123 (mín 8 caracteres)");
console.log("   - Fecha nacimiento: 1990-01-01");
console.log("   - Success: Redirige a login automáticamente");

// 4. LOGIN
console.log("\n✅ 4. INICIAR SESIÓN");
console.log("   - URL: http://localhost:5174/login");
console.log("   - Usar credenciales del registro");
console.log("   - Success: Redirige a /dashboard");

// 5. BACKEND
console.log("\n✅ 5. API ENDPOINTS");
console.log("   - GET  http://localhost:8000/api/productos (lista)");
console.log("   - GET  http://localhost:8000/api/catalogo (con filtros)");
console.log("   - GET  http://localhost:8000/api/producto/1 (detalle)");
console.log("   - POST http://localhost:8000/api/registro (registrar)");
console.log("   - POST http://localhost:8000/api/login (iniciar sesión)");

console.log("\n📋 CAMBIOS REALIZADOS:");
console.log("   ✓ CORS configurado para 5173 y 5174");
console.log("   ✓ Login y registro ahora usan JSON (request.data)");
console.log("   ✓ Home muestra 25 productos con agregar a carrito");
console.log("   ✓ Carrito.jsx página completa con resumen");
console.log("   ✓ Header dinámico con contador de carrito");
console.log("   ✓ 25 productos populados (poblar_productos command)");
console.log("   ✓ Rutas correctas sin barra al final");

console.log("\n🔧 Si algo falla:");
console.log("   1. Abre F12 para ver errores en consola");
console.log("   2. Verifica que ambos servidores corren:");
console.log("      - Backend: http://localhost:8000");
console.log("      - Frontend: http://localhost:5174");
console.log("   3. Recarga la página (Ctrl+Shift+R)");
