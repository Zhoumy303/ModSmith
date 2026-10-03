"""根据蓝图渲染 Fabric 项目模板。"""

import os
import shutil
import stat
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from modsmith.config import default_context

TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "fabric-project"

BINARY_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".jar", ".zip"}
COPY_ONLY_FILES = {"gradlew", "gradlew.bat"}


def _is_binary(path: Path) -> bool:
    return path.suffix.lower() in BINARY_EXTENSIONS


def _is_copy_only(path: Path) -> bool:
    return path.name in COPY_ONLY_FILES


def render_project(blueprint: dict, output_dir: Path) -> None:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        keep_trailing_newline=True,
    )
    
    defaults = default_context()

    context = {
        "mod_id": blueprint["mod_id"],
        "mod_name": blueprint.get("mod_name", blueprint["mod_id"]),
        "mod_description": blueprint.get("description", defaults["mod_description"]),
        "mod_version": blueprint.get("version", defaults["mod_version"]),
        "package_name": blueprint["package_name"],
        "package_path": blueprint["package_name"].replace(".", "/"),
        # 版本相关字段强制使用 config.py 的值，蓝图不能覆盖
        "minecraft_version": defaults["minecraft_version"],
        "fabric_loader_version": defaults["fabric_loader_version"],
        "loom_version": defaults["loom_version"],
        "fabric_api_version": defaults["fabric_api_version"],
        "author": blueprint.get("author", defaults["author"]),
    }

    if output_dir.exists():
        shutil.rmtree(output_dir)

    for template_path in TEMPLATE_DIR.rglob("*"):
        if template_path.is_dir():
            continue
        if any(part.startswith(".") and part not in {".gitignore"} for part in template_path.parts):
            continue

        rel_path = template_path.relative_to(TEMPLATE_DIR)
        rel_str = str(rel_path)

        rendered_rel_str = env.from_string(rel_str).render(**context)
        rendered_rel_path = Path(rendered_rel_str)

        if "src/main/java/com/example" in rendered_rel_str:
            rendered_rel_str = rendered_rel_str.replace(
                "src/main/java/com/example",
                f"src/main/java/{context['package_path']}"
            )
            rendered_rel_path = Path(rendered_rel_str)

        output_path = output_dir / rendered_rel_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if _is_binary(template_path) or _is_copy_only(template_path):
            shutil.copy2(template_path, output_path)
            continue

        try:
            content = template_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            shutil.copy2(template_path, output_path)
            continue

        rendered_content = env.from_string(content).render(**context)
        output_path.write_text(rendered_content, encoding="utf-8")

    gradlew_path = output_dir / "gradlew"
    if gradlew_path.exists():
        current_mode = gradlew_path.stat().st_mode
        gradlew_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    print(f"✅ 项目已生成到: {output_dir}")


from modsmith.generator.java import generate_java_items
from modsmith.generator.resources import generate_resources

def generate_project(blueprint: dict, output_dir: Path) -> None:
    """根据蓝图生成完整的 Fabric 项目。

    Args:
        blueprint: 通过校验的蓝图字典。
        output_dir: 输出项目目录。
    """
    # 1. 渲染基础项目模板
    render_project(blueprint, output_dir)

    # 2. 生成物品 Java 代码
    generate_java_items(blueprint, output_dir)

    # 3. 生成资源文件
    generate_resources(blueprint, output_dir)

    print(f"✅ 项目已完整生成到: {output_dir}")