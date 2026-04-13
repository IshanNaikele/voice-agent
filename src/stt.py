import os
import time
from groq import Groq
from src.logger import log_event

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def transcribe_audio(audio_source) -> tuple[str, float]:
    """
    Accepts a file path (str) or byte-stream.
    Returns (transcribed_text, latency_ms).
    """
    start = time.time()

    if isinstance(audio_source, str):
        with open(audio_source, "rb") as f:
            audio_bytes = f.read()
            filename = os.path.basename(audio_source)
    else:
        audio_bytes = audio_source.read()
        filename = "audio.wav"

    transcription = client.audio.transcriptions.create(
        model="whisper-large-v3",
        file=(filename, audio_bytes),
        response_format="text"
    )

    latency_ms = (time.time() - start) * 1000
    text = transcription.strip()

    log_event("STT", f"Transcribed: '{text}'", latency_ms)
    return text, latency_ms