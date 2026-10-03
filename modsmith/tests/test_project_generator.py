"""Test the project generator."""

from pathlib import Path

from modsmith.generator.project import generate_project

SAMPLE_BLUEPRINT = {
    "mod_id": "test-mod",
    "package_name": "com.testmod",
    "minecraft_version": "26.1.2",
    "fabric_loader_version": "0.19.5",
    "items": [
        {
            "id": "ruby",
            "type": "basic",
            "display_name_en": "Ruby",
            "display_name_zh": "红宝石",
            "texture": "auto",
        }
    ],
}


def test_generate_project_creates_files(tmp_path: Path):
    """Generating a project should create the key files."""
    output_dir = tmp_path / "test_project"
    generate_project(SAMPLE_BLUEPRINT, output_dir)

    # Core files exist
    assert (output_dir / "build.gradle").exists()
    assert (output_dir / "gradle.properties").exists()
    assert (output_dir / "gradlew").exists()
    assert (output_dir / "src/main/resources/fabric.mod.json").exists()

    # Java files
    java_dir = output_dir / "src/main/java/com/testmod"
    assert (java_dir / "ModItemIds.java").exists()
    assert (java_dir / "ModItems.java").exists()
    assert (java_dir / "ModItemsGenerated.java").exists()

    # Resource files
    assets_dir = output_dir / "src/main/resources/assets/test-mod"
    assert (assets_dir / "items/ruby.json").exists()
    assert (assets_dir / "models/item/ruby.json").exists()
    assert (assets_dir / "lang/en_us.json").exists()
    assert (assets_dir / "textures/item/ruby.png").exists()