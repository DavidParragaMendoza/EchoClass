class TranscriptionApp {
    constructor() {
        this.ws = null;
        this.mediaRecorder = null;
        this.audioStream = null;
        this.transcriptionText = '';
        this.isRecording = false;
        this.startTime = null;
        this.timerInterval = null;
        this.recordingInterval = null;
        this.RECORDING_DURATION = 8000; // Grabar cada 8 segundos para más contexto
        this.currentMode = null;
        
        this.initElements();
        this.initEventListeners();
        this.connectWebSocket();
    }

    initElements() {
        this.startMicBtn = document.getElementById('startMic');
        this.startSystemBtn = document.getElementById('startSystem');
        this.stopBtn = document.getElementById('stop');
        this.statusEl = document.getElementById('status');
        this.timerEl = document.getElementById('timer');
        this.transcriptionEl = document.getElementById('transcription');
        this.charCountEl = document.getElementById('charCount');
        this.summarizeBtn = document.getElementById('summarize');
        this.downloadRawBtn = document.getElementById('downloadRaw');
        this.clearBtn = document.getElementById('clear');
        this.summaryContainer = document.getElementById('summaryContainer');
        this.summaryEl = document.getElementById('summary');
        this.downloadSummaryBtn = document.getElementById('downloadSummary');
        this.loadingModal = document.getElementById('loadingModal');
        this.loadingText = document.getElementById('loadingText');
    }

    initEventListeners() {
        this.startMicBtn.addEventListener('click', () => this.startRecording('mic'));
        this.startSystemBtn.addEventListener('click', () => this.startRecording('system'));
        this.stopBtn.addEventListener('click', () => this.stopRecording());
        this.summarizeBtn.addEventListener('click', () => this.generateSummary());
        this.downloadRawBtn.addEventListener('click', () => this.downloadTranscription());
        this.clearBtn.addEventListener('click', () => this.clearAll());
        this.downloadSummaryBtn.addEventListener('click', () => this.downloadSummary());
    }

    connectWebSocket() {
        this.ws = new WebSocket('ws://localhost:8000/ws');
        
        this.ws.onopen = () => {
            console.log('✅ Conexión WebSocket establecida');
            this.updateStatus('🟢 Conectado al servidor', 'success');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'transcription') {
                this.addTranscription(data.text);
            } else if (data.type === 'error') {
                this.showError(data.message);
            } else if (data.type === 'warning') {
                console.warn('⚠️', data.message);
                // Mostrar advertencia temporal sin interrumpir
                this.showWarning(data.message);
            }
        };

        this.ws.onerror = (error) => {
            console.error('❌ Error WebSocket:', error);
            this.updateStatus('🔴 Error de conexión', 'error');
        };

        this.ws.onclose = () => {
            console.log('🔌 Conexión WebSocket cerrada');
            this.updateStatus('🔴 Desconectado', 'error');
            setTimeout(() => this.connectWebSocket(), 3000);
        };
    }

    async startRecording(mode) {
        try {
            this.currentMode = mode;
            
            if (mode === 'mic') {
                this.audioStream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        sampleRate: 16000
                    } 
                });
                this.updateStatus('🔴 Grabando Micrófono', 'recording');
            } else if (mode === 'system') {
                this.audioStream = await navigator.mediaDevices.getDisplayMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        sampleRate: 16000
                    },
                    video: false
                });
                this.updateStatus('🔴 Grabando Audio del Sistema', 'recording');
            }

            this.isRecording = true;
            this.startTimer();
            
            this.startMicBtn.disabled = true;
            this.startSystemBtn.disabled = true;
            this.stopBtn.disabled = false;
            
            this.transcriptionEl.innerHTML = '';
            
            // Iniciar ciclo de grabación
            this.startRecordingCycle();

        } catch (error) {
            console.error('❌ Error al iniciar grabación:', error);
            this.showError('No se pudo acceder al dispositivo de audio. Verifica los permisos.');
        }
    }

    startRecordingCycle() {
        // Crear un nuevo MediaRecorder para cada ciclo
        const startNewRecording = () => {
            if (!this.isRecording || !this.audioStream.active) {
                console.log('⏹️ Stream detenido, cancelando ciclo');
                return;
            }

            const chunks = [];
            
            try {
                this.mediaRecorder = new MediaRecorder(this.audioStream, {
                    mimeType: 'audio/webm;codecs=opus'
                });
            } catch (e) {
                // Fallback si opus no está soportado
                this.mediaRecorder = new MediaRecorder(this.audioStream, {
                    mimeType: 'audio/webm'
                });
            }

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    chunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                if (chunks.length > 0 && this.ws.readyState === WebSocket.OPEN) {
                    // Crear un Blob completo con TODOS los chunks (incluyendo header)
                    const audioBlob = new Blob(chunks, { type: 'audio/webm;codecs=opus' });
                    
                    if (audioBlob.size > 1000) { // Mínimo 1KB
                        console.log(`📤 Enviando grabación completa: ${audioBlob.size} bytes`);
                        audioBlob.arrayBuffer().then(buffer => {
                            this.ws.send(buffer);
                        });
                    } else {
                        console.log(`⚠️ Grabación muy pequeña (${audioBlob.size} bytes), omitiendo`);
                    }
                }
                
                // Iniciar siguiente ciclo si aún estamos grabando
                if (this.isRecording && this.audioStream.active) {
                    startNewRecording();
                }
            };

            // Grabar por RECORDING_DURATION ms, luego detenerse
            this.mediaRecorder.start();
            console.log(`🎙️ Iniciando grabación de ${this.RECORDING_DURATION/1000}s...`);
            
            setTimeout(() => {
                if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                    this.mediaRecorder.stop();
                }
            }, this.RECORDING_DURATION);
        };

        // Comenzar el primer ciclo
        startNewRecording();
    }

    stopRecording() {
        if (this.isRecording) {
            this.isRecording = false;
            
            // Detener el MediaRecorder si está activo
            if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                this.mediaRecorder.stop();
            }
            
            // Detener todos los tracks del stream
            if (this.audioStream) {
                this.audioStream.getTracks().forEach(track => track.stop());
            }
            
            this.stopTimer();
            
            this.updateStatus('🟢 Grabación detenida', 'success');
            this.startMicBtn.disabled = false;
            this.startSystemBtn.disabled = false;
            this.stopBtn.disabled = true;
            
            if (this.transcriptionText.length > 0) {
                this.summarizeBtn.disabled = false;
                this.downloadRawBtn.disabled = false;
            }
        }
    }

    addTranscription(text) {
        if (text.trim()) {
            this.transcriptionText += text + ' ';
            this.transcriptionEl.textContent = this.transcriptionText;
            this.charCountEl.textContent = this.transcriptionText.length;
            this.transcriptionEl.scrollTop = this.transcriptionEl.scrollHeight;
        }
    }

    async generateSummary() {
        if (!this.transcriptionText.trim()) {
            this.showError('No hay texto para resumir');
            return;
        }

        this.loadingModal.style.display = 'flex';
        this.loadingText.textContent = 'Generando resumen con Ollama...';

        try {
            const response = await fetch('http://localhost:8000/summarize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: this.transcriptionText })
            });

            if (!response.ok) {
                throw new Error('Error al generar resumen');
            }

            const data = await response.json();
            this.summaryEl.textContent = data.summary;
            this.summaryContainer.style.display = 'block';
            this.summaryContainer.scrollIntoView({ behavior: 'smooth' });
            
        } catch (error) {
            console.error('❌ Error al generar resumen:', error);
            this.showError('Error al conectar con Ollama. Verifica que esté ejecutándose.');
        } finally {
            this.loadingModal.style.display = 'none';
        }
    }

    downloadTranscription() {
        this.downloadFile(this.transcriptionText, 'transcripcion_raw.txt', 'text/plain');
    }

    downloadSummary() {
        const summaryText = this.summaryEl.textContent;
        this.downloadFile(summaryText, 'resumen_clase.md', 'text/markdown');
    }

    downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    clearAll() {
        if (confirm('¿Estás seguro de que deseas limpiar todo el contenido?')) {
            this.transcriptionText = '';
            this.transcriptionEl.innerHTML = '<p class="placeholder">La transcripción aparecerá aquí en tiempo real...</p>';
            this.charCountEl.textContent = '0';
            this.summaryEl.textContent = '';
            this.summaryContainer.style.display = 'none';
            this.summarizeBtn.disabled = true;
            this.downloadRawBtn.disabled = true;
            this.timerEl.textContent = '00:00:00';
        }
    }

    startTimer() {
        this.startTime = Date.now();
        this.timerInterval = setInterval(() => {
            const elapsed = Date.now() - this.startTime;
            const hours = Math.floor(elapsed / 3600000);
            const minutes = Math.floor((elapsed % 3600000) / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            
            this.timerEl.textContent = 
                `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        }, 1000);
    }

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    updateStatus(message, type) {
        this.statusEl.textContent = message;
        this.statusEl.className = `status ${type === 'recording' ? 'recording' : ''}`;
    }

    showError(message) {
        alert(`❌ Error: ${message}`);
    }

    showWarning(message) {
        // Mostrar advertencia temporal en el estado
        const originalStatus = this.statusEl.textContent;
        this.statusEl.textContent = `⚠️ ${message}`;
        setTimeout(() => {
            if (this.isRecording) {
                this.statusEl.textContent = '🔴 Grabando...';
            }
        }, 3000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new TranscriptionApp();
});
