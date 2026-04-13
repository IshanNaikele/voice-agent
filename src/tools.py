import os
import time
from groq import Groq
from src.schemas import Task, ActionResult
from src.logger import log_event

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

OUTPUT_DIR = os.path.abspath("output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def _safe_path(filename: str) -> str | None:
    """Ensure file path stays inside output/ directory."""
    target = os.path.abspath(os.path.join(OUTPUT_DIR, filename))
    if not target.startswith(OUTPUT_DIR):
        return None
    return target


def create_file(params: dict) -> ActionResult:
    filename = params.get("filename", "untitled.txt")
    content = params.get("content", "")
    path = _safe_path(filename)

    if not path:
        return ActionResult(intent="create_file", success=False,
                            message="Security error: path traversal detected.")
    try:
        with open(path, "w") as f:
            f.write(content)
        log_event("TOOL", f"Created file: {path}")
        return ActionResult(intent="create_file", success=True,
                            message=f"File created at output/{filename}",
                            output=content)
    except Exception as e:
        return ActionResult(intent="create_file", success=False, message=str(e))


def write_code(params: dict) -> ActionResult:
    filename = params.get("filename", "script.py")
    language = params.get("language", "python")
    description = params.get("description", "")
    path = _safe_path(filename)

    if not path:
        return ActionResult(intent="write_code", success=False,
                            message="Security error: path traversal detected.")
    try:
        prompt = f"Write {language} code for: {description}. Return only the raw code, no markdown."
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1500
        )
        code = response.choices[0].message.content.strip()

        with open(path, "w") as f:
            f.write(code)

        log_event("TOOL", f"Code written to: {path}")
        return ActionResult(intent="write_code", success=True,
                            message=f"Code saved to output/{filename}",
                            output=code)
    except Exception as e:
        return ActionResult(intent="write_code", success=False, message=str(e))


def summarize(params: dict) -> ActionResult:
    text = params.get("text", "")
    save_to = params.get("save_to", None)

    if not text:
        return ActionResult(intent="summarize", success=False,
                            message="No text provided to summarize.")
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "user",
                "content": f"Summarize the following text concisely:\n\n{text}"
            }],
            temperature=0.3,
            max_tokens=500
        )
        summary = response.choices[0].message.content.strip()

        if save_to:
            path = _safe_path(save_to)
            if path:
                with open(path, "w") as f:
                    f.write(summary)
                log_event("TOOL", f"Summary saved to: {path}")
                return ActionResult(intent="summarize", success=True,
                                    message=f"Summary saved to output/{save_to}",
                                    output=summary)

        return ActionResult(intent="summarize", success=True,
                            message="Summarization complete.", output=summary)
    except Exception as e:
        return ActionResult(intent="summarize", success=False, message=str(e))


def chat(params: dict) -> ActionResult:
    message = params.get("message", "")
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": message}],
            temperature=0.7,
            max_tokens=800
        )
        reply = response.choices[0].message.content.strip()
        log_event("TOOL", "Chat response generated.")
        return ActionResult(intent="chat", success=True,
                            message="Chat response ready.", output=reply)
    except Exception as e:
        return ActionResult(intent="chat", success=False, message=str(e))


def execute_task(task: Task) -> ActionResult:
    handlers = {
        "create_file": create_file,
        "write_code": write_code,
        "summarize": summarize,
        "chat": chat
    }
    handler = handlers.get(task.intent)
    if not handler:
        log_event("TOOL", f"Unknown intent: {task.intent}")
        return ActionResult(
            intent=task.intent,
            success=False,
            message=f"Sorry, I don't know how to handle '{task.intent}' yet."
        )
    return handler(task.parameters)