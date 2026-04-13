# app.py
import os
import requests
import streamlit as st
from dotenv import load_dotenv
from audiorecorder import audiorecorder
load_dotenv()

BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Voice Agent",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: #0a0a0f;
    color: #e8e6e1;
}
#MainMenu, footer, header { visibility: hidden; }

.stApp {
    background: #0a0a0f;
    background-image:
        radial-gradient(ellipse 80% 50% at 20% 10%, rgba(255,160,50,0.07) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 80%, rgba(255,80,50,0.05) 0%, transparent 60%);
}

.agent-title {
    font-size: 3.2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1;
    color: #f0ece4;
    margin-bottom: 0.2rem;
}
.agent-subtitle {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #ff9f2f;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    margin-bottom: 2rem;
}
.card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}
.card-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #ff9f2f;
    margin-bottom: 0.5rem;
}
.card-value { font-size: 1rem; color: #e8e6e1; line-height: 1.6; }
.card-mono {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    color: #a8e6cf;
    white-space: pre-wrap;
    line-height: 1.7;
}
.intent-badge {
    display: inline-block;
    background: rgba(255,159,47,0.12);
    border: 1px solid rgba(255,159,47,0.35);
    color: #ff9f2f;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    margin-right: 0.4rem;
    margin-bottom: 0.4rem;
    letter-spacing: 0.08em;
}
.confidence { color: #888; font-size: 0.65rem; margin-left: 0.3rem; }
.status-ok  { color: #a8e6cf; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; }
.status-err { color: #ff6b6b; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; }
.latency-row { display: flex; gap: 0.6rem; flex-wrap: wrap; margin-top: 0.4rem; }
.latency-pill {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 6px;
    padding: 0.18rem 0.6rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: #888;
}
.latency-pill span { color: #e8e6e1; }
.hist-item {
    border-left: 2px solid rgba(255,159,47,0.3);
    padding: 0.5rem 0.8rem;
    margin-bottom: 0.6rem;
    font-size: 0.82rem;
    color: #aaa;
}
.hist-time {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #555;
    margin-bottom: 0.15rem;
}
.divider { border: none; border-top: 1px solid rgba(255,255,255,0.06); margin: 1.2rem 0; }

.stButton > button {
    background: #ff9f2f !important;
    color: #0a0a0f !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.6rem !important;
}
section[data-testid="stSidebar"] {
    background: #0d0d14 !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "pending" not in st.session_state:
    st.session_state.pending = None
if "last_run" not in st.session_state:
    st.session_state.last_run = None
if "show_benchmark" not in st.session_state:
    st.session_state.show_benchmark = False

# ── Helpers ────────────────────────────────────────────────────────────────────
def api(method: str, path: str, **kwargs):
    try:
        r = requests.request(method, f"{BACKEND}{path}", timeout=60, **kwargs)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot reach backend. Run: `uvicorn main:app --reload`")
        st.stop()
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ API error: {e.response.text}")
        st.stop()


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown("### ⚙️ Settings")
    st.session_state.show_benchmark = st.toggle(
        "Show latency benchmarks", value=st.session_state.show_benchmark
    )
    human_loop = st.toggle("Human-in-the-loop confirm", value=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown("### 📋 Session History")

    hist_data = api("GET", "/history")
    history = hist_data.get("history", [])

    if not history:
        st.markdown(
            "<p style='color:#555;font-size:0.8rem;font-family:JetBrains Mono'>No actions yet.</p>",
            unsafe_allow_html=True
        )
    else:
        for entry in reversed(history[-10:]):
            intents_str = " · ".join(entry["intents"])
            transcript = entry["transcription"]
            st.markdown(f"""
            <div class="hist-item">
                <div class="hist-time">{entry['timestamp']}</div>
                <div>{transcript[:60]}{'…' if len(transcript) > 60 else ''}</div>
                <div style="color:#ff9f2f;font-size:0.7rem;margin-top:0.2rem">{intents_str}</div>
            </div>
            """, unsafe_allow_html=True)

    if history:
        if st.button("🗑 Clear history"):
            api("DELETE", "/history")
            st.session_state.pending = None
            st.session_state.last_run = None
            st.rerun()

# ── Main ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="agent-title">Voice Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="agent-subtitle">● FastAPI Backend · Groq-Powered · Intent Router</div>', unsafe_allow_html=True)

col_input, col_output = st.columns([1, 1], gap="large")

with col_input:
    st.markdown("#### 🎙️ Audio Input")

    input_mode = st.radio(
        "Source", ["Upload file", "Record microphone"],
        horizontal=True, label_visibility="collapsed"
    )

    audio_bytes = None
    audio_name  = None

    if input_mode == "Upload file":
        uploaded = st.file_uploader(
            "Drop a .wav or .mp3 file",
            type=["wav", "mp3", "m4a", "ogg"]
        )
        if uploaded:
            audio_bytes = uploaded.read()
            audio_name  = uploaded.name
            st.audio(audio_bytes, format="audio/wav")

    else:
        st.markdown(
            "<p style='color:#888;font-family:JetBrains Mono;font-size:0.75rem'>"
            "Press record, speak, then press stop.</p>",
            unsafe_allow_html=True
        )
        audio = audiorecorder("⏺ Record", "⏹ Stop")
        if len(audio) > 0:
            audio_bytes = audio.export().read()
            audio_name  = "recorded.wav"
            st.audio(audio_bytes, format="audio/wav")

    run_disabled = audio_bytes is None
    run_clicked  = st.button("▶ Run Agent", disabled=run_disabled, use_container_width=True)

    if run_clicked and audio_bytes:
        st.session_state.pending  = None
        st.session_state.last_run = None

        # Stage 1 — Transcribe
        with st.status("👂 Transcribing audio…", expanded=False) as s:
            t_resp = api(
                "POST", "/transcribe",
                files={"file": (audio_name, audio_bytes, "audio/wav")}
            )
            transcription  = t_resp["transcription"]
            stt_latency    = t_resp["stt_latency_ms"]
            s.update(label="👂 Transcription done", state="complete")

        # Stage 2 — Classify
        with st.status("🧠 Classifying intent…", expanded=False) as s:
            c_resp = api(
                "POST", "/classify",
                json={"transcription": transcription}
            )
            tasks          = c_resp["tasks"]
            intent_latency = c_resp["intent_latency_ms"]
            s.update(label="🧠 Intent detected", state="complete")

        latencies = {"stt": stt_latency, "intent": intent_latency}

        if human_loop:
            st.session_state.pending = (transcription, tasks, latencies)
        else:
            with st.status("🛠️ Executing tasks…", expanded=False) as s:
                e_resp = api(
                    "POST", "/execute",
                    json={"transcription": transcription, "tasks": tasks}
                )
                results = e_resp["results"]
                s.update(label="🛠️ Execution done", state="complete")

            st.session_state.last_run = {
                "transcription": transcription,
                "tasks": tasks,
                "results": results,
                "latencies": latencies
            }

        st.rerun()

# ── RIGHT — Output ─────────────────────────────────────────────────────────────
with col_output:
    st.markdown("#### 📊 System Output")

    # Human-in-the-loop
    if st.session_state.pending:
        transcription, tasks, latencies = st.session_state.pending

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-label">Transcription</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="card-value">{transcription}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-label">Proposed Actions</div>', unsafe_allow_html=True)
        for task in tasks:
            st.markdown(
                f'<span class="intent-badge">{task["intent"]}'
                f'<span class="confidence">{task["confidence"]:.0%}</span></span>',
                unsafe_allow_html=True
            )
            st.json(task["parameters"], expanded=False)
        st.markdown('</div>', unsafe_allow_html=True)

        st.warning("⚠️ Review proposed actions before executing.")
        c1, c2 = st.columns(2)

        with c1:
            if st.button("✅ Confirm & Execute", use_container_width=True):
                with st.status("🛠️ Executing…", expanded=False) as s:
                    e_resp = api(
                        "POST", "/execute",
                        json={"transcription": transcription, "tasks": tasks}
                    )
                    results = e_resp["results"]
                    s.update(label="🛠️ Done", state="complete")

                st.session_state.last_run = {
                    "transcription": transcription,
                    "tasks": tasks,
                    "results": results,
                    "latencies": latencies
                }
                st.session_state.pending = None
                st.rerun()

        with c2:
            if st.button("✗ Cancel", use_container_width=True):
                st.session_state.pending = None
                st.rerun()

    # Results
    elif st.session_state.last_run:
        run          = st.session_state.last_run
        transcription = run["transcription"]
        tasks        = run["tasks"]
        results      = run["results"]
        latencies    = run["latencies"]

        # Transcription card
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-label">Transcription</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="card-value">{transcription}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Intents card
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-label">Detected Intent(s)</div>', unsafe_allow_html=True)
        for task in tasks:
            st.markdown(
                f'<span class="intent-badge">{task["intent"]}'
                f'<span class="confidence">{task["confidence"]:.0%}</span></span>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

        # Per-task result cards
        for i, (task, result) in enumerate(zip(tasks, results)):
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(
                f'<div class="card-label">Action {i+1} — {task["intent"]}</div>',
                unsafe_allow_html=True
            )
            ok  = result["success"]
            cls = "status-ok" if ok else "status-err"
            ico = "✓" if ok else "✗"
            st.markdown(
                f'<div class="{cls}">{ico} {result["message"]}</div>',
                unsafe_allow_html=True
            )
            if result.get("output"):
                output = result["output"]
                st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
                st.markdown(
                    f'<div class="card-mono">{output[:1200]}'
                    f'{"…" if len(output) > 1200 else ""}</div>',
                    unsafe_allow_html=True
                )
            st.markdown('</div>', unsafe_allow_html=True)

        # Benchmark
        if st.session_state.show_benchmark:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="card-label">Model Benchmarks</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="latency-row">'
                f'<div class="latency-pill">STT · Whisper <span>{latencies["stt"]:.0f} ms</span></div>'
                f'<div class="latency-pill">Intent · Llama-3-70B <span>{latencies["intent"]:.0f} ms</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="card" style="text-align:center;padding:3rem 1.6rem;">
            <div style="font-size:2.5rem;margin-bottom:0.8rem">🎙️</div>
            <div style="color:#555;font-family:'JetBrains Mono',monospace;font-size:0.8rem;letter-spacing:0.1em">
                UPLOAD AUDIO · PRESS RUN
            </div>
        </div>
        """, unsafe_allow_html=True)