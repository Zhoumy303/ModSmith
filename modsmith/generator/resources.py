"""Generate item-related resource files (models, translations, client item definitions)."""

import json
from pathlib import Path


def generate_resources(blueprint: dict, project_dir: Path) -> None:
    """Generate resource files for the items in the blueprint.

    Args:
        blueprint: Blueprint dictionary.
        project_dir: Root directory of the generated project.
    """
    mod_id = blueprint["mod_id"]
    assets_dir = project_dir / "src" / "main" / "resources" / "assets" / mod_id

    # Create necessary directories
    (assets_dir / "items").mkdir(parents=True, exist_ok=True)
    (assets_dir / "models" / "item").mkdir(parents=True, exist_ok=True)
    (assets_dir / "textures" / "item").mkdir(parents=True, exist_ok=True)
    (assets_dir / "lang").mkdir(parents=True, exist_ok=True)

    # Collect translation key-value pairs
    en_us = {}
    zh_cn = {}

    for item in blueprint["items"]:
        item_id = item["id"]

        # 1. Client item definition
        client_item = {
            "model": {
                "type": "minecraft:model",
                "model": f"{mod_id}:item/{item_id}"
            }
        }
        (assets_dir / "items" / f"{item_id}.json").write_text(
            json.dumps(client_item, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # 2. Model file: choose parent based on type
        if item["type"] == "tool":
            parent = "minecraft:item/handheld"
        else:
            parent = "minecraft:item/generated"

        model = {
            "parent": parent,
            "textures": {
                "layer0": f"{mod_id}:item/{item_id}"
            }
        }
        (assets_dir / "models" / "item" / f"{item_id}.json").write_text(
            json.dumps(model, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # 3. Translation
        translation_key = f"item.{mod_id}.{item_id}"
        en_us[translation_key] = item.get("display_name_en", item_id)
        if "display_name_zh" in item:
            zh_cn[translation_key] = item["display_name_zh"]

    # Write English translations
    (assets_dir / "lang" / "en_us.json").write_text(
        json.dumps(en_us, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Write Chinese translations (only when Chinese translations exist)
    if zh_cn:
        (assets_dir / "lang" / "zh_cn.json").write_text(
            json.dumps(zh_cn, indent=2, ensure_ascii=False), encoding="utf-8"
        )