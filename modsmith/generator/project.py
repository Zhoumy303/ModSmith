"""根据蓝图渲染 Fabric 项目模板。"""

import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "fabric-project"


def render_project(blueprint: dict, output_dir: Path) -> None:
    """将蓝图渲染到输出目录。

    Args:
        blueprint: 蓝图字典。
        output_dir: 输出项目目录。
    """
    # 准备 Jinja2 环境
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        keep_trailing_newline=True,
    )

    # 准备渲染上下文
    context = {
        "mod_id": blueprint["mod_id"],
        "mod_name": blueprint.get("mod_name", blueprint["mod_id"]),
        "mod_description": blueprint.get("description", "A ModSmith generated mod"),
        "mod_version": blueprint.get("version", "0.1.0"),
        "package_name": blueprint["package_name"],
        "package_path": blueprint["package_name"].replace(".", "/"),
        "minecraft_version": blueprint["minecraft_version"],
        "fabric_loader_version": blueprint["fabric_loader_version"],
        "yarn_mappings": blueprint.get("yarn_mappings", "1.21.4+build.1"),
        "loom_version": blueprint.get("loom_version", "1.10-SNAPSHOT"),
        "fabric_api_version": blueprint.get("fabric_api_version", "0.119.2+1.21.4"),
        "author": blueprint.get("author", "ModSmith User"),
    }

    # 如果输出目录已存在，先删除
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # 遍历模板目录，渲染每个文件
    for template_path in TEMPLATE_DIR.rglob("*"):
        if template_path.is_dir():
            continue

        # 计算相对路径
        rel_path = template_path.relative_to(TEMPLATE_DIR)
        rel_str = str(rel_path)

        # 渲染文件路径（处理 {{ mod_id }} 等）
        rendered_rel_str = env.from_string(rel_str).render(**context)
        rendered_rel_path = Path(rendered_rel_str)

        # 处理包名路径替换
        if "src/main/java/com/example" in rendered_rel_str:
            rendered_rel_str = rendered_rel_str.replace(
                "src/main/java/com/example",
                f"src/main/java/{context['package_path']}"
            )
            rendered_rel_path = Path(rendered_rel_str)

        output_path = output_dir / rendered_rel_path
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 检查文件是否为二进制文件（根据扩展名）
        binary_extensions = {'.jar', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.bmp', '.webp', '.exe', '.dll', '.so', '.class', '.pyc'}
        if template_path.suffix.lower() in binary_extensions:
            # 二进制文件直接复制
            shutil.copy2(template_path, output_path)
        else:
            # 文本文件使用 Jinja2 渲染
            content = template_path.read_text(encoding="utf-8")
            rendered_content = env.from_string(content).render(**context)
            output_path.write_text(rendered_content, encoding="utf-8")

    print(f"✅ 项目已生成到: {output_dir}")