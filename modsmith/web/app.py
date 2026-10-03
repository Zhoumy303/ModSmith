"""ModSmith Web UI: FastAPI-based backend service."""
import asyncio
import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
import os
import subprocess
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

app = FastAPI(title="ModSmith Web UI")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# In-memory task storage: task_id -> state
TASKS: dict[str, dict] = {}
# In-memory Chat session storage: session_id -> [{role, content}]
CHAT_SESSIONS: dict[str, list[dict]] = {}

class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatClearRequest(BaseModel):
    session_id: str


class ChatSummarizeRequest(BaseModel):
    session_id: str

class GenerateRequest(BaseModel):
    description: str
    mod_id: str = "example-mod"
    package_name: str = "com.example"


class RunClientRequest(BaseModel):
    task_id: str

# ============================================================
# Chat mode
# ============================================================

@app.post("/api/chat")
async def chat(req: ChatRequest) -> dict:
    """Append the user message to the session history and return success."""
    if req.session_id not in CHAT_SESSIONS:
        CHAT_SESSIONS[req.session_id] = []
    CHAT_SESSIONS[req.session_id].append({"role": "user", "content": req.message})
    return {"success": True, "session_id": req.session_id}


@app.get("/api/chat/stream/{session_id}")
async def chat_stream(session_id: str):
    """Stream the Chat reply via SSE."""
    if session_id not in CHAT_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator() -> AsyncGenerator[dict, None]:
        from modsmith.llm.chat import chat_response

        history = CHAT_SESSIONS[session_id]
        if not history or history[-1]["role"] != "user":
            yield {"event": "error", "data": json.dumps({"message": "No pending message to answer"})}
            return

        user_message = history[-1]["content"]
        prior = history[:-1]

        loop = asyncio.get_event_loop()

        def run_chat() -> str:
            return chat_response(user_message, history=prior)

        try:
            answer = await loop.run_in_executor(None, run_chat)
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"message": str(e)})}
            return

        history.append({"role": "assistant", "content": answer})

        # Stream character by character (typewriter effect)
        for ch in answer:
            yield {"event": "chunk", "data": json.dumps({"text": ch})}
            await asyncio.sleep(0.008)

        yield {"event": "done", "data": json.dumps({"answer": answer})}

    return EventSourceResponse(event_generator())


@app.post("/api/chat/clear")
async def chat_clear(req: ChatClearRequest) -> dict:
    """Clear the history of a session."""
    CHAT_SESSIONS.pop(req.session_id, None)
    return {"success": True}


@app.post("/api/chat/summarize")
async def chat_summarize(req: ChatSummarizeRequest) -> dict:
    """Compress the conversation history into a requirement description for the Execute description box.

    First tries to extract the 【Requirement Summary】 marker from the last assistant message;
    if not found, calls the LLM once to generate a summary based on the history.
    """
    if req.session_id not in CHAT_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")

    history = CHAT_SESSIONS[req.session_id]
    if not history:
        raise HTTPException(status_code=400, detail="Conversation is empty")

    # 1. Prefer to extract the 【Requirement Summary】 marker
    for msg in reversed(history):
        if msg["role"] == "assistant" and "【Requirement Summary】" in msg["content"]:
            text = msg["content"]
            start = text.find("【Requirement Summary】") + len("【Requirement Summary】")
            end = len(text)
            for marker in ["Confirm", "Click", "Run", "\n\n"]:
                idx = text.find(marker, start)
                if idx != -1 and idx < end:
                    end = idx
            summary = text[start:end].strip()
            if summary:
                return {"summary": summary}

    # 2. Fallback: call the LLM to generate a summary
    from modsmith.llm.client import get_client, DEFAULT_MODEL

    def _run() -> str:
        client = get_client()
        dialogue = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in history
        )
        prompt = f"""Please read the following conversation and summarize the mod the user wants in one sentence.
Output only that sentence, without any explanation, JSON, or Markdown.

Requirements:
- Only describe what ModSmith can generate: basic items, food, tools
- Include: type, name, effect (if any)
- If there is no clear requirement in the conversation, output "unclear"

Conversation:
{dialogue}
"""
        message = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()

    try:
        summary = await asyncio.get_event_loop().run_in_executor(None, _run)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {e}")

    return {"summary": summary}

@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """Return the home page HTML."""
    index_path = STATIC_DIR / "index.html"
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.post("/api/generate")
async def generate(req: GenerateRequest) -> dict:
    """Create a generation task and return task_id."""
    task_id = str(uuid.uuid4())
    TASKS[task_id] = {
        "status": "pending",
        "logs": [],
        "result": None,
        "description": req.description,
        "mod_id": req.mod_id,
        "package_name": req.package_name,
        "project_dir": None,
        "blueprint_content": "",
        "readme_content": "",
    }
    return {"task_id": task_id}


