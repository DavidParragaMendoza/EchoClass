# 🔧 Guía para Recrear EchoClass en Cualquier Laptop

Esta guía te explica paso a paso cómo clonar y configurar **EchoClass** en **cualquier computadora**, adaptando los modelos de IA según tu hardware.

---

## 📋 Índice

1. [Evaluar tu Hardware](#1-evaluar-tu-hardware)
2. [Instalar Requisitos Base](#2-instalar-requisitos-base)
3. [Descargar el Proyecto](#3-descargar-el-proyecto)
4. [Configurar según tu RAM](#4-configurar-según-tu-ram)
5. [Verificar Instalación](#5-verificar-instalación)
6. [Personalización Adicional](#6-personalización-adicional)

---

## 1. Evaluar tu Hardware

Antes de empezar, identifica las especificaciones de tu laptop:

**Windows:** `Win + Pausa` o busca "Acerca de tu PC"
**Linux:** `lscpu` y `free -h`
**macOS:** Menú Apple → Acerca de esta Mac

### Categorías de Hardware

| Categoría | RAM | CPU | Configuración recomendada |
|-----------|-----|-----|---------------------------|
| 🟢 Básica | 8 GB | i5 / Ryzen 5 | Whisper `tiny` + Ollama `phi3:mini` |
| 🟡 Media | 16 GB | i5-i7 / Ryzen 5-7 | Whisper `base` + Ollama `mistral` |
| 🟢 Alta | 32 GB+ | i7-i9 / Ryzen 7-9 | Whisper `small` + Ollama `llama3` |

---

## 2. Instalar Requisitos Base

### 2.1 Python 3.9+

**Windows:**
```bash
# Usando winget
winget install Python.Python.3.11

# O descarga desde https://www.python.org/downloads/
# ⚠️ IMPORTANTE: Marca "Add Python to PATH" durante instalación
```

**Linux:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**macOS:**
```bash
brew install python@3.11
```

**Verificar:**
```bash
python --version   # Debe mostrar 3.9+
```

### 2.2 FFmpeg

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

**Verificar:**
```bash
ffmpeg -version
```

### 2.3 Ollama

1. Ve a [ollama.ai](https://ollama.ai)
2. Descarga el instalador para tu sistema
3. Instala y ejecuta Ollama

**Verificar:**
```bash
ollama --version
```

---

## 3. Descargar el Proyecto

### Opción A: Clonar con Git
```bash
git clone <URL_DEL_REPOSITORIO>
cd EchoClass
```

### Opción B: Descargar ZIP
1. Descarga el ZIP del repositorio
2. Extrae en una carpeta de tu elección
3. Abre una terminal en esa carpeta

### Instalar dependencias

**Windows:**
```cmd
install.bat
```

**Linux/macOS:**
```bash
chmod +x install.sh start_server.sh
./install.sh
```

**O manualmente:**
```bash
cd backend
python -m venv venv
# Windows: .\venv\Scripts\activate
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
```

---

## 4. Configurar según tu RAM

### 🔴 Si tienes 8 GB RAM (Configuración Ligera)

**Paso 1: Descargar modelo Ollama ligero**
```bash
ollama pull phi3:mini
```

**Paso 2: Configurar Whisper**

Abre `backend/transcription.py` y busca la línea con `model_size`:
```python
# ANTES (puede decir "base"):
self.model_size = "base"

# DESPUÉS - Cambia a "tiny":
self.model_size = "tiny"
```

**Paso 3: Configurar Ollama**

Abre `backend/llm_processor.py` y busca `model:`:
```python
# ANTES:
def __init__(self, model: str = "llama3"):

# DESPUÉS:
def __init__(self, model: str = "phi3:mini"):
```

**Paso 4 (Opcional): Reducir uso de CPU**

En `backend/transcription.py`:
```python
self.model = WhisperModel(
    self.model_size,
    cpu_threads=2,    # Reducir de 4 a 2
    num_workers=1     # Reducir de 2 a 1
)
```

---

### 🟡 Si tienes 16 GB RAM (Configuración Estándar)

**Paso 1: Descargar modelo Ollama**
```bash
ollama pull llama3
# o alternativa más rápida:
ollama pull mistral
```

**Paso 2: Configurar Whisper**

En `backend/transcription.py`:
```python
self.model_size = "base"  # Mantener en "base" - buen balance
```

**Paso 3: Configurar Ollama**

En `backend/llm_processor.py`:
```python
def __init__(self, model: str = "llama3"):  # o "mistral"
```

---

### 🟢 Si tienes 32 GB+ RAM (Configuración Potente)

**Paso 1: Descargar modelo Ollama de mayor calidad**
```bash
ollama pull llama3:70b
# o
ollama pull mixtral
```

**Paso 2: Configurar Whisper para mayor precisión**

En `backend/transcription.py`:
```python
self.model_size = "small"  # o incluso "medium"
```

**Paso 3: Configurar más threads**

```python
self.model = WhisperModel(
    self.model_size,
    cpu_threads=8,    # Más núcleos
    num_workers=4     # Más workers
)
```

---

## 5. Verificar Instalación

### Paso 1: Iniciar Ollama
```bash
ollama serve
```
Deja esta terminal abierta.

### Paso 2: Iniciar el servidor (nueva terminal)
```bash
# Windows
start_server.bat

# Linux/macOS
./start_server.sh
```

### Paso 3: Verificar que responde
```bash
curl http://localhost:8000/health
```

Debe responder:
```json
{
  "status": "healthy",
  "transcription_model": "loaded",
  "ollama_available": true
}
```

### Paso 4: Probar el frontend
1. Abre `frontend/index.html` en Chrome/Edge
2. Verifica que diga "🟢 Conectado al servidor"
3. Prueba grabar tu voz y transcribir

---

## 6. Personalización Adicional

### Cambiar idioma de transcripción

Abre `backend/transcription.py` y busca `language=`:

```python
# Para español (default):
language="es"

# Para inglés:
language="en"

# Para auto-detectar (más lento):
language=None
```

### Cambiar puerto del servidor

Si el puerto 8000 está ocupado, cambia en `backend/main.py`:
```python
uvicorn.run(
    "main:app",
    host="0.0.0.0",
    port=5000,  # Cambiar aquí
)
```

Y actualiza en `frontend/app.js`:
```javascript
this.ws = new WebSocket('ws://localhost:5000/ws');
// y también en fetch():
const response = await fetch('http://localhost:5000/summarize', {
```

### Cambiar colores del tema

Edita `frontend/styles.css` (líneas 9-18):
```css
:root {
    --primary-color: #2563eb;    /* Azul - Botones */
    --danger-color: #dc2626;     /* Rojo - Detener */
    --success-color: #16a34a;    /* Verde - Resumen */
    --bg-dark: #0f172a;          /* Fondo */
}
```

### Ajustar duración de grabación

En `frontend/app.js`, busca `RECORDING_DURATION`:
```javascript
this.RECORDING_DURATION = 5000;  // 5 segundos por defecto

// Para respuesta más rápida:
this.RECORDING_DURATION = 3000;  // 3 segundos

// Para mejor calidad:
this.RECORDING_DURATION = 7000;  // 7 segundos
```

---

## 📊 Tabla de Referencia Rápida

| Componente | Archivo | Qué cambiar |
|------------|---------|-------------|
| Modelo Whisper | `backend/transcription.py` | `model_size = "base"` |
| Modelo Ollama | `backend/llm_processor.py` | `model: str = "llama3"` |
| Idioma | `backend/transcription.py` | `language="es"` |
| Puerto | `backend/main.py` + `frontend/app.js` | `port=8000` |
| Colores | `frontend/styles.css` | Variables CSS `:root` |
| Duración grabación | `frontend/app.js` | `RECORDING_DURATION` |
| Threads CPU | `backend/transcription.py` | `cpu_threads=4` |

---

## ⚠️ Solución de Problemas Comunes

### "Module not found" al iniciar
```bash
cd backend
pip install -r requirements.txt --force-reinstall
```

### "Ollama no responde"
```bash
# Verificar que Ollama esté corriendo
ollama serve

# Verificar que el modelo esté descargado
ollama list
```

### "El servidor se cierra inmediatamente"
- Lee el error en la terminal
- Verifica que el entorno virtual esté activo
- Reinstala dependencias

### "Muy lento" o "Se congela"
1. Usa modelo Whisper más pequeño: `tiny`
2. Usa modelo Ollama más ligero: `phi3:mini`
3. Cierra otras aplicaciones
4. Reduce `cpu_threads` a 2

### "Port already in use"
```bash
# Windows - encontrar qué usa el puerto
netstat -ano | findstr :8000

# Matar el proceso
taskkill /PID <número> /F
```

---

## 🎯 Configuraciones Probadas

### ASUS X1504VA (Intel i7-1355U, 16GB RAM)
```
Whisper: base
Ollama: llama3
Threads: 4
Resultado: ✅ Funciona bien
```

### Laptop básica (Intel i5, 8GB RAM)
```
Whisper: tiny
Ollama: phi3:mini
Threads: 2
Resultado: ✅ Funciona (más lento)
```

### MacBook Pro M1 (16GB RAM)
```
Whisper: base
Ollama: llama3
Threads: 8
Resultado: ✅ Excelente rendimiento
```

---

**¡Listo! Tu proyecto está configurado para tu hardware específico.** 🚀
