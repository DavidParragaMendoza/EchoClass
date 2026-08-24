/**
 * EchoClass — Configuración del servidor remoto
 *
 * INSTRUCCIONES:
 * 1. Crea tu pod en RunPod siguiendo runpod/DEPLOY.md
 * 2. Copia la URL del pod desde el dashboard de RunPod
 * 3. Reemplaza "REEMPLAZAR" con tu URL real (sin barra final)
 *
 * Ejemplo:
 *   serverUrl: "https://abc12345-8000.proxy.runpod.net"
 *   wsUrl:     "wss://abc12345-8000.proxy.runpod.net"
 *
 * Mientras no tengas el pod activo, deja los valores con
 * "REEMPLAZAR" — la app mostrará un error claro de conexión.
 */
window.ECHOCLASS_CONFIG = {
  serverUrl: "https://REEMPLAZAR-8000.proxy.runpod.net",
  wsUrl:     "wss://REEMPLAZAR-8000.proxy.runpod.net"
};
