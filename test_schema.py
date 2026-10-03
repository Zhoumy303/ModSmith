"""Validate that the Schema is legal and that examples conform to it."""

import json
from pathlib import Path

import jsonschema

# Path definitions
SCHEMA_PATH = Path("modsmith/blueprint/schema.json")
EXAMPLES_DIR = Path("modsmith/blueprint/examples")


def main() -> None:
    # 1. Load the Schema
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # 2. Validate the Schema itself
    try:
        jsonschema.Draft7Validator.check_schema(schema)
        print("✅ The Schema itself is a valid JSON Schema.")
    except jsonschema.SchemaError as e:
        print(f"❌ The Schema itself is invalid: {e}")
        return

    # 3. Validate each example against the Schema
    validator = jsonschema.Draft7Validator(schema)
    all_passed = True

    for example_path in sorted(EXAMPLES_DIR.glob("*.json")):
        with open(example_path, "r", encoding="utf-8") as f:
            example = json.load(f)

        errors = list(validator.iter_errors(example))
        if errors:
            all_passed = False
            print(f"❌ {example_path.name} does not conform to the Schema:")
            for error in errors:
                print(f"   - {error.message}")
        else:
            print(f"✅ {example_path.name} conforms to the Schema.")

    if all_passed:
        print("\n🎉 All examples passed validation!")
    else:
        print("\n⚠️ Some examples did not pass validation. Please check.")


if __name__ == "__main__":
    main()