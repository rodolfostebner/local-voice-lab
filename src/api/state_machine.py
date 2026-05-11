"""
Conversational State Machine - Source of Truth.

Nenhuma camada externa (API, WebSocket, Frontend) pode alterar
o estado do pipeline diretamente. Todas as mudancas passam por
esta classe, que valida transicoes e emite eventos.
"""
import time
import threading
import uuid
from enum import Enum
from typing import Callable, List, Optional


class ConversationState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"
    THINKING = "thinking"
    QUEUED = "queued"
    SPEAKING = "speaking"
    ERROR = "error"


# Transicoes validas: estado_atual -> [estados_permitidos]
VALID_TRANSITIONS = {
    ConversationState.IDLE:          [ConversationState.LISTENING, ConversationState.ERROR],
    ConversationState.LISTENING:     [ConversationState.TRANSCRIBING, ConversationState.IDLE, ConversationState.ERROR],
    ConversationState.TRANSCRIBING:  [ConversationState.THINKING, ConversationState.QUEUED, ConversationState.IDLE, ConversationState.ERROR],
    ConversationState.QUEUED:        [ConversationState.THINKING, ConversationState.IDLE, ConversationState.ERROR],
    ConversationState.THINKING:      [ConversationState.SPEAKING, ConversationState.IDLE, ConversationState.ERROR],
    ConversationState.SPEAKING:      [ConversationState.IDLE, ConversationState.ERROR],
    ConversationState.ERROR:         [ConversationState.IDLE],
}


class StateEvent:
    """Evento estruturado emitido a cada transicao de estado."""
    def __init__(self, event_type: str, data: dict = None, client_id: str = None):
        self.event_type = event_type
        self.data = data or {}
        self.timestamp = time.time()
        self.client_id = client_id

    def to_dict(self):
        return {
            "event": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp,
            "client_id": self.client_id,
        }


class ConversationStateMachine:
    """
    Source of Truth para o estado conversacional do pipeline.
    Thread-safe. Emite eventos estruturados via callbacks.
    """

    def __init__(self):
        self._state = ConversationState.IDLE
        self._lock = threading.Lock()
        self._listeners: List[Callable[[StateEvent], None]] = []
        self._history: List[dict] = []
        self.active_cycle_id: Optional[str] = None

    def start_new_cycle(self) -> str:
        """Inicia um novo ciclo de conversação, orfanando tasks antigas."""
        with self._lock:
            self.active_cycle_id = str(uuid.uuid4())
            print(f"\n[CYCLE] Novo ciclo iniciado: {self.active_cycle_id}")
            return self.active_cycle_id

    @property
    def state(self) -> ConversationState:
        return self._state

    def add_listener(self, callback: Callable[[StateEvent], None]):
        """Registra um callback para receber eventos de estado."""
        self._listeners.append(callback)

    def _emit(self, event: StateEvent):
        """Notifica todos os listeners sobre um evento."""
        self._history.append(event.to_dict())
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                print(f"[StateMachine] Erro em listener: {e}")

    def transition_to(self, new_state: ConversationState, context: dict = None, client_id: str = None, cycle_id: str = None) -> bool:
        """
        Tenta transicionar para um novo estado.
        Retorna True se a transicao foi valida, False caso contrario.
        """
        with self._lock:
            if cycle_id is not None and cycle_id != self.active_cycle_id:
                print(f"[LATE_EVENT] Ignorando transicao {self._state.value} -> {new_state.value}. Cycle {cycle_id} obsoleto.")
                return False

            allowed = VALID_TRANSITIONS.get(self._state, [])
            if new_state not in allowed:
                print(f"[STATE_GUARD] Transicao INVALIDA bloqueada: {self._state.value} -> {new_state.value}")
                return False

            old_state = self._state
            self._state = new_state
            print(f"[StateMachine] {old_state.value} -> {new_state.value} (Cycle: {self.active_cycle_id})")

            self._emit(StateEvent("state_changed", {
                "from": old_state.value,
                "to": new_state.value,
                **(context or {}),
            }, client_id=client_id))
            return True

    def emit_event(self, event_type: str, data: dict = None, client_id: str = None, cycle_id: str = None):
        """Emite um evento arbitrario (metricas, chunks, erros) sem mudar estado."""
        with self._lock:
            if cycle_id is not None and cycle_id != self.active_cycle_id:
                print(f"[LATE_EVENT] Evento {event_type} descartado. Cycle {cycle_id} obsoleto.")
                return
            self._emit(StateEvent(event_type, data, client_id=client_id))

    def reset(self):
        """Forca retorno ao IDLE (uso em erro/recovery)."""
        with self._lock:
            self._state = ConversationState.IDLE
            self._emit(StateEvent("state_changed", {
                "from": "reset",
                "to": ConversationState.IDLE.value,
            }))

    def get_history(self) -> List[dict]:
        """Retorna o historico de eventos para persistencia."""
        return list(self._history)
