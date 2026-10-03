"""Test the blueprint Schema and validation logic."""

import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from modsmith.blueprint.validator import validate_blueprint

SCHEMA_PATH = Path(__file__).parent.parent / "blueprint" / "schema.json"
EXAMPLES_DIR = Path(__file__).parent.parent / "blueprint" / "examples"


def test_schema_is_valid():
    """The Schema itself is a valid JSON Schema."""
    import jsonschema
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.Draft7Validator.check_schema(schema)


def test_all_examples_pass_validation():
    """All example blueprints pass Schema validation."""
    for example_path in EXAMPLES_DIR.glob("*.json"):
        with open(example_path, "r", encoding="utf-8") as f:
            blueprint = json.load(f)
        validate_blueprint(blueprint)


def test_missing_required_field_fails():
    """A blueprint missing a required field fails validation."""
    invalid_blueprint = {
        "mod_id": "test-mod",
        "package_name": "com.test",
        "minecraft_version": "26.1.2",
        "fabric_loader_version": "0.19.5",
        # Missing the items field
    }
    with pytest.raises(ValidationError):
        validate_blueprint(invalid_blueprint)


def test_food_missing_saturation_fails():
    """A food type missing saturation fails validation."""
    invalid = {
        "mod_id": "test-mod",
        "package_name": "com.test",
        "minecraft_version": "26.1.2",
        "fabric_loader_version": "0.19.5",
        "items": [
            {
                "id": "apple",
                "type": "food",
                "display_name_en": "Apple",
                "nutrition": 4,
                # Missing saturation and always_edible
            }
        ],
    }
    with pytest.raises(ValidationError):
        validate_blueprint(invalid)