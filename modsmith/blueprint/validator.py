"""Blueprint validation and LLM-driven correction."""

import json
from pathlib import Path

import jsonschema

from modsmith.llm.client import generate_blueprint

SCHEMA_PATH = Path(__file__).parent / "schema.json"


def _load_schema() -> dict:
    """Load the blueprint JSON Schema."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_blueprint(blueprint: dict) -> None:
    """Validate the blueprint against the Schema; raise jsonschema.ValidationError on failure."""
    schema = _load_schema()
    jsonschema.validate(instance=blueprint, schema=schema)


def generate_validated_blueprint(user_input: str, max_retries: int = 3) -> dict:
    """Generate a blueprint and validate it; on failure, feed back to the LLM for correction,
    retrying at most max_retries times.

    Args:
        user_input: The user's natural language description.
        max_retries: Maximum number of retries.

    Returns:
        A validated blueprint dictionary.

    Raises:
        RuntimeError: If a valid blueprint still cannot be generated after max_retries attempts.
    """
    last_error = None
    current_input = user_input

    for attempt in range(1, max_retries + 1):
        try:
            blueprint = generate_blueprint(current_input)
            validate_blueprint(blueprint)
            print(f"✅ Attempt {attempt} successfully generated a valid blueprint.")
            return blueprint
        except jsonschema.ValidationError as e:
            last_error = e
            path = " -> ".join(str(p) for p in e.path) if e.path else "root"
            feedback = f"""The previously generated blueprint is invalid. The error information is as follows:

- Error location: {path}
- Error type: {e.message}

Please correct it strictly according to the following requirements:
1. If `type` is `food`, it must contain `nutrition` (integer), `saturation` (float, e.g. 0.3), `always_edible` (boolean, e.g. true).
2. If `type` is `fuel`, it must contain `burn_time` (integer).
3. If `type` is `tool`, it must contain `tool_type`, `durability`, `mining_speed`, `attack_damage`.
4. If a field is missing, fill in a reasonable default value. For example, `saturation` defaults to 0.3, `always_edible` defaults to true.

Please regenerate a valid blueprint. Output JSON only."""
            print(f"⚠️ Attempt {attempt} failed: {e.message}")
            current_input = f"{user_input}\n\n{feedback}"
        except json.JSONDecodeError as e:
            last_error = e
            feedback = f"The previously returned content is not valid JSON. Error: {e}. Please output JSON only, without any explanation."
            print(f"⚠️ Attempt {attempt} failed: {feedback}")
            current_input = f"{user_input}\n\n{feedback}"

    raise RuntimeError(f"After {max_retries} attempts, a valid blueprint still could not be generated. Last error: {last_error}")