@app.get("/api/stream/{task_id}")
async def stream(task_id: str):
    """Push task progress via SSE."""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_generator():
        task = TASKS[task_id]
        loop = asyncio.get_event_loop()

        def run_task():
            # Use absolute paths to avoid path failures caused by working directory changes
            project_dir = Path(f"./web_output/{task_id}/project").resolve()
            output_dir = Path(f"./web_output/{task_id}/output").resolve()
            task["project_dir"] = str(project_dir)

            def log(msg: str):
                task["logs"].append(msg)

            try:
                log(f"🧠 Parsing description: {task['description']}")
                from modsmith.blueprint.validator import generate_validated_blueprint
                from modsmith.verifier.gradle import build_with_retry
                from modsmith.packager.archive import package_output

                blueprint = generate_validated_blueprint(task["description"])
                blueprint["mod_id"] = task["mod_id"]
                blueprint["package_name"] = task["package_name"]
                log(f"✅ Blueprint generated: {blueprint['mod_id']}")

                log("🔨 Starting project generation and compilation...")
                success, final_blueprint = build_with_retry(blueprint, project_dir)
                if not success:
                    log("❌ Compilation failed")
                    task["status"] = "failed"
                    return

                log("📦 Starting packaging...")
                results = package_output(final_blueprint, project_dir, output_dir)
                task["result"] = {k: str(v) for k, v in results.items()}

                # Read blueprint and README content for frontend display
                blueprint_path = results.get("blueprint")
                if blueprint_path and Path(blueprint_path).exists():
                    task["blueprint_content"] = Path(blueprint_path).read_text(encoding="utf-8")

                readme_path = results.get("readme")
                if readme_path and Path(readme_path).exists():
                    task["readme_content"] = Path(readme_path).read_text(encoding="utf-8")

                task["status"] = "success"
                log("🎉 All done!")
            except Exception as e:
                task["status"] = "failed"
                log(f"❌ Error: {e}")

        future = loop.run_in_executor(None, run_task)

        sent_index = 0
        while True:
            logs = task["logs"]
            while sent_index < len(logs):
                yield {"event": "log", "data": json.dumps({"message": logs[sent_index]})}
                sent_index += 1

            if task["status"] == "success":
                yield {"event": "done", "data": json.dumps({
                    "result": task["result"],
                    "project_dir": task["project_dir"],
                    "blueprint_content": task.get("blueprint_content", ""),
                    "readme_content": task.get("readme_content", ""),
                })}
                break
            elif task["status"] == "failed":
                yield {"event": "error", "data": json.dumps({"message": "Task failed"})}
                break

            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


@app.get("/api/download/{task_id}/{filename}")
async def download(task_id: str, filename: str):
    """Download a generated file."""
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    file_path = Path(f"./web_output/{task_id}/output/{filename}").resolve()
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)


@app.post("/api/run_client")
async def run_client(req: RunClientRequest) -> dict:
    """Launch the Minecraft client in the background for verification."""
    if req.task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    task = TASKS[req.task_id]
    project_dir = task.get("project_dir")
    if not project_dir:
        raise HTTPException(status_code=400, detail="Project directory does not exist. Please generate a mod first.")

    project_path = Path(project_dir).resolve()
    if not project_path.exists():
        raise HTTPException(status_code=400, detail=f"Project directory does not exist: {project_path}")

    # Choose gradlew command based on OS
    if os.name == "nt":
        gradlew = project_path / "gradlew.bat"
    else:
        gradlew = project_path / "gradlew"

    if not gradlew.exists():
        raise HTTPException(status_code=400, detail=f"gradlew not found: {gradlew}")

    try:
        subprocess.Popen(
            [str(gradlew), "runClient"],
            cwd=str(project_path),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to launch: {e}")

    return {"success": True, "message": "Game is launching, please wait..."}

    from modsmith.verifier.runtime import run_client_with_log


class AutoVerifyRequest(BaseModel):
    task_id: str


@app.post("/api/auto_verify")
async def auto_verify(req: AutoVerifyRequest) -> dict:
    """Launch the game and automatically verify mod loading and item registration."""
    if req.task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    task = TASKS[req.task_id]
    project_dir = task.get("project_dir")
    if not project_dir:
        raise HTTPException(status_code=400, detail="Project directory does not exist")

    project_path = Path(project_dir).resolve()
    if not project_path.exists():
        raise HTTPException(status_code=400, detail=f"Project directory does not exist: {project_path}")

    # Run synchronously (long-running; acceptable during MVP)
    result = run_client_with_log(project_path, timeout=180)
    return {
        "success": result.success,
        "mod_loaded": result.mod_loaded,
        "item_registered": result.item_registered,
        "message": result.message,
        "matched_lines": result.matched_lines,
    }

    