"""Generate Java code related to item registration."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "java"


def generate_java_items(blueprint: dict, project_dir: Path) -> None:
    """Generate Java code for the items in the blueprint.

    Args:
        blueprint: Blueprint dictionary.
        project_dir: Root directory of the generated project.
    """
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        keep_trailing_newline=True,
    )

    context = {
        "package_name": blueprint["package_name"],
        "items": blueprint["items"],
        "mod_id": blueprint["mod_id"],
    }

    package_path = blueprint["package_name"].replace(".", "/")
    java_dir = project_dir / "src" / "main" / "java" / package_path
    java_dir.mkdir(parents=True, exist_ok=True)

    files_to_generate = {
        "ModItemIds.java.jinja": "ModItemIds.java",
        "ModItems.java.jinja": "ModItems.java",
        "ModItemsGenerated.java.jinja": "ModItemsGenerated.java",
    }

    for template_name, output_name in files_to_generate.items():
        template = env.get_template(template_name)
        content = template.render(**context)
        (java_dir / output_name).write_text(content, encoding="utf-8")