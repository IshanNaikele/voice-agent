# 🎙️ Voice-Controlled Local AI Agent

A voice-powered AI agent that transcribes audio, classifies user intent, and executes local actions — all through a clean, modern UI built with Streamlit and FastAPI.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Streamlit UI  (app.py)               │
│   Audio Input → Upload / Microphone                         │
│   Output      → Transcription · Intent · Action · Result    │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP (REST)
┌─────────────────────▼───────────────────────────────────────┐
│                     FastAPI Backend  (main.py)              │
│                                                             │
│  POST /transcribe  →  src/stt.py   →  Groq Whisper API     │
│  POST /classify    →  src/intent.py →  Groq Llama-3 API    │
│  POST /execute     →  src/tools.py →  Local File System     │
│  GET  /history     →  src/memory.py → Session Memory        │
└─────────────────────────────────────────────────────────────┘
```

### Pipeline Flow

```
Audio File / Mic Recording
        │
        ▼
  [STT]  Groq Whisper-large-v3
        │  → Transcribed text
        ▼
  [Intent]  Groq Llama-3.1-8b-instant
        │  → JSON task list  { intent, parameters, confidence }
        ▼
  [Tools]  Local execution
        │  → create_file · write_code · summarize · chat
        ▼
  [UI]  Display results + update session history
```

---

## 🤖 Models Used

| Stage | Model | Provider | Why |
|---|---|---|---|
| Speech-to-Text | `whisper-large-v3` | Groq API | See hardware note below |
| Intent Classification | `llama-3.1-8b-instant` | Groq API | Fast, low-latency JSON routing |
| Code Generation | `llama-3.1-8b-instant` | Groq API | Sufficient for code tasks |
| Summarization | `llama-3.1-8b-instant` | Groq API | Higher quality for text summarization |

### ⚠️ Hardware Workaround Note

> **Why Groq API instead of a local Whisper model?**
>
> The assignment recommends running Whisper locally via HuggingFace (e.g., `openai/whisper-large-v3`). However, running this model locally requires a GPU with at least 6–8 GB of VRAM for reasonable inference speed. My development machine does not meet this requirement — running it on CPU results in 30–60+ seconds of latency per audio clip, which makes the UI unusable in practice.
>
> **Solution:** I use Groq's hosted Whisper API, which provides the same `whisper-large-v3` model with ~500–800 ms latency. The model is identical — only the compute location differs. This is documented as an acceptable alternative in the assignment brief.

---

## ✨ Features

### Core Requirements
- ✅ **Audio Input** — Upload `.wav`, `.mp3`, `.m4a`, `.ogg` files or record directly from the microphone
- ✅ **Speech-to-Text** — Groq Whisper-large-v3 with latency tracking
- ✅ **Intent Classification** — Groq Llama-3 with structured JSON output
- ✅ **4 Supported Intents** — `create_file`, `write_code`, `summarize`, `chat`
- ✅ **File Safety** — All file operations restricted to the `output/` directory
- ✅ **Clean UI** — Streamlit frontend showing transcription, intent, action, and result

### Bonus Features Implemented
- ✅ **Compound Commands** — One audio input can trigger multiple tasks (e.g., "Write a Python file and summarize it")
- ✅ **Human-in-the-Loop** — Optional confirmation step before executing file operations
- ✅ **Graceful Degradation** — Falls back to `chat` intent on parse errors; handles unsupported audio formats
- ✅ **Session Memory** — Rolling chat context passed to the LLM; full action history in the sidebar
- ✅ **Model Benchmarking** — STT and intent latency displayed in the UI (toggle in settings)

---

## 🗂️ Project Structure

```
voice-agent/
├── app.py                  # Streamlit frontend
├── main.py                 # FastAPI backend
├── src/
│   ├── stt.py              # Speech-to-text (Groq Whisper)
│   ├── intent.py           # Intent classification (Groq Llama-3)
│   ├── tools.py            # Tool execution (file ops, code gen, summarize, chat)
│   ├── memory.py           # Session memory (chat context + action history)
│   ├── schemas.py          # Pydantic models (Task, ActionResult, AgentResponse)
│   └── logger.py           # Structured logging to logs/system.log
├── output/                 # ⚠️ All generated files go here (sandboxed)
│   └── .gitkeep
├── logs/
│   └── system.log
├── .env                    # API keys (not committed)
├── .env.example            # Template for required environment variables
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Setup & Installation

### Prerequisites

- Python 3.11+
- A [Groq API key](https://console.groq.com) (free tier available)

### 1. Clone the Repository

```bash
git clone https://github.com/IshanNaikele/voice-agent
cd voice-agent
```

### 2. Create a Virtual Environment

```bash
python -m venv my_env
# Windows
my_env\Scripts\activate
# macOS / Linux
source my_env/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and add your key:

```env
GROQ_API_KEY=your_groq_api_key_here
BACKEND_URL=http://localhost:8000
```

### 5. Run the Backend (FastAPI)

Open a terminal and run:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. You can explore the auto-generated docs at `http://localhost:8000/docs`.

### 6. Run the Frontend (Streamlit)

Open a **second terminal** (with the virtual environment activated) and run:

```bash
streamlit run app.py
```

The UI will open automatically at `http://localhost:8501`.

---

## 🧪 Example Usage

### Example 1 — Write Code
**Say:** *"Create a Python file called retry.py with an exponential backoff retry function."*

| Stage | Output |
|---|---|
| Transcription | "Create a Python file called retry.py with an exponential backoff retry function." |
| Intent | `write_code` (97% confidence) |
| Action | Generated Python code saved to `output/retry.py` |
| Result | File contents displayed in the UI |

### Example 2 — Compound Command (Bonus)
**Say:** *"Summarize this text: Machine learning is a subset of AI... and save it to summary.txt"*

| Stage | Output |
|---|---|
| Transcription | Full spoken text |
| Intents | `summarize` → then saves to `output/summary.txt` |
| Action | Two tasks executed in sequence |
| Result | Summary shown in UI + file created |

### Example 3 — General Chat
**Say:** *"What is the difference between a list and a tuple in Python?"*

| Stage | Output |
|---|---|
| Intent | `chat` |
| Action | LLM response generated |
| Result | Answer displayed in UI (no files created) |

---

## 🔒 Security

- All file operations are sandboxed to the `output/` directory
- Path traversal attacks are blocked via `_safe_path()` in `tools.py`
- Filenames are validated before any write operation
- The `output/` directory is pre-created at startup; no other directories are writable

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/transcribe` | Upload audio file → returns transcribed text |
| `POST` | `/classify` | Text → returns list of detected tasks |
| `POST` | `/execute` | Execute task list → returns results |
| `GET` | `/history` | Retrieve session action history |
| `DELETE` | `/history` | Clear session history |
| `GET` | `/health` | Health check |

Full interactive docs: `http://localhost:8000/docs`

---

## 📦 Dependencies

```
groq                      # Groq API client (Whisper STT + Llama LLM)
fastapi                   # Backend API framework
uvicorn                   # ASGI server for FastAPI
streamlit                 # Frontend UI framework
streamlit-audiorecorder   # Microphone recording component
python-dotenv             # .env file loading
pydantic                  # Data validation and schemas
python-multipart          # File upload support for FastAPI
httpx                     # Async HTTP client
```

---

## 🐛 Known Limitations

- Session memory resets if the FastAPI server is restarted (in-memory only, not persisted to disk)
- The `summarize` intent works best when the text to summarize is spoken directly in the audio; very long texts may be truncated by the STT model
- Microphone recording quality depends on the browser and OS audio permissions

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
