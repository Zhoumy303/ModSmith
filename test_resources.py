"""Test resource file generation."""

from pathlib import Path

from modsmith.generator.resources import generate_resources

# Manually construct a blueprint containing multiple types
blueprint = {
    "mod_id": "example-mod",
    "package_name": "com.example",
    "minecraft_version": "26.1.2",
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
            "effects": [],
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

# Generate to a temporary directory
output_dir = Path("./test_resources_output")
generate_resources(blueprint, output_dir)
print(f"Resource files generated at: {output_dir}")