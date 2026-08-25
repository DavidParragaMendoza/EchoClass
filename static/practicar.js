class PracticeApp {
    constructor() {
        this.ws = null;
        this.mediaRecorder = null;
        this.audioStream = null;
        this.isRecording = false;
        this.startTime = null;
        this.timerInterval = null;
        this.recordingInterval = null;
        this.accumulatedTranscription = '';

        // Configuración del servidor remoto (RunPod).
        // Editar static/config.js con la URL del pod cuando esté activo.
        // Si window.ECHOCLASS_CONFIG no está definido, cae en window.location (modo local).
        const _cfg = window.ECHOCLASS_CONFIG || {};
        this.SERVER_URL = _cfg.serverUrl
            ? _cfg.serverUrl.replace(/\/+$/, '')
            : window.location.origin;
        this.WS_URL = _cfg.wsUrl
            ? _cfg.wsUrl.replace(/\/+$/, '')
            : (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host;

        this.languageNotes = {
            es: 'ℹ️ <strong>Precisión de Whisper en Español:</strong> <strong>Muy Alta (~95%+)</strong>. Excelente reconocimiento fonético y sintáctico.',
            en: 'ℹ️ <strong>Precisión de Whisper en Inglés:</strong> <strong>Excelente (~97%+)</strong>. Máxima precisión por volumen de entrenamiento en el modelo.',
            pt: 'ℹ️ <strong>Precisión de Whisper en Portugués (Brasil):</strong> <strong>Muy Alta (~93%+)</strong>. Gran reconocimiento del acento brasileiro y variaciones regionales.',
            zh: 'ℹ️ <strong>Precisión de Whisper en Chino Mandarín:</strong> <strong>Alta (~88% - 92%)</strong>. Buena detección; procura vocalizar tonos claramente.',
            ru: 'ℹ️ <strong>Precisión de Whisper en Ruso:</strong> <strong>Buena (~91% - 94%)</strong>. Reconocimiento sólido en alfabeto cirílico y consonantes complejas.'
        };

        this.initElements();
        this.initEventListeners();
        this.updateLanguageNote();
    }

    initElements() {
        this.targetWordInput = document.getElementById('targetWord');
        this.languageSelect = document.getElementById('languageSelect');
        this.languageInfoNote = document.getElementById('languageInfoNote');
        this.startRecordBtn = document.getElementById('startRecordBtn');
        this.stopRecordBtn = document.getElementById('stopRecordBtn');
        this.statusEl = document.getElementById('status');
        this.timerEl = document.getElementById('timer');
        this.transcriptionEl = document.getElementById('transcriptionEl');

        this.evaluationCard = document.getElementById('evaluationCard');
        this.scoreBadge = document.getElementById('scoreBadge');
        this.scoreTitle = document.getElementById('scoreTitle');
        this.scoreDescription = document.getElementById('scoreDescription');
        this.expectedTextDisplay = document.getElementById('expectedTextDisplay');
        this.transcribedTextDisplay = document.getElementById('transcribedTextDisplay');
    }

    initEventListeners() {
        this.languageSelect.addEventListener('change', () => {
            this.updateLanguageNote();
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.sendLanguageConfig();
            }
        });

        this.startRecordBtn.addEventListener('click', () => this.startRecording());
        this.stopRecordBtn.addEventListener('click', () => this.stopRecording());
    }

    updateLanguageNote() {
        const lang = this.languageSelect.value;
        this.languageInfoNote.innerHTML = this.languageNotes[lang] || this.languageNotes['es'];
    }

    sendLanguageConfig() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const selectedLang = this.languageSelect.value;
            this.ws.send(JSON.stringify({
                type: 'config',
                language: selectedLang
            }));
            console.log(`🌐 Idioma configurado enviado a WebSocket: ${selectedLang}`);
        }
    }

    async connectWebSocket() {
        return new Promise((resolve, reject) => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.sendLanguageConfig();
                resolve();
                return;
            }

            const wsUrl = this.WS_URL;
            
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('📡 WebSocket conectado para Práctica');
                this.sendLanguageConfig();
                resolve();
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'transcription' && data.text) {
                        this.handleTranscriptionReceived(data.text);
                    }
                } catch (e) {
                    console.error('Error parseando mensaje WS:', e);
                }
            };

            this.ws.onerror = (err) => {
                console.error('❌ Error en WebSocket:', err);
                this.statusEl.textContent = '❌ Error de conexión';
                this.statusEl.className = 'status status-error';
                reject(new Error('No se pudo establecer la conexión WebSocket con el servidor.'));
            };

            this.ws.onclose = () => {
                console.log('🔌 WebSocket cerrado');
            };
        });
    }

    async startRecording() {
        const targetText = this.targetWordInput.value.trim();
        if (!targetText) {
            alert('Por favor ingresa una palabra o frase a practicar antes de grabar.');
            this.targetWordInput.focus();
            return;
        }

        try {
            this.statusEl.textContent = '🔄 Conectando servidor...';
            await this.connectWebSocket();
        } catch (wsErr) {
            alert('No se pudo conectar al servidor de transcripción (/ws). Verifica que el servidor (start.bat) esté ejecutándose.');
            return;
        }

        try {
            this.audioStream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    channelCount: 1,
                    sampleRate: 16000
                }
            });

            this.accumulatedTranscription = '';
            this.transcriptionEl.innerHTML = '<p class="placeholder">Escuchando pronunciación...</p>';
            this.evaluationCard.style.display = 'none';

            this.mediaRecorder = new MediaRecorder(this.audioStream, {
                mimeType: this.getSupportedMimeType()
            });

            // Acumulamos los chunks y enviamos un WebM completo al parar.
            // Enviar chunks parciales con start(1000) rompe el header EBML
            // y FFmpeg no puede parsear los fragmentos intermedios.
            const audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                const mimeType = this.getSupportedMimeType() || 'audio/webm';
                const audioBlob = new Blob(audioChunks, { type: mimeType });
                console.log(`📤 Enviando grabación completa: ${audioBlob.size} bytes`);
                if (audioBlob.size > 5000 && this.ws && this.ws.readyState === WebSocket.OPEN) {
                    audioBlob.arrayBuffer().then(buffer => {
                        this.ws.send(buffer);
                        console.log('✅ Audio enviado al servidor para transcripción');
                    }).catch(err => console.error('❌ Error enviando audio:', err));
                } else {
                    console.warn('⚠️ Grabación demasiado corta o WebSocket desconectado');
                }
            };

            this.mediaRecorder.start(); // Sin timeslice → graba todo hasta stop()
            this.isRecording = true;
            this.startTime = Date.now();

            this.startTimer();
            this.updateRecordingUI(true);

        } catch (err) {
            console.error('❌ Error al acceder al micrófono:', err);
            alert('No se pudo acceder al micrófono. Por favor verifica los permisos en la barra de direcciones del navegador.');
            this.statusEl.textContent = '❌ Error de micrófono';
        }
    }

    getSupportedMimeType() {
        const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus'];
        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) return type;
        }
        return '';
    }

    stopRecording() {
        if (!this.isRecording) return;

        this.isRecording = false;

        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }

        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
        }

        this.stopTimer();
        this.updateRecordingUI(false);

        // Dar 1.5s para recibir la transcripción final antes de evaluar si está vacía
        setTimeout(() => {
            this.evaluatePronunciation();
        }, 1500);
    }

    handleTranscriptionReceived(text) {
        if (!text) return;
        
        if (!this.accumulatedTranscription) {
            this.accumulatedTranscription = text;
        } else {
            this.accumulatedTranscription += ' ' + text;
        }

        this.transcriptionEl.innerHTML = `<p style="font-weight: 500; font-size: 1.1em; color: var(--text-primary);">${this.accumulatedTranscription}</p>`;
        
        // Evaluar pronunciación en tiempo real
        this.evaluatePronunciation();
    }

    evaluatePronunciation() {
        const expected = this.targetWordInput.value.trim();
        const actual = this.accumulatedTranscription.trim();

        if (!expected) return;

        this.expectedTextDisplay.textContent = expected;
        this.transcribedTextDisplay.textContent = actual || '(Sin audio detectado)';

        const { score, level, description, badgeClass } = this.calculateScore(expected, actual);

        this.scoreBadge.textContent = `${score}/10`;
        this.scoreBadge.className = `score-badge ${badgeClass}`;
        this.scoreTitle.textContent = level;
        this.scoreDescription.textContent = description;

        this.evaluationCard.style.display = 'block';
    }

    calculateScore(target, transcribed) {
        if (!transcribed || transcribed === '(Sin audio detectado)') {
            return {
                score: 1,
                level: 'Sin Coincidencia',
                description: 'No se escuchó audio inteligible o no hubo sonido capturado.',
                badgeClass: 'score-low'
            };
        }

        const cleanTarget = this.normalizeText(target);
        const cleanTranscribed = this.normalizeText(transcribed);

        if (cleanTarget === cleanTranscribed) {
            return {
                score: 10,
                level: '¡Excelente! 🎯',
                description: 'Pronunciación perfecta. Coincidencia exacta con la palabra u oración deseada.',
                badgeClass: 'score-10'
            };
        }

        const maxLen = Math.max(cleanTarget.length, cleanTranscribed.length);
        if (maxLen === 0) {
            return { score: 1, level: 'Sin Coincidencia', description: 'Texto vacío.', badgeClass: 'score-low' };
        }

        const distance = this.getLevenshteinDistance(cleanTarget, cleanTranscribed);
        const similarity = Math.max(0, 1 - (distance / maxLen));

        if (similarity >= 0.95) {
            return { score: 10, level: '¡Excelente!', description: 'Pronunciación casi perfecta con variaciones imperceptibles.', badgeClass: 'score-10' };
        } else if (similarity >= 0.85) {
            return { score: 9, level: '¡Sobresaliente!', description: 'Pronunciación muy clara. Pequeña variación de acento o consonante.', badgeClass: 'score-9' };
        } else if (similarity >= 0.75) {
            return { score: 8, level: '¡Muy Bueno!', description: 'Comprensión alta con ligera imprecisión fonética.', badgeClass: 'score-8' };
        } else if (similarity >= 0.65) {
            return { score: 7, level: 'Bueno', description: 'Comprensible pero con acento o desviación en algunas letras.', badgeClass: 'score-7' };
        } else if (similarity >= 0.55) {
            return { score: 6, level: 'Aceptable', description: 'Se entiende la intención, pero la pronunciación requiere mejorar.', badgeClass: 'score-6' };
        } else if (similarity >= 0.45) {
            return { score: 5, level: 'Regular', description: 'Aproximación básica; varias sílabas resultaron deformadas.', badgeClass: 'score-5' };
        } else if (similarity >= 0.35) {
            return { score: 4, level: 'Deficiente', description: 'Pronunciación confusa o palabra escuchada de forma incompleta.', badgeClass: 'score-low' };
        } else if (similarity >= 0.25) {
            return { score: 3, level: 'Insuficiente', description: 'Ruido o sonido alejado de la palabra objetivo.', badgeClass: 'score-low' };
        } else if (similarity >= 0.10) {
            return { score: 2, level: 'Muy Bajo', description: 'Prácticamente no coincide con la palabra esperada.', badgeClass: 'score-low' };
        } else {
            return { score: 1, level: 'Sin Coincidencia', description: 'Lo que se escuchó no coincide con la palabra deseada.', badgeClass: 'score-low' };
        }
    }

    normalizeText(text) {
        return text
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '') // Eliminar diacríticos/acentos
            .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()?'"¡!¿?]/g, '') // Eliminar puntuación
            .replace(/\s+/g, ' ')
            .trim();
    }

    getLevenshteinDistance(a, b) {
        const matrix = Array.from({ length: a.length + 1 }, () => Array(b.length + 1).fill(0));
        for (let i = 0; i <= a.length; i++) matrix[i][0] = i;
        for (let j = 0; j <= b.length; j++) matrix[0][j] = j;
        for (let i = 1; i <= a.length; i++) {
            for (let j = 1; j <= b.length; j++) {
                const cost = a[i - 1] === b[j - 1] ? 0 : 1;
                matrix[i][j] = Math.min(
                    matrix[i - 1][j] + 1,
                    matrix[i][j - 1] + 1,
                    matrix[i - 1][j - 1] + cost
                );
            }
        }
        return matrix[a.length][b.length];
    }

    startTimer() {
        this.timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            const minutes = String(Math.floor(elapsed / 60)).padStart(2, '0');
            const seconds = String(elapsed % 60).padStart(2, '0');
            this.timerEl.textContent = `00:${minutes}:${seconds}`;
        }, 1000);
    }

    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    updateRecordingUI(isRecording) {
        this.startRecordBtn.disabled = isRecording;
        this.stopRecordBtn.disabled = !isRecording;
        this.targetWordInput.disabled = isRecording;
        this.languageSelect.disabled = isRecording;

        if (isRecording) {
            this.statusEl.textContent = '🔴 Grabando y evaluando...';
            this.statusEl.className = 'status status-recording';
        } else {
            this.statusEl.textContent = '🟢 Grabación finalizada';
            this.statusEl.className = 'status status-ready';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.practiceApp = new PracticeApp();
});
