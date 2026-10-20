#!/usr/bin/env python3
"""Style an exported Lovelace dashboard. Writes a NEW file; never deploys."""
from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
import sys

import yaml

MARKER = "/* Remoto iOS v1 */"
FRAME = MARKER + """
ha-card {
  background: var(--ha-card-background, var(--card-background-color));
  color: var(--primary-text-color);
  border-radius: 18px;
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.20);
  overflow: hidden;
  --mdc-icon-size: 24px;
}
ha-state-icon, ha-icon { --mdc-icon-size: 24px; }
ha-tile-icon {
  --tile-icon-opacity: 0 !important;
  --tile-icon-hover-opacity: 0 !important;
}
mushroom-shape-icon { --icon-symbol-size: 24px; }
"""
STATIC_ICON = """
ha-tile-icon {
  --tile-icon-color: var(--state-icon-color, var(--primary-text-color)) !important;
}
mushroom-shape-icon {
  --icon-color: var(--state-icon-color, var(--primary-text-color)) !important;
  --icon-color-disabled: var(--disabled-text-color) !important;
}
"""
SHAPE = MARKER + """
.shape, .shape.disabled {
  background: transparent !important;
  box-shadow: none !important;
}
"""
SUPPORTED = {"gauge", "tile", "entity", "entities", "button",
             "custom:mushroom-template-card", "custom:mushroom-legacy-template-card"}


def append_css(existing: str, addition: str) -> str:
    if not isinstance(existing, str):
        raise ValueError("card_mod CSS must be a string; export raw dashboard YAML")
    return existing if MARKER in existing else existing.rstrip() + "\n" + addition


def style_card(card: dict) -> None:
    mushroom = card["type"].startswith("custom:mushroom-")
    css = FRAME
    if mushroom:
        # Keep Jinja/JS status colors, including fault and phase imbalance colors.
        color = str(card.get("color", card.get("icon_color", "")))
        if not any(token in color for token in ("{{", "{%", "[[[")):
            css += STATIC_ICON
    mod = card.setdefault("card_mod", {})
    if not isinstance(mod, dict):
        raise ValueError("card_mod must be a mapping")
    style = mod.get("style", "")
    if mushroom or isinstance(style, dict):
        if isinstance(style, str):
            style = {".": style}
        if not isinstance(style, dict):
            raise ValueError("Unsupported card_mod.style format")
        style["."] = append_css(style.get(".", ""), css)
        if mushroom:
            style["mushroom-shape-icon$"] = append_css(
                style.get("mushroom-shape-icon$", ""), SHAPE)
        mod["style"] = style
    else:
        mod["style"] = append_css(style, css)


def transform(document: dict) -> tuple[dict, dict]:
    if not isinstance(document, dict) or not isinstance(document.get("views"), list):
        raise ValueError("Expected a full raw dashboard with a views list")
    result = deepcopy(document)
    result.setdefault("background", "var(--background-image)")
    counts = {"styled": 0, "filled_gauges": 0, "segmented_gauges_kept": 0}

    def walk(value):
        if isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, dict):
            if value.get("type") in SUPPORTED:
                style_card(value)
                counts["styled"] += 1
                if value["type"] == "gauge":
                    # HA requires needle:true for segmented gauges. Keep these intact.
                    if "segments" in value:
                        counts["segmented_gauges_kept"] += 1
                    else:
                        value["needle"] = False
                        counts["filled_gauges"] += 1
            for key, item in value.items():
                if key != "card_mod":
                    walk(item)

    walk(result["views"])
    return result, counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Exported raw dashboard YAML")
    parser.add_argument("output", type=Path, help="New YAML file (must not exist)")
    args = parser.parse_args()
    try:
        result, counts = transform(yaml.safe_load(args.input.read_text()))
        # Serialize before creating anything; exclusive creation protects source/exports.
        text = yaml.safe_dump(result, sort_keys=False, allow_unicode=True, width=120)
        with args.output.open("x") as target:
            target.write(text)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"No dashboard deployed: {exc}", file=sys.stderr)
        return 1
    print(f"Created {args.output}: {counts}. Review and import into a TEST dashboard.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
