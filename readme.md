# 🎙️ EchoClass

Transcribe tus clases en tiempo real y genera resúmenes con IA. 100% local y privado.

## ⚡ Instalación Rápida

### Requisitos Previos
- **Windows 10/11**
- **Python 3.9 - 3.13** (recomendado 3.11/3.12) → [Descargar](https://www.python.org/downloads/)
- **Ollama** → [Descargar](https://ollama.ai)

### Instalar

```cmd
.\install.bat
```

El instalador configura automáticamente:
- ✅ Entorno virtual Python
- ✅ Todas las dependencias
- ✅ FFmpeg (si no está instalado)
- ✅ Modelo de IA para resúmenes

### Iniciar

```cmd
.\start.bat
```

Abre **http://localhost:8000** en tu navegador.

> ⚠️ Asegúrate de que Ollama esté ejecutándose (`ollama serve`)

---

## 📖 Uso

1. **Grabar** → Clic en "Grabar Micrófono"
2. **Hablar** → La transcripción aparece en tiempo real
3. **Detener** → Clic en "Detener"
4. **Resumir** → Clic en "Generar Resumen con Ollama"
5. **Descargar** → Exporta en .txt o .md

---

## ⚙️ Configuración

### Cambiar modelo de transcripción

Edita `src/core/config.py`:
```python
model_size: str = "large"      # máxima precisión
compute_type: str = "float16"  # ideal para GPU NVIDIA
device: str = "cuda"           # usa GPU
```

### Cambiar modelo de resúmenes

```cmd
ollama pull qwen2.5:7b
```

Edita `src/core/config.py`:
```python
model: str = "qwen2.5:7b"  # modelo por defecto
```

---

## 🔧 Solución de Problemas

| Problema | Solución |
|----------|----------|
| No se conecta al servidor | Verifica que `start.bat` esté ejecutándose |
| Error de Ollama | Ejecuta `ollama serve` en otra terminal |
| No detecta micrófono | Abre desde http://localhost:8000 (no file://) |
| Resumen lento | Normal: 30-60 seg en CPU |

---

## 📁 Estructura

```
EchoClass/
├── src/                    # Código fuente (Clean Architecture)
│   ├── api/                # Endpoints REST y WebSocket
│   ├── core/               # Configuración
│   ├── domain/             # Modelos y contratos
│   ├── infrastructure/     # Adaptadores (Whisper, Ollama)
│   ├── services/           # Casos de uso
│   └── main.py             # Punto de entrada
├── static/                 # Frontend
├── install.bat             # Instalador
├── start.bat               # Iniciar servidor
└── requirements.txt        # Dependencias Python
```

---

## 📫 Contacto

- **LinkedIn:** [David Parraga Mendoza](https://www.linkedin.com/in/davidparragamendoza/)
- **X:** [@DavidParragaMen](https://x.com/DavidParragaMen)

---

MIT License

