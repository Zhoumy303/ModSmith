"""End-to-end pipeline: from natural language to a packaged mod."""

from pathlib import Path

from modsmith.blueprint.validator import generate_validated_blueprint
from modsmith.verifier.gradle import build_with_retry
from modsmith.packager.archive import package_output


def run_pipeline(
    user_input: str,
    project_dir: Path,
    output_dir: Path,
    max_retries: int = 3,
) -> dict | None:
    """Complete pipeline: generate blueprint → generate project → compile verification → package output.

    Args:
        user_input: User's natural language description.
        project_dir: Generated project directory.
        output_dir: Packaging output directory.
        max_retries: Maximum number of retries.

    Returns:
        Packaging result dictionary, or None on failure.
    """
    print(f"🧠 Parsing user description: {user_input}")
    blueprint = generate_validated_blueprint(user_input, max_retries=max_retries)
    print(f"✅ Blueprint generated: {blueprint['mod_id']}")

    print(f"\n🔨 Starting project generation and compilation...")
    success, final_blueprint = build_with_retry(blueprint, project_dir, max_retries)

    if not success:
        print("❌ Compilation failed, cannot continue packaging.")
        return None

    print(f"\n📦 Starting packaging...")
    results = package_output(final_blueprint, project_dir, output_dir)
    print(f"\n🎉 All done! Output directory: {output_dir}")
    return results