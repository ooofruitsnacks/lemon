# SPDX-License-Identifier: AGPL-3.0-only

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "lemon/config.json"

FONT = (
    '"JetBrains Mono", "Twemoji", '
    '"Apple Color Emoji", "Segoe UI Emoji", monospace'
)

USERNAME_COLORS = [
    "#395F32", "#815600", "#006963", "#435C94",
    "#79518A", "#994460", "#875135", "#4D6642",
]

FONT_FACES = [
    {
        "font-family": "JetBrains Mono",
        "font-style": "normal",
        "font-weight": weight,
        "font-display": "swap",
        "src": [{
            "url": f"lemon-fonts/JetBrainsMono-{name}.ttf",
            "format": "truetype",
        }],
    }
    for name, weight in [("Regular", "400"), ("Bold", "700")]
]


def make_theme(name, rail, sidebar, header, canvas, menu, hover):
    text = "#283D2B"
    secondary = "#52654A"
    accent = "#416B35"
    border = "#94AA75"

    return {
        "name": name,
        "is_dark": False,
        "fonts": {
            "faces": FONT_FACES,
            "general": FONT,
            "monospace": FONT,
        },
        "colors": {
            "accent-color": accent,
            "primary-color": accent,
            "warning-color": "#AF352F",
            "sidebar-color": rail,
            "roomlist-background-color": sidebar,
            "roomlist-text-color": text,
            "roomlist-text-secondary-color": secondary,
            "roomlist-highlights-color": hover,
            "roomlist-separator-color": border,
            "timeline-background-color": canvas,
            "timeline-text-color": text,
            "timeline-text-secondary-color": secondary,
            "timeline-highlights-color": hover,
            "username-colors": USERNAME_COLORS,
            "avatar-background-colors": USERNAME_COLORS,

            # Extra color variables used by cartoon.css.
            "lemon-rail": rail,
            "lemon-sidebar": sidebar,
            "lemon-header": header,
            "lemon-canvas": canvas,
            "lemon-menu": menu,
            "lemon-hover": hover,
            "lemon-border": border,
            "lemon-text": text,
        },
        "compound": {
            "--cpd-font-family-sans": FONT,

            "--cpd-color-bg-canvas-default": canvas,
            "--cpd-color-bg-canvas-disabled": sidebar,
            "--cpd-color-bg-subtle-primary": sidebar,
            "--cpd-color-bg-subtle-secondary": menu,
            "--cpd-color-bg-subtle-tertiary": header,

            "--cpd-color-bg-action-primary-rest": accent,
            "--cpd-color-bg-action-primary-hovered": "#34592B",
            "--cpd-color-bg-action-primary-pressed": "#294823",
            "--cpd-color-bg-action-secondary-rest": menu,
            "--cpd-color-bg-action-secondary-hovered": hover,
            "--cpd-color-bg-action-secondary-pressed": header,
            "--cpd-color-bg-action-tertiary-hovered": hover,

            "--cpd-color-text-primary": text,
            "--cpd-color-text-secondary": secondary,
            "--cpd-color-text-action-primary": text,
            "--cpd-color-text-action-accent": accent,
            "--cpd-color-text-on-solid-primary": "#FFF8CB",

            "--cpd-color-icon-primary": text,
            "--cpd-color-icon-secondary": secondary,
            "--cpd-color-icon-accent-tertiary": accent,
            "--cpd-color-icon-on-solid-primary": "#FFF8CB",

            "--cpd-color-border-interactive-primary": accent,
            "--cpd-color-border-interactive-secondary": border,
            "--cpd-color-border-focused": accent,
        },
    }


config = json.loads(CONFIG.read_text(encoding="utf-8"))
settings = config.setdefault("setting_defaults", {})

# Preserve any additional themes you have added.
replaced_names = {"Lemon", "Lemon Summer Breeze", "Lemon at Dusk"}
other_themes = [
    theme
    for theme in settings.get("custom_themes", [])
    if theme.get("name") not in replaced_names
]

settings["custom_themes"] = [
    make_theme(
        "Lemon Summer Breeze",
        rail="#D0E8A8",
        sidebar="#F8EDAC",
        header="#DDF0C5",
        canvas="#FFF8DC",
        menu="#F4F1C5",
        hover="#E4EBAC",
    ),
    make_theme(
        "Lemon at Dusk",
        rail="#BECEA0",
        sidebar="#E1DDA8",
        header="#CBDCB5",
        canvas="#EDE8CB",
        menu="#E4E1BC",
        hover="#D1D8A0",
    ),
    *other_themes,
]

config["default_theme"] = "custom-Lemon Summer Breeze"

CONFIG.write_text(
    json.dumps(config, indent=2) + "\n",
    encoding="utf-8",
)

print("Updated Lemon's pastel themes and bundled font settings.")
