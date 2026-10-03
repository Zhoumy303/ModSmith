"""Test the packaging output module."""

from pathlib import Path

from modsmith.pipeline import run_pipeline

results = run_pipeline(
    user_input="Create an apple that restores 4 hunger points when eaten",
    project_dir=Path("./pipeline_project"),
    output_dir=Path("./pipeline_output"),
)

if results:
    print("\nPackaging results:")
    for key, path in results.items():
        print(f"  {key}: {path}")
else:
    print("Packaging failed.")