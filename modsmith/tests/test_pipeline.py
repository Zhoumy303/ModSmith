"""Test the end-to-end pipeline (mock LLM)."""

from pathlib import Path
from unittest.mock import patch

from modsmith.pipeline import run_pipeline

SAMPLE_BLUEPRINT = {
    "mod_id": "mock-mod",
    "package_name": "com.mock",
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


@patch("modsmith.pipeline.generate_validated_blueprint")
@patch("modsmith.pipeline.build_with_retry")
def test_pipeline_end_to_end(mock_build, mock_generate, tmp_path: Path):
    """Test the pipeline's behavior under mocks."""
    mock_generate.return_value = SAMPLE_BLUEPRINT
    mock_build.return_value = (True, SAMPLE_BLUEPRINT)

    results = run_pipeline(
        user_input="test",
        project_dir=tmp_path / "project",
        output_dir=tmp_path / "output",
    )

    assert results is not None
    assert "source_zip" in results
    assert "blueprint" in results