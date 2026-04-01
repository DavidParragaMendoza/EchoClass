# 🎙️ EchoClass

Aplicación web local, gratuita y privada para transcribir clases en tiempo real y generar resúmenes estructurados con IA. Todo funciona offline en tu computadora.

> **Echo** = Eco de tus clases capturado con IA 🎓✨

---

## 📋 Tabla de Contenidos

1. [Características](#-características)
2. [Requisitos](#-requisitos)
3. [Instalación Rápida](#-instalación-rápida)
4. [Uso Diario](#-uso-diario)
5. [Configuración de Modelos](#-configuración-de-modelos)
6. [Solución de Problemas](#-solución-de-problemas)
7. [Estructura del Proyecto](#-estructura-del-proyecto)

---

## ✨ Características

- 🎤 **Transcripción en tiempo real** con Whisper (faster-whisper)
- 💻 **Captura de audio** del micrófono o sistema (Zoom, Teams, Meet)
- 🤖 **Resumen inteligente** con Ollama (LLM local)
- 🔒 **100% privado** - Todo se ejecuta localmente, sin internet
- 📥 **Exportación** en Markdown y texto plano
- ⚡ **Optimizado para CPU** - No requiere GPU

---

## 🖥️ Requisitos

| Requisito | Mínimo | Recomendado |
|-----------|--------|-------------|
| CPU | Intel i5 / Ryzen 5 | Intel i7 / Ryzen 7 |
| RAM | 8 GB | 16 GB |
| Almacenamiento | 10 GB libres | 20 GB libres |
| SO | Windows 10, Linux, macOS | Windows 11 |
| Python | 3.9+ | 3.11+ |

**Software necesario:**
- Python 3.9+
- FFmpeg (procesamiento de audio)
- Ollama (IA para resúmenes)

---

## 🚀 Instalación Rápida

### Paso 1: Instalar FFmpeg

**Windows:**
```bash
winget install FFmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### Paso 2: Instalar Ollama

1. Descarga desde [ollama.ai](https://ollama.ai)
2. Instala y ejecuta
3. Descarga un modelo:
```bash
ollama pull llama3
```

### Paso 3: Instalar dependencias del proyecto

**Windows:**
```cmd
install.bat
```

**Linux/macOS:**
```bash
chmod +x install.sh && ./install.sh
```

### Paso 4: Verificar instalación

```bash
python --version          # Debe mostrar 3.9+
ffmpeg -version           # Debe mostrar versión
ollama list               # Debe mostrar llama3
```

---

## 📖 Uso Diario

### Iniciar la aplicación

**1. Iniciar Ollama** (si no está corriendo):
```bash
ollama serve
```

**2. Iniciar el servidor:**

Windows: `start_server.bat`  
Linux/macOS: `./start_server.sh`

**3. Abrir el frontend:**
- Abre `frontend/index.html` en tu navegador

### Flujo de trabajo

1. **Grabar Micrófono** → Para clases presenciales
2. **Grabar Audio Sistema** → Para Zoom, Teams, YouTube
3. **Detener** → Finaliza la grabación
4. **Generar Resumen** → Crea resumen con IA (30-60 seg)
5. **Descargar** → Exporta en .txt o .md

### Controles del servidor

| Acción | Comando |
|--------|---------|
| Iniciar | `start_server.bat` |
| Detener | `Ctrl + C` en la terminal |
| Verificar | Abrir http://localhost:8000 |

---

## ⚙️ Configuración de Modelos

### Modelo Whisper (Transcripción)

Edita `backend/transcription.py`, busca `model_size`:

| Modelo | RAM | Velocidad | Precisión | Uso recomendado |
|--------|-----|-----------|-----------|-----------------|
| `tiny` | ~1 GB | ⚡⚡⚡ Muy rápido | ⭐⭐ | Laptops con 8GB RAM |
| `base` | ~1.4 GB | ⚡⚡ Rápido | ⭐⭐⭐ | **Recomendado** |
| `small` | ~2 GB | ⚡ Normal | ⭐⭐⭐⭐ | Alta precisión |

```python 
# Línea ~20 en backend/transcription.py
self.model_size = "base"  # Cambia aquí: tiny, base, small
```

### Modelo Ollama (Resúmenes)

Primero descarga el modelo que quieras:
```bash
ollama pull llama3      # 4.7GB - Recomendado
ollama pull mistral     # 4.1GB - Más ligero
```

Luego edita `backend/llm_processor.py`:
```python
# Línea ~14 en backend/llm_processor.py
def __init__(self, model: str = "llama3"):  # Cambia "llama3" por tu modelo
```

### Cambiar idioma de transcripción

Edita `backend/transcription.py`:
```python
# Línea ~86
language="es"    # Español (default)
language="en"    # Inglés
language=None    # Auto-detectar
```

### Ajustar rendimiento CPU

```python
# En backend/transcription.py, línea ~37
self.model = WhisperModel(
    self.model_size,
    cpu_threads=4,  # Ajusta según tus núcleos de CPU
    num_workers=2
)
```

---

## 🔧 Solución de Problemas

### ❌ "No se puede conectar al servidor"
```bash
# Verifica que el servidor esté corriendo
curl http://localhost:8000/health
```

### ❌ "Error de Ollama / No se pudo conectar"
```bash
# Reinicia Ollama
ollama serve

# Verifica que el modelo esté descargado
ollama list
```

### ❌ "No detecta el micrófono"
- Permite acceso al micrófono en el popup del navegador
- Usa Chrome o Edge (mejor compatibilidad)

### ❌ "Audio del sistema no funciona"
- Windows: Habilita "Mezcla estéreo" en configuración de audio
- Usa Chrome o Edge
- Comparte la pestaña con audio al grabar

### ❌ "El resumen tarda mucho"
- Normal: 30-60 segundos en CPU
- Usa un modelo más ligero: `phi3:mini` o `mistral`

### ❌ "Error de memoria / RAM"
1. Usa Whisper `tiny` en lugar de `base`
2. Cierra otras aplicaciones
3. El sistema libera Whisper antes de cargar Ollama automáticamente

### ❌ "Port 8000 already in use"
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <número_del_PID> /F
```

### ❌ WebM corrupto / Errores de audio
El sistema usa grabaciones cíclicas de 5 segundos. Si hay problemas:
- Habla más fuerte/cerca del micrófono
- Ajusta `RECORDING_DURATION` en `frontend/app.js` (3000-10000 ms)

---

## 📊 Consumo de Recursos

| Fase | RAM | CPU |
|------|-----|-----|
| Transcribiendo | ~2-3 GB | 25-35% |
| Generando resumen | ~6-7 GB | 50-70% |
| Servidor en reposo | ~400 MB | 5% |

---

## 📁 Estructura del Proyecto

```
EchoClass/
├── backend/                    # Servidor Python
│   ├── main.py                 # Servidor FastAPI + WebSocket
│   ├── transcription.py        # Motor Whisper (⚙️ cambiar modelo aquí)
│   ├── llm_processor.py        # Conexión Ollama (⚙️ cambiar modelo aquí)
│   └── requirements.txt        # Dependencias Python
│
├── frontend/                   # Interfaz Web
│   ├── index.html              # Página principal
│   ├── styles.css              # Estilos (🎨 cambiar colores aquí)
│   └── app.js                  # Lógica JavaScript
│
├── install.bat / install.sh    # Instaladores automáticos
├── start_server.bat / .sh      # Iniciar servidor
├── README.md                   # Este archivo
├── GUIA_RECREAR_PROYECTO.md    # Cómo recrear en otra laptop
└── ROADMAP.md                  # Mejoras futuras
```

---

## 🔗 Enlaces Útiles

- [Documentación Whisper](https://github.com/openai/whisper)
- [Documentación Ollama](https://ollama.ai)
- [Descargar FFmpeg](https://ffmpeg.org/download.html)
- [Descargar Python](https://www.python.org/downloads/)

---

## 📝 Licencia

MIT License - Código abierto y gratuito.

---

## 📫 Redes:

* 💼 **LinkedIn:** [David Parraga Mendoza](https://www.linkedin.com/in/davidparragamendoza/)
* 🐦 **X (Twitter):** [@DavidParragaMen](https://x.com/DavidParragaMen)
**Desarrollado con ❤️ para aprendizaje local y privado**

