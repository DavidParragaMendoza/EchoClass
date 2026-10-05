# 🚀 Guía de Despliegue en RunPod (EchoClass)

> [!NOTE]
> **Documento Actualizado:**
> Esta guía preliminar ha sido reemplazada por el manual oficial, ilustrado paso a paso con capturas de pantalla, resolución de incidencias (como la biblioteca `zstd`), configuración de GPU y evidencias de pruebas en vivo.
> 
> 👉 **Por favor consulta el manual completo en:** **[GUIA_DESPLIEGUE_RUNPOD.md](../GUIA_DESPLIEGUE_RUNPOD.md)**

---

### Resumen Rápido de Comandos para Exportar Imagen:

```bash
# 1. Compilar imagen optimizada para CUDA 12.1 desde la raíz del proyecto:
docker build -f runpod/Dockerfile -t TU_USUARIO/echoclass:latest .

# 2. Publicar en Docker Hub:
docker push TU_USUARIO/echoclass:latest
```

Para la configuración completa del Pod en RunPod (GPU NVIDIA RTX A5000 / 4090, variables de entorno y conectividad WebSocket segura), sigue la guía detallada en [GUIA_DESPLIEGUE_RUNPOD.md](../GUIA_DESPLIEGUE_RUNPOD.md).
