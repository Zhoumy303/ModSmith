"""Test the project generator."""

from pathlib import Path

from modsmith.blueprint.validator import generate_validated_blueprint
from modsmith.generator.project import generate_project

# Generate blueprint
blueprint = generate_validated_blueprint("Create an apple that restores 4 hunger points when eaten")

# Generate project
output_dir = Path("./generated_project")
generate_project(blueprint, output_dir)