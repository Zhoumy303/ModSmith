"""LLM client for generating blueprints from natural language."""
from modsmith.config import MINECRAFT_VERSION, FABRIC_LOADER_VERSION

import os
import json
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Anthropic-compatible endpoint for Zhipu GLM
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/anthropic"

# Default model (can be overridden in .env)
DEFAULT_MODEL = os.environ.get("GLM_MODEL", "glm-5.3")

# Blueprint schema paths
SCHEMA_PATH = Path(__file__).parent.parent / "blueprint" / "schema.json"
EXAMPLES_DIR = Path(__file__).parent.parent / "blueprint" / "examples"


def _load_schema() -> dict:
    """Load the blueprint JSON Schema."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_examples() -> list[dict]:
    """Load few-shot example blueprints."""
    from modsmith.config import default_context
    defaults = default_context()

    examples = []
    if EXAMPLES_DIR.exists():
        for path in sorted(EXAMPLES_DIR.glob("*.json")):
            with open(path, "r", encoding="utf-8") as f:
                example = json.load(f)
            # Override version fields in examples with configured versions
            example["minecraft_version"] = defaults["minecraft_version"]
            example["fabric_loader_version"] = defaults["fabric_loader_version"]
            examples.append(example)
    return examples


def _build_system_prompt() -> str:
    """Build the system prompt, including the Schema and few-shot examples."""
    schema = _load_schema()
    examples = _load_examples()

    prompt = f"""You are a Minecraft Fabric mod blueprint generator.

Your task is to generate a blueprint that conforms to the following JSON Schema based on the user's natural-language description.

## Schema

```json
{json.dumps(schema, indent=2, ensure_ascii=False)}
```

## Examples

"""

    for i, example in enumerate(examples, 1):
        prompt += f"### Example {i}\n\n```json\n{json.dumps(example, indent=2, ensure_ascii=False)}\n```\n\n"

    prompt += """## Rules

1. Output JSON only. Do not include any explanation, comments, or Markdown code block markers.
2. All required fields must be present.
3. The `type` field can only be one of: basic, food, fuel, tool.
4. If the description is unclear, use reasonable defaults.
5. If the `texture` field cannot be determined, use "auto".

## Required fields per type

- **basic**: `id`, `type`, `display_name_en`
- **food**: `id`, `type`, `display_name_en`, `nutrition`, `saturation`, `always_edible`
- **fuel**: `id`, `type`, `display_name_en`, `burn_time`
- **tool**: `id`, `type`, `display_name_en`, `tool_type`, `durability`, `mining_speed`, `attack_damage`

## Suggested defaults

- `saturation`: 0.3
- `always_edible`: true
- `effects`: empty array `[]`
- `texture`: "auto"

## Version requirements (must be strictly followed)

- `minecraft_version` must be "{MINECRAFT_VERSION}"
- `fabric_loader_version` must be "{FABRIC_LOADER_VERSION}"
- Do not use any other version numbers.
"""

    return prompt


def get_client() -> anthropic.Anthropic:
    """Create and return an Anthropic client for Zhipu GLM."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is not set. Please configure your Zhipu API Key in the .env file."
        )

    return anthropic.Anthropic(
        api_key=api_key,
        base_url=ZHIPU_BASE_URL,
    )


def generate_blueprint(user_input: str) -> dict:
    """Convert a natural-language description into structured blueprint JSON.

    Args:
        user_input: The user's natural-language description of the mod.

    Returns:
        A blueprint dictionary that conforms to the Schema.

    Raises:
        ValueError: When the API key is not configured.
        json.JSONDecodeError: When the content returned by the LLM is not valid JSON.
    """
    client = get_client()
    system_prompt = _build_system_prompt()

    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_input},
        ],
    )

    # Extract text content
    response_text = message.content[0].text.strip()

    # Remove possible Markdown code fence markers
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    # Parse JSON
    blueprint = json.loads(response_text)
    return blueprint