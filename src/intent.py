import os
import json
import time
from groq import Groq
from src.schemas import Task, AgentResponse
from src.logger import log_event

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are a strict JSON routing agent. Analyze the user's input and return ONLY valid JSON.
No explanation. No markdown. No extra text.

Available intents:
- create_file     → parameters: { filename: str, content: str }
- write_code      → parameters: { filename: str, language: str, description: str }
- summarize       → parameters: { text: str, save_to: str | null }
- chat            → parameters: { message: str }

Rules:
- Always return a JSON object: { "tasks": [ ...list of task objects... ] }
- Each task: { "intent": str, "parameters": {}, "confidence": float (0.0-1.0) }
- If the user gives multiple commands, return multiple tasks in the list.
- If unclear, default to the "chat" intent.
- confidence reflects how sure you are about the intent.

Example output:
{
  "tasks": [
    { "intent": "write_code", "parameters": { "filename": "retry.py", "language": "python", "description": "a retry function with exponential backoff" }, "confidence": 0.97 }
  ]
}
"""


def classify_intent(
    transcribed_text: str,
    session_memory: list[dict] = []
) -> tuple[AgentResponse, float]:
    """
    Returns (AgentResponse, latency_ms).
    session_memory: last N interactions as [{"role": ..., "content": ...}]
    """
    start = time.time()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += session_memory[-6:]  # last 3 pairs (user+assistant)
    messages.append({"role": "user", "content": transcribed_text})

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.1,
        max_tokens=1000
    )

    latency_ms = (time.time() - start) * 1000
    raw_json = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw_json)
        tasks = [Task(**t) for t in parsed.get("tasks", [])]
    except Exception as e:
        log_event("INTENT", f"Parse error: {e}. Falling back to chat.")
        tasks = [Task(
            intent="chat",
            parameters={"message": transcribed_text},
            confidence=0.5
        )]

    agent_response = AgentResponse(tasks=tasks, raw_text=transcribed_text)
    log_event("INTENT", f"Detected {len(tasks)} task(s)", latency_ms)
    return agent_response, latency_ms