"""Test the runtime auto-verification module."""

from pathlib import Path

from modsmith.verifier.runtime import run_client_with_log

# Assume generated_project already exists and compiled successfully
project_dir = Path("./generated_project")

result = run_client_with_log(project_dir, timeout=180)
print(f"Success: {result.success}")
print(f"Mod loaded: {result.mod_loaded}")
print(f"Item registered: {result.item_registered}")
print(f"Message: {result.message}")
print("Matched log lines:")
for line in result.matched_lines:
    print(f"  {line}")