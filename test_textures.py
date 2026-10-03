"""Test the texture generator."""

from pathlib import Path

from modsmith.generator.textures import generate_all_textures

blueprint = {
    "mod_id": "example-mod",
    "items": [
        {
            "id": "ruby",
            "type": "basic",
            "visual": {
                "shape": "crystal",
                "primary_color": "#dc2626",
                "accent_color": "#fca5a5",
                "pattern": "sparkle",
            },
        },
        {
            "id": "healing_apple",
            "type": "food",
            "visual": {
                "shape": "round",
                "primary_color": "#dc2626",
                "accent_color": "#86efac",
                "pattern": "sparkle",
            },
        },
        {
            "id": "guidite_sword",
            "type": "tool",
            "visual": {
                "shape": "blade",
                "primary_color": "#94a3b8",
                "accent_color": "#cbd5e1",
                "pattern": "none",
            },
        },
        {
            "id": "quark_gluon_plasma",
            "type": "basic",
            "visual": {
                "shape": "liquid",
                "primary_color": "#a855f7",
                "accent_color": "#c084fc",
                "pattern": "glow",
            },
        },
        {
            "id": "mystery_dust",
            "type": "basic",
            # Intentionally no visual, to test the fallback
        },
    ],
}

output_dir = Path("./test_textures_output")
generate_all_textures(blueprint, output_dir)
print(f"Textures generated at: {output_dir}")