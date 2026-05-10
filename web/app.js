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
            if (prefs.voice) voiceSelect.value = prefs.voice;
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
        voice: voiceSelect.value,
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
const modeSelect      = $('mode-select');
const voiceSelect     = $('voice-select');
const voiceToggle     = $('voice-toggle');
const textInput       = $('text-input');
const sendBtn         = $('send-btn');
const modelLabel      = $('model-label');
const connectionDot   = $('connection-dot');
const metricTTFT      = $('metric-ttft');
const metricTTFS      = $('metric-ttfs');
const metricTotal     = $('metric-total');
const metricChunks    = $('metric-chunks');


// ─── WebSocket ───────────────────────────────────────────────
function connect() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${location.host}/ws`);

    ws.onopen = () => {
        connectionDot.className = 'dot connected';
        connectionDot.title = 'Conectado';
        addSystemMessage('Conectado ao Voice Lab');
        if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }

        // Sync preferences to backend
        syncConfig();
    };

    ws.onclose = () => {
        connectionDot.className = 'dot disconnected';
        connectionDot.title = 'Desconectado';
        reconnectTimer = setTimeout(connect, 3000);
    };

    ws.onerror = () => { ws.close(); };

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
            if (data.config) {
                modelLabel.textContent = data.config.llm_model || 'gemma3:4b';
            }
            break;

        case 'ack':
            break;

        case 'state_changed':
            updateState(data.to);
            break;

        case 'transcription_complete':
            addMessage('user', data.text);
            break;

        case 'llm_chunk':
            appendToStreaming(data.token);
            break;

        case 'tts_chunk_ready':
            break;

        case 'playback_finished':
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
    }
}


// ─── Messages ────────────────────────────────────────────────
function addMessage(role, text) {
    const el = document.createElement('div');
    el.className = `message ${role}`;
    el.textContent = text;
    messagesEl.appendChild(el);
    scrollToBottom();
}

function addSystemMessage(text) {
    const el = document.createElement('div');
    el.className = 'message system';
    el.textContent = text;
    messagesEl.appendChild(el);
    scrollToBottom();
}

function appendToStreaming(token) {
    if (!streamingMsgEl) {
        streamingMsgEl = document.createElement('div');
        streamingMsgEl.className = 'message assistant streaming';
        messagesEl.appendChild(streamingMsgEl);
    }
    streamingMsgEl.textContent += token;
    scrollToBottom();
}

function finalizeStreaming() {
    if (streamingMsgEl) {
        streamingMsgEl.classList.remove('streaming');
        streamingMsgEl = null;
    }
}

function scrollToBottom() {
    const chatArea = $('chat-area');
    chatArea.scrollTop = chatArea.scrollHeight;
}


// ─── Text Input ──────────────────────────────────────────────
function sendTextMessage() {
    const text = textInput.value.trim();
    if (!text || currentState !== 'idle') return;

    // Show user message immediately
    addMessage('user', text);
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
        addSystemMessage('⚠️ Microfone não disponível: ' + err.message);
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

    fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            mode: mode,
            tts_voice: voiceSelect.value,
            voice_enabled: voiceEnabled,
        }),
    });
}


// ─── Event Listeners ─────────────────────────────────────────

// Text input
textInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendTextMessage();
    }
});

sendBtn.addEventListener('click', sendTextMessage);

// PTT
pttBtn.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    if (currentState === 'idle') startRecording();
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
});

// Mode selector
modeSelect.addEventListener('change', () => {
    syncConfig();
    savePrefs();
});

// Voice selector
voiceSelect.addEventListener('change', () => {
    syncConfig();
    savePrefs();
});

// Voice toggle
voiceToggle.addEventListener('click', () => {
    voiceEnabled = !voiceEnabled;
    voiceToggle.classList.toggle('active', voiceEnabled);
    voiceToggle.textContent = voiceEnabled ? '🔊' : '🔇';
    syncConfig();
    savePrefs();
});


// ─── Init ────────────────────────────────────────────────────
loadPrefs();
connect();
