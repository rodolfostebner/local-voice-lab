/**
 * Voice Lab — Frontend Client (M7: UX Conversacional)
 * 
 * Thin observer layer. All conversational logic lives on the backend.
 * Handles: WebSocket events, MediaRecorder PTT, text input, preferences.
 */

// ─── State ───────────────────────────────────────────────────
let ws = null;
let mediaRecorder = null;
let audioChunks = [];
let currentState = 'idle';
let reconnectTimer = null;
let streamingMsgEl = null;
let voiceEnabled = true;

// Audio Queue State
let audioQueue = [];
let isAudioPlaying = false;
let currentAudio = null;

const MODE_MODEL_MAP = {
    fast: 'qwen2.5:0.5b',
    standard: 'llama3.2:1b',
    premium: 'gemma3:4b',
};

// ─── Preferences (localStorage) ──────────────────────────────
function loadPrefs() {
    try {
        const prefs = JSON.parse(localStorage.getItem('voicelab_prefs'));
        if (prefs) {
            if (prefs.mode) modeSelect.value = prefs.mode;
            if (prefs.persona) personaSelect.value = prefs.persona;
            if (prefs.voiceEnabled !== undefined) {
                voiceEnabled = prefs.voiceEnabled;
                voiceToggle.classList.toggle('active', voiceEnabled);
                voiceToggle.textContent = voiceEnabled ? '🔊' : '🔇';
            }
        }
    } catch (e) { /* ignore */ }
}

function savePrefs() {
    localStorage.setItem('voicelab_prefs', JSON.stringify({
        mode: modeSelect.value,
        persona: personaSelect.value,
        voiceEnabled: voiceEnabled,
    }));
}


// ─── DOM Elements ────────────────────────────────────────────
const $ = (id) => document.getElementById(id);
const messagesEl      = $('messages');
const stateBanner     = $('state-banner');
const stateIcon       = $('state-icon');
const stateLabel      = $('state-label');
const pttBtn          = $('ptt-btn');
const micIcon         = $('mic-icon');
const stopIcon        = $('stop-icon');
const cancelBtn       = $('cancel-btn');
const personaSelect   = $('persona-select');
const modeSelect      = $('mode-select');
const voiceToggle     = $('voice-toggle');
const textInput       = $('text-input');
const sendBtn         = $('send-btn');
const modelLabel      = $('model-label');
const connectionDot   = $('connection-dot');
const connectionStatus = $('connection-status');
const clearBtn         = $('clear-btn');
const metricTTFT      = $('metric-ttft');
const metricTTFS      = $('metric-ttfs');
const metricTotal     = $('metric-total');
const metricChunks    = $('metric-chunks');


