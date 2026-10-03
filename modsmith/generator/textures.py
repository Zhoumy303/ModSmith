"""Generate item textures: draw pixel art of different shapes based on visual features."""

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw


# ============================================================
# Utility functions
# ============================================================

def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert '#dc2626' to (220, 38, 38)."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _color_from_id(item_id: str) -> tuple[int, int, int]:
    """Fallback: generate a deterministic color from the item ID."""
    digest = hashlib.md5(item_id.encode("utf-8")).hexdigest()
    return (int(digest[0:2], 16), int(digest[2:4], 16), int(digest[4:6], 16))


def _get_visual(item: dict) -> dict:
    """Extract visual features from the item definition, using fallbacks when missing.

    - If there is no primary_color, generate one from the item ID's MD5 hash.
    - If there is no accent_color, use a lighter version of the primary color.
    - If there is no shape, use "abstract".
    - If there is no pattern, use "none".
    """
    visual = dict(item.get("visual", {}))

    if not visual.get("primary_color"):
        r, g, b = _color_from_id(item["id"])
        visual["primary_color"] = f"#{r:02x}{g:02x}{b:02x}"

    if not visual.get("accent_color"):
        r, g, b = _hex_to_rgb(visual["primary_color"])
        visual["accent_color"] = (
            f"#{min(r+60,255):02x}{min(g+60,255):02x}{min(b+60,255):02x}"
        )

    visual.setdefault("shape", "abstract")
    visual.setdefault("pattern", "none")
    return visual


# ============================================================
# Shape drawing functions (each returns a 16x16 RGBA Image)
# ============================================================

def _draw_round(size: int, primary: tuple, accent: tuple) -> Image.Image:
    """Round/fruit: a circle with a highlight."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 2
    draw.ellipse(
        [margin, margin, size - margin - 1, size - margin - 1],
        fill=primary, outline=accent,
    )
    draw.ellipse([4, 4, 6, 6], fill=(255, 255, 255, 200))
    return img


def _draw_blade(size: int, primary: tuple, accent: tuple) -> Image.Image:
    """Sword/dagger: diagonal blade + hilt."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.line([(4, size - 5), (size - 3, 4)], fill=primary, width=3)
    draw.line([(5, size - 6), (size - 4, 3)], fill=accent, width=1)
    draw.line([(2, size - 3), (5, size - 6)], fill=(101, 67, 33), width=2)
    draw.line([(3, size - 8), (8, size - 3)], fill=accent, width=1)
    return img


def _draw_axe(size: int, primary: tuple, accent: tuple) -> Image.Image:
    """Axe: wooden handle + axe head."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.line([(5, size - 2), (size - 5, 4)], fill=(101, 67, 33), width=2)
    draw.polygon([(4, 4), (10, 2), (12, 7), (7, 9)], fill=primary, outline=accent)
    return img


def _draw_pickaxe(size: int, primary: tuple, accent: tuple) -> Image.Image:
    """Pickaxe: wooden handle + pick head."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.line([(5, size - 2), (size - 5, 4)], fill=(101, 67, 33), width=2)
    draw.arc([2, 2, size - 4, 10], start=180, end=360, fill=primary, width=2)
    draw.arc([3, 3, size - 5, 9], start=180, end=360, fill=accent, width=1)
    return img


def _draw_crystal(size: int, primary: tuple, accent: tuple) -> Image.Image:
    """Gem/ore: rhombus crystal with facet highlights."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    center = size // 2
    draw.polygon([
        (center, 2), (size - 3, center),
        (center, size - 3), (3, center),
    ], fill=primary, outline=accent)
    draw.polygon([
        (center, 3), (center + 3, center), (center, center + 1),
    ], fill=(255, 255, 255, 120))
    return img


def _draw_ingot(size: int, primary: tuple, accent: tuple) -> Image.Image:
    """Metal ingot: a 3D rectangular block."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.polygon(
        [(3, 6), (size - 4, 5), (size - 3, 9), (2, 10)],
        fill=accent, outline=primary,
    )
    draw.polygon(
        [(2, 10), (size - 3, 9), (size - 4, size - 3), (3, size - 2)],
        fill=primary, outline=accent,
    )
    return img


