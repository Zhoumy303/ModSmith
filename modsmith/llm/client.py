"""LLM client for generating blueprints from natural language."""

import os
import json
from pathlib import Path

import anthropic
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 智谱 GLM 的 Anthropic 兼容端点
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/anthropic"

# 默认模型（可在 .env 中覆盖）
DEFAULT_MODEL = os.environ.get("GLM_MODEL", "glm-5.3")

# 蓝图 Schema 路径
SCHEMA_PATH = Path(__file__).parent.parent / "blueprint" / "schema.json"
EXAMPLES_DIR = Path(__file__).parent.parent / "blueprint" / "examples"


def _load_schema() -> dict:
    """加载蓝图 JSON Schema。"""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_examples() -> list[dict]:
    """加载 few-shot 示例蓝图。"""
    from modsmith.config import default_context
    defaults = default_context()

    examples = []
    if EXAMPLES_DIR.exists():
        for path in sorted(EXAMPLES_DIR.glob("*.json")):
            with open(path, "r", encoding="utf-8") as f:
                example = json.load(f)
            # 用配置中的版本覆盖示例中的版本
            example["minecraft_version"] = defaults["minecraft_version"]
            example["fabric_loader_version"] = defaults["fabric_loader_version"]
            examples.append(example)
    return examples


def _build_system_prompt() -> str:
    """构建 System Prompt，包含 Schema 和 few-shot 示例。"""
    schema = _load_schema()
    examples = _load_examples()

    prompt = f"""你是一个 Minecraft Fabric 模组蓝图生成器。

你的任务是根据用户的自然语言描述，生成符合以下 JSON Schema 的蓝图。

## Schema

```json
{json.dumps(schema, indent=2, ensure_ascii=False)}
```

## 示例

"""

    for i, example in enumerate(examples, 1):
        prompt += f"### 示例 {i}\n\n```json\n{json.dumps(example, indent=2, ensure_ascii=False)}\n```\n\n"

    prompt += """## 规则

1. 只输出 JSON，不要任何解释、注释或 Markdown 代码块标记。
2. 所有必填字段必须存在。
3. `type` 字段只能是以下值之一：basic、food、tool。
4. 如果描述不明确，使用合理的默认值。
5. `texture` 字段如果无法确定，使用 "auto"。

## 各类型的必填字段
basic：id、type、display_name_en、visual
food：id、type、display_name_en、nutrition、saturation、always_edible、visual
tool：id、type、display_name_en、tool_type、durability、mining_speed、attack_damage、visual

## 默认值建议
saturation：0.3
always_edible：true
effects：空数组 []
texture："auto"

## 视觉特征必须由你主动推断
用户描述模组时通常不会提到贴图长什么样。你必须根据物品的名称、类型、效果，主动推断出合理的 visual 字段，不要留空、不要输出 "auto"、不要省略。

推断方法
1. 先看名称关键词，决定 shape：
    苹果、浆果、果实、面包、肉 → round / organic
    宝石、水晶、钻石、矿石、碎片 → crystal
    剑、刀刃、匕首 → blade
    斧、镐 → axe / pickaxe
    药水、血浆、液体、燃料 → liquid
    锭、块、金属 → ingot
2. 再看效果，决定 primary_color：
    回血、生命恢复 → #dc2626（红）
    加速、夜视 → #22d3ee（青）
    中毒、凋零 → #4d7c0f / #7e22ce（深绿/紫）
    力量、攻击 → #ea580c（橙红）
    幸运、财富 → #f59e0b（金）
    寒冷、冰霜 → #93c5fd（蓝白）
    无明显效果 → 根据名称推断（钻石→#22d3ee，红宝石→#dc2626，金锭→#f59e0b）
3. 最后看名称形容词，决定 pattern：
    闪烁、发光 → sparkle
    神秘、暗影 → glow
    破碎、古老的 → cracks
    纯净、光滑 → none
4. accent_color 的推断：
    通常是 primary_color 的亮版（每个 RGB 分量 + 40 到 +80，上限 255）
    也可以根据物品类型选一个撞色（如红色果实用绿色高光 #86efac）
5. 兜底：如果以上都推断不出，用 shape = abstract，primary_color 从物品 ID 推断。

示例
用户输入"创建一个吃了回血的苹果"
→ 名称有"苹果" → shape = round
→ 效果是"回血" → primary_color = #dc2626
→ accent_color = #86efac（果实的绿色高光）
→ pattern = sparkle

用户输入"做一个闪烁的钻石"
→ 名称有"钻石" → shape = crystal
→ 名称有"闪烁" → pattern = sparkle
→ primary_color = #22d3ee（钻石的青蓝色）
→ accent_color = #67e8f9

用户输入"创建一把基迪特剑"
→ 名称有"剑" → shape = blade
→ 无特殊效果 → primary_color = #94a3b8（金属灰）
→ accent_color = #cbd5e1
→ pattern = none

用户输入"做一个神秘的紫色药水"
→ 名称有"药水" → shape = liquid
→ 名称有"神秘" → pattern = glow
→ 名称有"紫色" → primary_color = #a855f7
→ accent_color = #c084fc

##版本要求（必须严格遵守）
minecraft_version 必须是 "{MINECRAFT_VERSION}"
fabric_loader_version 必须是 "{FABRIC_LOADER_VERSION}"
不要使用任何其他版本号。
"""

    from modsmith.config import MINECRAFT_VERSION, FABRIC_LOADER_VERSION
    prompt = prompt.replace("{MINECRAFT_VERSION}", MINECRAFT_VERSION)
    prompt = prompt.replace("{FABRIC_LOADER_VERSION}", FABRIC_LOADER_VERSION)
    return prompt


def get_client() -> anthropic.Anthropic:
    """创建并返回智谱 GLM 的 Anthropic 客户端。"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY 未设置。请在 .env 文件中配置你的智谱 API Key。"
        )

    return anthropic.Anthropic(
        api_key=api_key,
        base_url=ZHIPU_BASE_URL,
    )


def generate_blueprint(user_input: str) -> dict:
    """将自然语言描述转换为结构化的蓝图 JSON。

    Args:
        user_input: 用户对模组的自然语言描述。

    Returns:
        符合 Schema 的蓝图字典。

    Raises:
        ValueError: 当 API Key 未配置时。
        json.JSONDecodeError: 当 LLM 返回的内容不是合法 JSON 时。
    """
    client = get_client()
    system_prompt = _build_system_prompt()

    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_input},
        ],
    )

    # 提取文本内容
    response_text = message.content[0].text.strip()

    # 去除可能的 Markdown 代码块标记
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        response_text = "\n".join(lines[1:-1])

    # 解析 JSON
    blueprint = json.loads(response_text)
    return blueprint