// ─── WebSocket ───────────────────────────────────────────────
function connect() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;

    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${location.host}/ws`;
    
    console.log(`[WS] Conectando a ${wsUrl}...`);
    connectionDot.className = 'dot reconnecting';
    connectionStatus.textContent = 'Conectando...';

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        connectionDot.className = 'dot connected';
        connectionDot.title = 'Conectado';
        connectionStatus.textContent = 'Online';
        console.log('[WS] Conectado');
        if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
        syncConfig();
    };

    ws.onclose = () => {
        connectionDot.className = 'dot disconnected';
        connectionDot.title = 'Desconectado';
        connectionStatus.textContent = 'Offline';
        console.log('[WS] Desconectado. Tentando reconectar...');
        if (!reconnectTimer) {
            reconnectTimer = setTimeout(connect, 3000);
        }
    };

    ws.onerror = (err) => {
        console.error('[WS] Erro:', err);
        ws.close();
    };

    ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        handleEvent(msg);
    };
}


// ─── Event Handler ───────────────────────────────────────────
function handleEvent(msg) {
    const { event, data } = msg;

    switch (event) {
        case 'connected':
            updateState(data.state);
            // Apenas atualiza a UI se não houver preferências salvas sendo sincronizadas
            if (data.config && !localStorage.getItem('voicelab_prefs')) {
                modelLabel.textContent = data.config.llm_model || 'gemma3:4b';
            }
            if (data.personas && personaSelect) {
                const currentVal = personaSelect.value;
                personaSelect.innerHTML = '';
                data.personas.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p.id;
                    opt.textContent = `👤 ${p.display_name}`;
                    personaSelect.appendChild(opt);
                });
                const prefs = JSON.parse(localStorage.getItem('voicelab_prefs') || '{}');
                if (prefs.persona) {
                    personaSelect.value = prefs.persona;
                } else if (currentVal) {
                    personaSelect.value = currentVal;
                }
                syncPersona();
            }
            break;

        case 'ack':
            break;

        case 'state_changed':
            updateState(data.to);
            break;

        case 'persona_changed':
            if (data.greeting) {
                addSystemMessage(`[${data.persona_id}] ${data.greeting}`);
            }
            break;

        case 'transcription_complete':
            addMessage('user', data.text);
            break;

        case 'llm_chunk':
            appendToStreaming(data.token);
            break;

        case 'tts_chunk_ready':
            console.log('[Audio] Chunk recebido:', data.audio_url);
            if (voiceEnabled && data.audio_url) {
                addToAudioQueue(data.audio_url);
            }
            break;

        case 'playback_finished':
            // Opcional: agora o frontend controla isso localmente
            break;

        case 'metrics_updated':
            if (data.ttft !== undefined) metricTTFT.textContent = data.ttft.toFixed(2) + 's';
            if (data.ttfs !== undefined) metricTTFS.textContent = data.ttfs.toFixed(2) + 's';
            break;

        case 'pipeline_complete':
            finalizeStreaming();
            if (data.total_time) metricTotal.textContent = data.total_time.toFixed(2) + 's';
            if (data.chunks_count !== undefined) metricChunks.textContent = data.chunks_count;
            break;

        case 'chat_cleared':
            messagesEl.innerHTML = '';
            addSystemMessage('Conversa limpa');
            resetMetrics();
            stopAudioPlayback();
            break;

        case 'error':
            addSystemMessage('⚠️ ' + (data.message || 'Erro desconhecido'));
            finalizeStreaming();
            break;
    }
}


// ─── State UI Updates ────────────────────────────────────────
const STATE_CONFIG = {
    idle:          { icon: '●', label: 'Pronto',          class: 'state-idle' },
    listening:     { icon: '◉', label: 'Ouvindo...',      class: 'state-listening' },
    transcribing:  { icon: '◎', label: 'Transcrevendo...', class: 'state-transcribing' },
    queued:        { icon: '⏳', label: 'Na Fila...',       class: 'state-queued' },
    thinking:      { icon: '◈', label: 'Pensando...',     class: 'state-thinking' },
    speaking:      { icon: '◆', label: 'Falando...',      class: 'state-speaking' },
    error:         { icon: '✕', label: 'Erro',            class: 'state-error' },
};

function updateState(newState) {
    currentState = newState;
    const cfg = STATE_CONFIG[newState] || STATE_CONFIG.idle;

    stateBanner.className = cfg.class;
    stateIcon.textContent = cfg.icon;
    stateLabel.textContent = cfg.label;

    const isIdle = newState === 'idle';
    pttBtn.disabled = !isIdle;
    sendBtn.disabled = !isIdle;
    textInput.disabled = !isIdle;
    cancelBtn.style.visibility = isIdle ? 'hidden' : 'visible';

    if (isIdle) {
        micIcon.style.display = '';
        stopIcon.style.display = 'none';
        pttBtn.classList.remove('recording');
        textInput.focus();
        // REMOVIDO: stopAudioPlayback() daqui para não matar a fila gerada assíncronamente.
    }
}


// ─── Audio Playback Queue ────────────────────────────────────
function addToAudioQueue(url) {
    audioQueue.push(url);
    if (!isAudioPlaying) {
        playNextInQueue();
    }
}

function playNextInQueue() {
    if (audioQueue.length === 0) {
        console.log('[Audio] Fila vazia.');
        isAudioPlaying = false;
        currentAudio = null;
        return;
    }

    isAudioPlaying = true;
    const url = audioQueue.shift();
    console.log('[Audio] Reproduzindo:', url);
    
    // Resolve URL relativa se necessário (garante absoluto para mobile)
    const absoluteUrl = url.startsWith('http') ? url : window.location.origin + url;
    currentAudio = new Audio(absoluteUrl);
    
    currentAudio.onended = () => {
        console.log('[Audio] Chunk finalizado.');
        playNextInQueue();
    };

    currentAudio.onerror = (err) => {
        console.error("[Audio] Erro no carregamento:", url, err);
        playNextInQueue();
    };

    currentAudio.play().catch(err => {
        console.warn("[Audio] Falha no play (User interaction required?):", err);
        // Não pula a fila imediatamente para dar chance de retomar com clique se for bloqueio de autoplay
        isAudioPlaying = false; 
    });
}

function stopAudioPlayback() {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.src = "";
        currentAudio = null;
    }
    audioQueue = [];
    isAudioPlaying = false;
}


// ─── Messages ────────────────────────────────────────────────
function addMessage(role, text) {
    const el = document.createElement('div');
    el.className = `message ${role}`;
    el.textContent = text;
    messagesEl.appendChild(el);
    scrollToBottom();
}

function addSystemMessage(text, isError = false) {
    const el = document.createElement('div');
    el.className = `message system ${isError ? 'error' : ''}`;
    el.textContent = text;
    messagesEl.appendChild(el);
    scrollToBottom(true);
}

function appendToStreaming(token) {
    if (!streamingMsgEl) {
        streamingMsgEl = document.createElement('div');
        streamingMsgEl.className = 'message assistant streaming';
        messagesEl.appendChild(streamingMsgEl);
    }
    // Adiciona o token sem causar saltos bruscos
    streamingMsgEl.textContent += token;
    scrollToBottom();
}

function finalizeStreaming() {
    if (streamingMsgEl) {
        streamingMsgEl.classList.remove('streaming');
        streamingMsgEl = null;
    }
}

function scrollToBottom(force = false) {
    const chatArea = $('chat-area');
    const isNearBottom = chatArea.scrollHeight - chatArea.scrollTop - chatArea.clientHeight < 100;
    
    if (force || isNearBottom) {
        chatArea.scrollTo({
            top: chatArea.scrollHeight,
            behavior: 'smooth'
        });
    }
}


// ─── Text Input ──────────────────────────────────────────────
function sendTextMessage() {
    const text = textInput.value.trim();
    if (!text || currentState !== 'idle') return;

    // Show user message via transcription_complete event (Source of Truth)
    textInput.value = '';

    // Reset metrics
    resetMetrics();

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'text_message', text: text }));
    }
}


// ─── Push-to-Talk ────────────────────────────────────────────
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
        audioChunks = [];

        mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) audioChunks.push(e.data);
        };

        mediaRecorder.onstop = async () => {
            stream.getTracks().forEach(t => t.stop());
            const blob = new Blob(audioChunks, { type: 'audio/webm' });
            const reader = new FileReader();
            reader.onloadend = () => {
                const base64 = reader.result.split(',')[1];
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ action: 'audio_data', audio: base64 }));
                }
            };
            reader.readAsDataURL(blob);
        };

        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: 'start_listening' }));
        }

        mediaRecorder.start();
        pttBtn.classList.add('recording');
        micIcon.style.display = 'none';
        stopIcon.style.display = '';
        resetMetrics();

    } catch (err) {
        addSystemMessage('⚠️ Microfone bloqueado. Verifique as permissões de HTTPS no seu navegador.', true);
        console.error('[Audio] Erro:', err);
        updateState('idle');
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        pttBtn.classList.remove('recording');
        micIcon.style.display = '';
        stopIcon.style.display = 'none';
    }
}

function resetMetrics() {
    metricTTFT.textContent = '—';
    metricTTFS.textContent = '—';
    metricTotal.textContent = '—';
    metricChunks.textContent = '—';
}


// ─── Config Sync ─────────────────────────────────────────────
function syncConfig() {
    const mode = modeSelect.value;
    const model = MODE_MODEL_MAP[mode];
    modelLabel.textContent = model;

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            action: 'config',
            mode: mode,
            voice_enabled: voiceEnabled,
        }));
    }
}

function syncPersona() {
    if (ws && ws.readyState === WebSocket.OPEN && personaSelect.value) {
        ws.send(JSON.stringify({
            action: 'set_persona',
            persona_id: personaSelect.value,
        }));
    }
}


// ─── Event Listeners ─────────────────────────────────────────

// Text input
textInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        stopAudioPlayback(); // Interrompe fala atual se o usuário mandar novo texto
        sendTextMessage();
    }
});

sendBtn.addEventListener('click', sendTextMessage);

// PTT
pttBtn.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    if (currentState === 'idle') {
        stopAudioPlayback(); // Interrompe fala atual se o usuário quiser falar
        startRecording();
    }
});

pttBtn.addEventListener('pointerup', (e) => {
    e.preventDefault();
    stopRecording();
});

pttBtn.addEventListener('pointerleave', () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') stopRecording();
});

// Cancel
cancelBtn.addEventListener('click', () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'cancel' }));
    }
    finalizeStreaming();
    stopAudioPlayback();
});

// Mode selector
modeSelect.addEventListener('change', () => {
    syncConfig();
    savePrefs();
});

// Persona selector
if (personaSelect) {
    personaSelect.addEventListener('change', () => {
        syncPersona();
        savePrefs();
    });
}

// Voice toggle
voiceToggle.addEventListener('click', () => {
    voiceEnabled = !voiceEnabled;
    voiceToggle.classList.toggle('active', voiceEnabled);
    voiceToggle.textContent = voiceEnabled ? '🔊' : '🔇';
    syncConfig();
    savePrefs();
});

// Clear Chat
clearBtn.addEventListener('click', () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: 'clear_chat' }));
    } else {
        // Fallback local se estiver offline
        messagesEl.innerHTML = '';
        addSystemMessage('Conversa limpa (local)');
        resetMetrics();
    }
});


// ─── Init ────────────────────────────────────────────────────
loadPrefs();
connect();
