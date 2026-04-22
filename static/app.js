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
        this.RECORDING_DURATION = 8000;
        this.SERVER_URL = 'https://contortively-sledlike-marcella.ngrok-free.dev'.replace(/\/+$/, '');
        this.WS_URL = this.SERVER_URL.replace(/^http/, 'ws');
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
        
        // Nuevos elementos para pegar texto
        this.togglePasteBtn = document.getElementById('togglePaste');
        this.pasteArea = document.getElementById('pasteArea');
        this.pasteText = document.getElementById('pasteText');
        this.usePastedTextBtn = document.getElementById('usePastedText');
        
        // Elementos de progreso
        this.progressContainer = document.getElementById('progressContainer');
        this.progressBar = document.getElementById('progressBar');
        this.progressText = document.getElementById('progressText');
        this.progressLog = document.getElementById('progressLog');
    }

    initEventListeners() {
        this.startMicBtn.addEventListener('click', () => this.startRecording('mic'));
        
        if (this.startSystemBtn) {
            this.startSystemBtn.addEventListener('click', () => this.startRecording('system'));
        }
        
        this.stopBtn.addEventListener('click', () => this.stopRecording());
        this.summarizeBtn.addEventListener('click', () => this.generateSummaryWithProgress());
        this.downloadRawBtn.addEventListener('click', () => this.downloadTranscription());
        this.clearBtn.addEventListener('click', () => this.clearAll());
        this.downloadSummaryBtn.addEventListener('click', () => this.downloadSummary());
        
        // Eventos para pegar texto
        this.togglePasteBtn.addEventListener('click', () => this.togglePasteArea());
        this.usePastedTextBtn.addEventListener('click', () => this.usePastedText());
    }

    togglePasteArea() {
        const isHidden = this.pasteArea.style.display === 'none';
        this.pasteArea.style.display = isHidden ? 'block' : 'none';
        this.togglePasteBtn.textContent = isHidden ? 'Ocultar' : 'Mostrar';
    }

    usePastedText() {
        const text = this.pasteText.value.trim();
        if (!text) {
            alert('Por favor, pega algún texto primero');
            return;
        }
        
        this.transcriptionText = text;
        this.transcriptionEl.textContent = text;
        this.charCountEl.textContent = text.length;
        this.summarizeBtn.disabled = false;
        this.downloadRawBtn.disabled = false;
        
        // Ocultar área de pegar
        this.pasteArea.style.display = 'none';
        this.togglePasteBtn.textContent = 'Mostrar';
        
        this.updateStatus('✅ Texto cargado', 'success');
    }

    connectWebSocket() {
        this.ws = new WebSocket(`${this.WS_URL}/ws`);
        
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
        console.log(`🎙️ Iniciando grabación en modo: ${mode}`);
        
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.showError('WebSocket no está conectado. Espera un momento e intenta de nuevo.');
            console.error('❌ WebSocket no está conectado');
            return;
        }
        
        try {
            this.currentMode = mode;
            
            if (mode === 'mic') {
                console.log('🎤 Solicitando acceso al micrófono...');
                this.audioStream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        sampleRate: 16000
                    } 
                });
                console.log('✅ Acceso al micrófono concedido');
                this.updateStatus('🔴 Grabando Micrófono', 'recording');
            } else if (mode === 'system') {
                console.log('💻 Solicitando acceso al audio del sistema...');
                this.audioStream = await navigator.mediaDevices.getDisplayMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        sampleRate: 16000
                    },
                    video: false
                });
                console.log('✅ Acceso al audio del sistema concedido');
                this.updateStatus('🔴 Grabando Audio del Sistema', 'recording');
            }

            this.isRecording = true;
            this.startTimer();
            
            this.startMicBtn.disabled = true;
            if (this.startSystemBtn) this.startSystemBtn.disabled = true;
            this.stopBtn.disabled = false;
            
            this.transcriptionEl.innerHTML = '';
            
            console.log('🔄 Iniciando ciclo de grabación...');
            this.startRecordingCycle();

        } catch (error) {
            console.error('❌ Error al iniciar grabación:', error);
            this.isRecording = false;
            this.startMicBtn.disabled = false;
            if (this.startSystemBtn) this.startSystemBtn.disabled = false;
            this.stopBtn.disabled = true;
            
            if (error.name === 'NotAllowedError') {
                this.showError('Permiso denegado. Por favor, permite el acceso al micrófono en la configuración de tu navegador.');
            } else if (error.name === 'NotFoundError') {
                this.showError('No se encontró ningún dispositivo de audio. Verifica que tu micrófono esté conectado.');
            } else {
                this.showError('No se pudo acceder al dispositivo de audio: ' + error.message);
            }
        }
    }

    startRecordingCycle() {
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
                if (chunks.length > 0 && this.ws && this.ws.readyState === WebSocket.OPEN) {
                    const audioBlob = new Blob(chunks, { type: 'audio/webm;codecs=opus' });
                    
                    if (audioBlob.size > 1000) {
                        console.log(`📤 Enviando grabación completa: ${audioBlob.size} bytes`);
                        audioBlob.arrayBuffer().then(buffer => {
                            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                                this.ws.send(buffer);
                                console.log('✅ Audio enviado al servidor');
                            } else {
                                console.warn('⚠️ WebSocket no está conectado, omitiendo envío');
                            }
                        }).catch(error => {
                            console.error('❌ Error al enviar audio:', error);
                        });
                    } else {
                        console.log(`⚠️ Grabación muy pequeña (${audioBlob.size} bytes), omitiendo`);
                    }
                } else {
                    console.warn('⚠️ No hay chunks o WebSocket no está conectado');
                }
                
                if (this.isRecording && this.audioStream && this.audioStream.active) {
                    startNewRecording();
                }
            };

            this.mediaRecorder.start();
            console.log(`🎙️ Iniciando grabación de ${this.RECORDING_DURATION/1000}s...`);
            
            setTimeout(() => {
                if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                    this.mediaRecorder.stop();
                }
            }, this.RECORDING_DURATION);
        };

        startNewRecording();
    }

    stopRecording() {
        console.log('🛑 Deteniendo grabación...');
        
        if (this.isRecording) {
            this.isRecording = false;
            
            if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
                console.log('⏹️ Deteniendo MediaRecorder...');
                this.mediaRecorder.stop();
            }
            
            if (this.audioStream) {
                console.log('🔇 Deteniendo stream de audio...');
                this.audioStream.getTracks().forEach(track => {
                    track.stop();
                    console.log(`  ✓ Track detenido: ${track.kind}`);
                });
                this.audioStream = null;
            }
            
            this.stopTimer();
            
            this.updateStatus('🟢 Grabación detenida', 'success');
            this.startMicBtn.disabled = false;
            if (this.startSystemBtn) this.startSystemBtn.disabled = false;
            this.stopBtn.disabled = true;
            
            if (this.transcriptionText.length > 0) {
                this.summarizeBtn.disabled = false;
                this.downloadRawBtn.disabled = false;
            }
            
            console.log('✅ Grabación detenida completamente');
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

    async generateSummaryWithProgress() {
        if (!this.transcriptionText.trim()) {
            this.showError('No hay texto para resumir');
            return;
        }

        // Mostrar contenedor de progreso
        this.progressContainer.style.display = 'block';
        this.progressBar.style.width = '0%';
        this.progressText.textContent = 'Iniciando...';
        this.progressLog.innerHTML = '';
        this.summaryContainer.style.display = 'none';
        this.summarizeBtn.disabled = true;

        try {
            const response = await fetch(`${this.SERVER_URL}/summarize/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: this.transcriptionText })
            });

            if (!response.ok) {
                throw new Error('Error al conectar con el servidor');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            this.handleProgressEvent(data);
                        } catch (e) {
                            console.warn('Error parsing SSE data:', e);
                        }
                    }
                }
            }
            
        } catch (error) {
            console.error('❌ Error al generar resumen:', error);
            this.addLogEntry('❌ Error: ' + error.message, 'error');
            this.showError('Error al conectar con Ollama. Verifica que esté ejecutándose.');
        } finally {
            this.summarizeBtn.disabled = false;
        }
    }

    handleProgressEvent(data) {
        if (data.type === 'progress') {
            this.progressText.textContent = data.message;
            
            // Calcular porcentaje
            if (data.total > 0) {
                const percent = (data.current / data.total) * 100;
                this.progressBar.style.width = `${percent}%`;
            } else if (data.phase === 'analyzing') {
                this.progressBar.style.width = '5%';
            } else if (data.phase === 'preparing') {
                this.progressBar.style.width = '2%';
            }
            
            // Agregar al log
            const isSuccess = data.message.includes('✓') || data.message.includes('✅');
            this.addLogEntry(data.message, isSuccess ? 'success' : 'info');
            
        } else if (data.type === 'complete') {
            this.progressBar.style.width = '100%';
            this.progressText.textContent = '✅ Resumen completado';
            this.addLogEntry('✅ Resumen generado exitosamente', 'success');
            
            // Mostrar resumen
            this.summaryEl.textContent = data.summary;
            this.summaryContainer.style.display = 'block';
            this.summaryContainer.scrollIntoView({ behavior: 'smooth' });
            
            // Ocultar progreso después de un momento
            setTimeout(() => {
                this.progressContainer.style.display = 'none';
            }, 2000);
            
        } else if (data.type === 'error') {
            this.progressText.textContent = '❌ Error';
            this.addLogEntry('❌ ' + data.message, 'error');
            this.showError(data.message);
        }
    }

    addLogEntry(message, type = 'info') {
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.textContent = `${new Date().toLocaleTimeString()} - ${message}`;
        this.progressLog.appendChild(entry);
        this.progressLog.scrollTop = this.progressLog.scrollHeight;
    }

    // Método antiguo por si se necesita (sin progreso)
    async generateSummary() {
        if (!this.transcriptionText.trim()) {
            this.showError('No hay texto para resumir');
            return;
        }

        this.loadingModal.style.display = 'flex';
        this.loadingText.textContent = 'Generando resumen con Ollama...';

        try {
            const response = await fetch(`${this.SERVER_URL}/summarize`, {
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
            this.progressContainer.style.display = 'none';
            this.summarizeBtn.disabled = true;
            this.downloadRawBtn.disabled = true;
            this.timerEl.textContent = '00:00:00';
            this.pasteText.value = '';
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
