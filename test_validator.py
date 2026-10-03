"""Test the blueprint validation module."""

import json
from modsmith.blueprint.validator import generate_validated_blueprint

result = generate_validated_blueprint("Create an apple that restores 4 hunger points when eaten")
print(json.dumps(result, indent=2, ensure_ascii=False))