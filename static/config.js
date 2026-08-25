/**
 * EchoClass — Configuración del servidor
 *
 * ✅ MODO RUNPOD (recomendado):
 *    Deja serverUrl y wsUrl vacíos ("").
 *    La app usará window.location automáticamente → no necesitas tocar nada.
 *
 * 🛠️ MODO LOCAL APUNTANDO A RUNPOD (desarrollo):
 *    Rellena las URLs solo si sirves el frontend desde tu PC
 *    apuntando a un pod remoto. NUNCA subas esto a git con URLs reales.
 *
 * Ejemplo para desarrollo local:
 *   serverUrl: "https://XXXXX-8000.proxy.runpod.net"
 *   wsUrl:     "wss://XXXXX-8000.proxy.runpod.net/ws"
 */
window.ECHOCLASS_CONFIG = {
  serverUrl: "",
  wsUrl:     ""
};