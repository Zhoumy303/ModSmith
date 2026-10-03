"""生成物品注册相关的 Java 代码。"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "java"


def generate_java_items(blueprint: dict, project_dir: Path) -> None:
    """为蓝图中的物品生成 Java 代码。

    Args:
        blueprint: 蓝图字典。
        project_dir: 生成的项目根目录。
    """
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        keep_trailing_newline=True,
    )

    # 准备统一的渲染上下文（所有模板共用）
    context = {
        "package_name": blueprint["package_name"],
        "items": blueprint["items"],
        "mod_id": blueprint["mod_id"],
    }

    # 准备包路径
    package_path = blueprint["package_name"].replace(".", "/")
    java_dir = project_dir / "src" / "main" / "java" / package_path
    java_dir.mkdir(parents=True, exist_ok=True)

    # 需要生成的文件列表：模板名 -> 输出文件名
    files_to_generate = {
        "ModItemIds.java.jinja": "ModItemIds.java",
        "ModItems.java.jinja": "ModItems.java",
        "ModItemsGenerated.java.jinja": "ModItemsGenerated.java",
    }

    for template_name, output_name in files_to_generate.items():
        template = env.get_template(template_name)
        content = template.render(**context)
        (java_dir / output_name).write_text(content, encoding="utf-8")