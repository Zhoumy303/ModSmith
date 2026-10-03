"""Test the project generator, including full Java code generation."""

from pathlib import Path

from modsmith.blueprint.validator import generate_validated_blueprint
from modsmith.generator.project import generate_project

# Use a blueprint containing multiple types for testing
blueprint = {
    "mod_id": "example-mod",
    "package_name": "com.example",
    "minecraft_version": "26.2",
    "fabric_loader_version": "0.19.5",
    "items": [
        {
            "id": "ruby",
            "type": "basic",
            "display_name_en": "Ruby",
            "display_name_zh": "红宝石",
            "texture": "auto"
        },
        {
            "id": "healing_apple",
            "type": "food",
            "display_name_en": "Healing Apple",
            "display_name_zh": "治愈苹果",
            "nutrition": 4,
            "saturation": 0.3,
            "always_edible": True,
            "effects": [
                {"effect": "regeneration", "duration_ticks": 200, "amplifier": 0}
            ],
            "texture": "auto"
        },
        {
            "id": "quark_gluon_plasma",
            "type": "fuel",
            "display_name_en": "Quark-Gluon Plasma",
            "display_name_zh": "夸克-胶子等离子体",
            "burn_time": 2400,
            "texture": "auto"
        },
        {
            "id": "guidite_sword",
            "type": "tool",
            "display_name_en": "Guidite Sword",
            "display_name_zh": "基迪特剑",
            "tool_type": "sword",
            "durability": 455,
            "mining_speed": 5.0,
            "attack_damage": 1.5,
            "texture": "auto"
        }
    ]
}

output_dir = Path("./generated_project")
generate_project(blueprint, output_dir)