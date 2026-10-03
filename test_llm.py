"""Test Zhipu GLM connection."""

import json
from modsmith.llm.client import generate_blueprint

result = generate_blueprint("Create an apple that restores 4 hunger points when eaten")
print(json.dumps(result, indent=2, ensure_ascii=False))