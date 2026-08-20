"""Premium visual design tokens for the ULTRON desktop UI."""

from __future__ import annotations

PALETTE = {
    "bg": "#0A0505",
    "bg_elevated": "#150808",
    "surface": "#150808",
    "surface_soft": "#210D0D",
    "surface_glass": "#0D0505",
    "line": "#3D1013",
    "line_soft": "#5C161B",
    "line_hot": "#FF1E2D",
    "cyan": "#FF1E2D",
    "cyan_soft": "#FF5C64",
    "cyan_hot": "#FF9AA0",
    "blue": "#8A0F14",
    "amber": "#FFC857",
    "green": "#00FFC6",
    "red": "#FF3B30",
    "text": "#F5E8E9",
    "text_muted": "#C79098",
    "text_faint": "#7A4A4F",
    "ink": "#0D0505",
}

FONTS = {
    "display": "Orbitron",
    "ui": "Bahnschrift",
    "mono": "Cascadia Mono",
}

RADIUS = {
    "card": 8,
    "button": 8,
    "pill": 999,
}


def build_design_tokens() -> dict:
    """Return stable design tokens for tests, docs, and UI modules."""

    return {
        "name": "Cyber Hologram",
        "palette": dict(PALETTE),
        "fonts": dict(FONTS),
        "radius": dict(RADIUS),
        "spacing": {"xs": 6, "sm": 10, "md": 16, "lg": 24, "xl": 34},
    }


def font(kind: str, size: int, weight: str | None = None) -> tuple:
    """Build a CustomTkinter font tuple from theme tokens."""

    family = FONTS.get(kind, FONTS["ui"])
    return (family, size, weight) if weight else (family, size)
