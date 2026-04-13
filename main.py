# main.py
import os
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

from src.stt import transcribe_audio
from src.intent import classify_intent
from src.tools import execute_task
from src.memory import SessionMemory
from src.schemas import Task, ActionResult

app = FastAPI(title="Voice Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single session memory (per server instance)
memory = SessionMemory(max_chat_pairs=3)


# ── Response models ────────────────────────────────────────────────────────────
class TranscribeResponse(BaseModel):
    transcription: str
    stt_latency_ms: float


class IntentResponse(BaseModel):
    transcription: str
    tasks: List[Task]
    intent_latency_ms: float


class ExecuteRequest(BaseModel):
    transcription: str
    tasks: List[Task]


class ExecuteResponse(BaseModel):
    results: List[ActionResult]


class HistoryEntry(BaseModel):
    timestamp: str
    transcription: str
    intents: List[str]


class HistoryResponse(BaseModel):
    history: List[HistoryEntry]


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(file: UploadFile = File(...)):
    """Stage 1: Audio → Text via Groq Whisper."""
    allowed = {".wav", ".mp3", ".m4a", ".ogg"}
    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    audio_bytes = await file.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        transcription, latency = transcribe_audio(tmp_path)
    finally:
        os.unlink(tmp_path)

    return TranscribeResponse(
        transcription=transcription,
        stt_latency_ms=round(latency, 2)
    )


@app.post("/classify", response_model=IntentResponse)
async def classify(payload: dict):
    """Stage 2: Text → Intent classification via Groq Llama."""
    transcription = payload.get("transcription", "")
    if not transcription:
        raise HTTPException(status_code=400, detail="transcription is required")

    agent_response, latency = classify_intent(
        transcription,
        session_memory=memory.get_chat_context()
    )

    return IntentResponse(
        transcription=transcription,
        tasks=agent_response.tasks,
        intent_latency_ms=round(latency, 2)
    )


@app.post("/execute", response_model=ExecuteResponse)
async def execute(payload: ExecuteRequest):
    """Stage 3: Execute tasks and store in memory."""
    results = []
    for task in payload.tasks:
        result = execute_task(task)
        results.append(result)

    intents = [t.intent for t in payload.tasks]
    memory.add(payload.transcription, intents, results)

    return ExecuteResponse(results=results)


@app.get("/history", response_model=HistoryResponse)
async def get_history():
    """Return session action history."""
    entries = memory.get_action_history()
    return HistoryResponse(history=[
        HistoryEntry(
            timestamp=e.timestamp,
            transcription=e.transcription,
            intents=e.intents
        )
        for e in entries
    ])


@app.delete("/history")
async def clear_history():
    """Clear session memory."""
    memory.clear()
    return {"message": "History cleared."}


@app.get("/health")
async def health():
    return {"status": "ok"}