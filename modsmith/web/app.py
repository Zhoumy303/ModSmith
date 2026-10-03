"""ModSmith Web UI: FastAPI-based backend service."""

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


class GenerateRequest(BaseModel):
    description: str
    mod_id: str = "example-mod"
    package_name: str = "com.example"


class RunClientRequest(BaseModel):
    task_id: str


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