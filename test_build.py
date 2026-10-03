"""Test the compile verification module."""

from pathlib import Path

from modsmith.blueprint.validator import generate_validated_blueprint
from modsmith.verifier.gradle import build_with_retry

# Generate the initial blueprint
blueprint = generate_validated_blueprint("Create an apple that restores 4 hunger points when eaten")

# Output directory
output_dir = Path("./build_test_project")

# Run compile verification
success, final_blueprint = build_with_retry(blueprint, output_dir)
if success:
    print("🎉 Compile verification succeeded!")
    print(f"Final blueprint: {final_blueprint}")
else:
    print("❌ Compile verification failed.")