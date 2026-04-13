from dataclasses import dataclass, field
from datetime import datetime
from src.schemas import ActionResult


@dataclass
class MemoryEntry:
    timestamp: str
    transcription: str
    intents: list[str]
    results: list[ActionResult]


class SessionMemory:
    def __init__(self, max_chat_pairs: int = 3):
        self.action_history: list[MemoryEntry] = []
        self.chat_history: list[dict] = []   # OpenAI-style message dicts
        self.max_chat_pairs = max_chat_pairs

    def add(self, transcription: str, intents: list[str], results: list[ActionResult]):
        entry = MemoryEntry(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            transcription=transcription,
            intents=intents,
            results=results
        )
        self.action_history.append(entry)

        # Keep rolling chat context for LLM
        self.chat_history.append({"role": "user", "content": transcription})
        assistant_reply = " | ".join(
            r.output or r.message for r in results
        )
        self.chat_history.append({"role": "assistant", "content": assistant_reply})

        # Trim to last N pairs
        max_msgs = self.max_chat_pairs * 2
        if len(self.chat_history) > max_msgs:
            self.chat_history = self.chat_history[-max_msgs:]

    def get_chat_context(self) -> list[dict]:
        return self.chat_history

    def get_action_history(self) -> list[MemoryEntry]:
        return self.action_history

    def clear(self):
        self.action_history.clear()
        self.chat_history.clear()