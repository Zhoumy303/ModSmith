"""Compile verification module: run Gradle build and feed failures back to the LLM to correct the blueprint."""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from modsmith.generator.project import generate_project
from modsmith.llm.client import generate_blueprint
from modsmith.blueprint.validator import validate_blueprint


@dataclass
class BuildResult:
    """Gradle build result."""
    success: bool
    stdout: str
    stderr: str
    returncode: int


def run_gradle_build(project_dir: Path) -> BuildResult:
    """Run ./gradlew build in the specified project directory."""
    # Key: convert to absolute path to avoid cwd and path concatenation conflicts
    project_dir = project_dir.resolve()

    gradlew = project_dir / ("gradlew.bat" if os.name == "nt" else "gradlew")

    if not gradlew.exists():
        return BuildResult(
            success=False,
            stdout="",
            stderr=f"Could not find {gradlew}",
            returncode=-1,
        )

    try:
        result = subprocess.run(
            [str(gradlew), "build"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=300,
        )
        return BuildResult(
            success=(result.returncode == 0),
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
        )
    except subprocess.TimeoutExpired as e:
        return BuildResult(
            success=False,
            stdout=e.stdout or "",
            stderr=f"Build timed out: {e}",
            returncode=-1,
        )
    except Exception as e:
        return BuildResult(
            success=False,
            stdout="",
            stderr=f"Exception while running gradlew: {e}",
            returncode=-1,
        )


def _extract_errors(build_result: BuildResult) -> str:
    """Extract key error messages from the build result for feedback to the LLM."""
    lines = []
    # Extract error lines from stderr
    for line in build_result.stderr.splitlines():
        if "错误:" in line or "error:" in line.lower():
            lines.append(line)
    # If not found in stderr, try stdout
    if not lines:
        for line in build_result.stdout.splitlines():
            if "错误:" in line or "error:" in line.lower():
                lines.append(line)
    if not lines:
        # Fallback: return the last 20 lines
        all_lines = (build_result.stderr + "\n" + build_result.stdout).splitlines()
        lines = all_lines[-20:]
    return "\n".join(lines)


def build_with_retry(
    blueprint: dict,
    output_dir: Path,
    max_retries: int = 3,
) -> tuple[bool, dict]:
    """Generate the project and compile it; on failure, feed back to the LLM to correct the blueprint and retry.

    Args:
        blueprint: Initial blueprint dictionary.
        output_dir: Output project directory.
        max_retries: Maximum number of retries.

    Returns:
        (success, final blueprint dictionary)
    """
    current_blueprint = blueprint

    for attempt in range(1, max_retries + 1):
        print(f"\n🔄 Attempt {attempt}: generating and compiling...")

        # 1. Generate project
        generate_project(current_blueprint, output_dir)

        # 2. Compile
        result = run_gradle_build(output_dir)

        if result.success:
            print(f"✅ Attempt {attempt}: compilation succeeded!")
            return True, current_blueprint

        # 3. Compilation failed; extract error information
        error_summary = _extract_errors(result)
        print(f"⚠️ Attempt {attempt}: compilation failed:\n{error_summary}")

        # 4. Feed back to the LLM to correct the blueprint
        correction_prompt = f"""The previously generated blueprint caused compilation to fail. The error information is as follows:

{error_summary}

Please correct the blueprint according to the above errors. Note:
- If the error is related to Java code, check whether the item type and related fields are complete.
- If the error is related to model or texture paths, check whether the item ID naming conforms to the conventions.
- Output only the corrected full blueprint JSON, without any explanation.
"""
        try:
            current_blueprint = generate_blueprint(correction_prompt)
            validate_blueprint(current_blueprint)
        except Exception as e:
            print(f"⚠️ Error while correcting blueprint: {e}")
            # Continue to the next loop, but it may still fail

    print(f"❌ After {max_retries} attempts, compilation still failed.")
    return False, current_blueprint