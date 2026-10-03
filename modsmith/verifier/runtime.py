"""Runtime verification: launch runClient and parse logs to verify mod loading and item registration."""

import os
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RuntimeResult:
    """Runtime verification result."""
    success: bool
    mod_loaded: bool
    item_registered: bool
    raw_log: str
    matched_lines: list[str] = field(default_factory=list)
    message: str = ""


def run_client_with_log(
    project_dir: Path,
    timeout: int = 180,
) -> RuntimeResult:
    """Launch ./gradlew runClient, capture logs, and determine whether the mod and item loaded successfully.

    Args:
        project_dir: The generated project directory.
        timeout: Maximum wait time (seconds).

    Returns:
        A RuntimeResult object.
    """
    project_dir = project_dir.resolve()
    if os.name == "nt":
        gradlew = project_dir / "gradlew.bat"
    else:
        gradlew = project_dir / "gradlew"

    if not gradlew.exists():
        return RuntimeResult(
            success=False,
            mod_loaded=False,
            item_registered=False,
            raw_log="",
            message=f"Could not find {gradlew}",
        )

    try:
        proc = subprocess.Popen(
    [str(gradlew), "runClient"],
    cwd=str(project_dir),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
    errors="replace",
)
    except Exception as e:
        return RuntimeResult(
            success=False,
            mod_loaded=False,
            item_registered=False,
            raw_log="",
            message=f"Launch failed: {e}",
        )

    log_lines: list[str] = []
    mod_loaded = False
    item_registered = False
    start = time.time()

    try:
        while True:
            if proc.poll() is not None:
                # Process has exited; read any remaining output
                if proc.stdout:
                    log_lines.extend(proc.stdout.readlines())
                break

            if time.time() - start > timeout:
                proc.terminate()
                break

            if proc.stdout:
                line = proc.stdout.readline()
                if not line:
                    time.sleep(0.2)
                    continue
                log_lines.append(line)

                # Check if the mod loaded successfully
                if "Loading" in line and "mods:" in line:
                    # The following lines will list the loaded mods
                    pass
                if "Hello Fabric world from" in line:
                    mod_loaded = True

                # Check if the item registered successfully (based on the log in ModItemsGenerated)
                if "Registered item" in line or "item.example-mod" in line:
                    item_registered = True

                # Early exit: both conditions met
                if mod_loaded and item_registered:
                    # Wait a few more seconds to collect remaining logs
                    time.sleep(2)
                    proc.terminate()
                    break
    except KeyboardInterrupt:
        proc.terminate()

    raw_log = "".join(log_lines)

    # Fallback: run a regex scan once more
    if not mod_loaded:
        mod_loaded = bool(re.search(r"Hello Fabric world from", raw_log))
    if not item_registered:
        item_registered = bool(re.search(r"item\.example-mod\.", raw_log))

    matched = [
        line.strip() for line in log_lines
        if "Hello Fabric world" in line or "item.example-mod" in line
    ]

    success = mod_loaded and item_registered
    if success:
        message = "✅ Mod loaded, item registered."
    elif mod_loaded:
        message = "⚠️ Mod loaded, but no item registration log detected."
    else:
        message = "❌ Mod failed to load. Please check the logs."

    return RuntimeResult(
        success=success,
        mod_loaded=mod_loaded,
        item_registered=item_registered,
        raw_log=raw_log,
        matched_lines=matched,
        message=message,
    )