# 🚀 Guía de Despliegue — EchoClass en RunPod

## Prerequisitos

- Cuenta en [RunPod.io](https://www.runpod.io)
- Docker instalado en tu máquina local (para construir la imagen)
- Cuenta en [Docker Hub](https://hub.docker.com) o acceso a un registry privado

---

## Paso 1 — Construir y publicar la imagen Docker

Desde la raíz del proyecto:

```bash
# 1. Construir la imagen
docker build -f runpod/Dockerfile -t TU_USUARIO/echoclass:latest .

# 2. Publicar en Docker Hub
docker login
docker push TU_USUARIO/echoclass:latest
```

> **Reemplaza** `TU_USUARIO` con tu usuario de Docker Hub.

---

## Paso 2 — Crear el pod en RunPod

1. Ir a [RunPod → Pods](https://www.runpod.io/console/pods)
2. Clic en **"+ Deploy"**
3. Elegir GPU: **RTX 4090** (recomendado) o **RTX 3090**
4. En **"Container Image"** poner: `TU_USUARIO/echoclass:latest`
5. En **"Container Disk"**: mínimo **30 GB** (modelos de Whisper + Ollama)
6. En **"Expose HTTP Ports"**: agregar el puerto **`8000`**
7. Variables de entorno (sección **"Environment Variables"**):

| Variable | Valor |
|----------|-------|
| `WHISPER_MODEL` | `large-v3` |
| `WHISPER_DEVICE` | `cuda` |
| `WHISPER_COMPUTE_TYPE` | `float16` |
| `WHISPER_LANGUAGE` | `es` |
| `OLLAMA_MODEL` | `qwen2.5:7b` |

8. Clic en **"Deploy"**

---

## Paso 3 — Obtener la URL del pod

Una vez el pod esté corriendo:

1. Ir al pod en el dashboard de RunPod
2. Buscar la sección **"Connect"** → **"HTTP Service"**
3. Copiar la URL que tiene este formato:
   ```
   https://XXXXXXXX-8000.proxy.runpod.net
   ```

---

## Paso 4 — Configurar el frontend

Editar el archivo [`static/config.js`](../static/config.js):

```js
window.ECHOCLASS_CONFIG = {
  // Pegar aquí la URL del paso anterior (SIN barra final)
  serverUrl: "https://XXXXXXXX-8000.proxy.runpod.net",
  wsUrl:     "wss://XXXXXXXX-8000.proxy.runpod.net"
};
```

Guardar el archivo y abrir `static/index.html` en el navegador.

---

## Paso 5 — Verificar que todo funciona

Abrir en el navegador:
```
https://XXXXXXXX-8000.proxy.runpod.net/health
```

Deberías ver algo así:
```json
{
  "status": "healthy",
  "services": {
    "transcription": { "status": "loaded" },
    "summarization": { "status": "available", "model": "qwen2.5:7b" }
  }
}
```

---

## Costos estimados

| GPU | Precio/hora | Uso típico (clase 2h) |
|-----|------------|----------------------|
| RTX 4090 | ~$0.74/hr | ~$1.48 |
| RTX 3090 | ~$0.44/hr | ~$0.88 |
| RTX 3080 | ~$0.34/hr | ~$0.68 |

> **Recomendación**: Apagar el pod cuando no lo uses. Los modelos quedan en caché en el volumen del pod para el siguiente arranque (más rápido).

---

## Solución de problemas

| Problema | Causa probable | Solución |
|----------|---------------|----------|
| `/health` no responde | Pod aún iniciando | Esperar 3-5 min (primera descarga del modelo LLM) |
| WebSocket no conecta | URL mal copiada | Verificar que `wsUrl` en `config.js` empieza con `wss://` |
| Whisper tarda mucho | GPU no detectada | Ver logs del pod; verificar que `WHISPER_DEVICE=cuda` |
| Ollama error | Modelo no descargado aún | Revisar logs del pod, esperar descarga de qwen2.5:7b |

---

## Variables de entorno disponibles

| Variable | Default | Descripción |
|----------|---------|-------------|
| `WHISPER_MODEL` | `large-v3` | Tamaño del modelo Whisper |
| `WHISPER_DEVICE` | `cuda` | `cuda` o `cpu` |
| `WHISPER_COMPUTE_TYPE` | `float16` | `float16` (GPU) o `int8` (CPU) |
| `WHISPER_LANGUAGE` | `es` | Idioma de transcripción |
| `WHISPER_CPU_THREADS` | `4` | Hilos CPU (solo si device=cpu) |
| `OLLAMA_MODEL` | `qwen2.5:7b` | Modelo LLM para resúmenes |
| `OLLAMA_URL` | `http://localhost:11434` | URL de Ollama (no cambiar) |
| `SERVER_PORT` | `8000` | Puerto del servidor FastAPI |