def _draw_liquid(size: int, primary: tuple, accent: tuple) -> Image.Image:
    """Bottled liquid: bottle outline + liquid."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([5, 7, size - 6, size - 3], fill=primary, outline=accent)
    draw.rectangle([7, 3, size - 8, 7], fill=accent)
    draw.rectangle([6, 2, size - 7, 3], fill=(101, 67, 33))
    return img


def _draw_organic(size: int, primary: tuple, accent: tuple) -> Image.Image:
    """Organic food: irregular blocky shape."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([2, 3, size - 3, size - 2], fill=primary, outline=accent)
    draw.ellipse([4, 5, 7, 8], fill=(255, 255, 255, 100))
    return img


def _draw_abstract(size: int, primary: tuple, accent: tuple) -> Image.Image:
    """Abstract: placeholder square with a dot in the center."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([1, 1, size - 2, size - 2], fill=primary, outline=accent)
    center = size // 2
    draw.ellipse(
        [center - 2, center - 2, center + 2, center + 2],
        fill=(255, 255, 255, 180),
    )
    return img


_SHAPE_DRAWERS = {
    "round": _draw_round,
    "blade": _draw_blade,
    "axe": _draw_axe,
    "pickaxe": _draw_pickaxe,
    "crystal": _draw_crystal,
    "ingot": _draw_ingot,
    "liquid": _draw_liquid,
    "organic": _draw_organic,
    "abstract": _draw_abstract,
}


# ============================================================
# Pattern overlay
# ============================================================

def _apply_pattern(img: Image.Image, pattern: str, accent: tuple) -> None:
    """Apply a pattern on top of the existing image."""
    draw = ImageDraw.Draw(img)
    size = img.width

    if pattern == "sparkle":
        for x, y in [(4, 4), (size - 6, 5), (5, size - 6)]:
            draw.point((x, y), fill=(255, 255, 255, 255))
            draw.point((x + 1, y), fill=(255, 255, 255, 180))
            draw.point((x, y + 1), fill=(255, 255, 255, 180))

    elif pattern == "glow":
        for i in range(1, 3):
            draw.rectangle(
                [i, i, size - 1 - i, size - 1 - i],
                outline=(accent[0], accent[1], accent[2], 100 - i * 30),
            )

    elif pattern == "cracks":
        draw.line([(3, 5), (7, 9)], fill=accent, width=1)
        draw.line([(7, 9), (5, 13)], fill=accent, width=1)

    elif pattern == "dots":
        for x in range(3, size - 3, 4):
            for y in range(3, size - 3, 4):
                draw.point((x, y), fill=accent)

    elif pattern == "stripes":
        for y in range(3, size - 3, 3):
            draw.line([(2, y), (size - 3, y)], fill=accent, width=1)


# ============================================================
# Entry points
# ============================================================

def generate_texture(item: dict, output_path: Path, size: int = 16) -> None:
    """Generate a single texture based on the item's visual features.

    Args:
        item: Item definition containing id, type, visual, etc.
        output_path: Output PNG path.
        size: Texture side length, default 16.
    """
    visual = _get_visual(item)

    primary = _hex_to_rgb(visual["primary_color"])
    accent = _hex_to_rgb(visual["accent_color"])
    shape = visual["shape"]
    pattern = visual["pattern"]

    drawer = _SHAPE_DRAWERS.get(shape, _draw_abstract)
    img = drawer(size, primary, accent)

    if pattern != "none":
        _apply_pattern(img, pattern, accent)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")


def generate_all_textures(blueprint: dict, project_dir: Path) -> None:
    """Generate textures for all items in the blueprint.

    Args:
        blueprint: Blueprint dictionary.
        project_dir: Root directory of the generated project.
    """
    mod_id = blueprint["mod_id"]
    textures_dir = (
        project_dir / "src" / "main" / "resources"
        / "assets" / mod_id / "textures" / "item"
    )

    for item in blueprint["items"]:
        output_path = textures_dir / f"{item['id']}.png"
        generate_texture(item, output_path)
        shape = item.get("visual", {}).get("shape", "abstract")
        print(f"  🎨 Generated texture: {output_path.name} ({shape})")