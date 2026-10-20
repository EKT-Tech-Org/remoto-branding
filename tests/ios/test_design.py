import importlib.util
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "design/ios/style_dashboard.py"
spec = importlib.util.spec_from_file_location("style_dashboard", TOOL)
design = importlib.util.module_from_spec(spec)
spec.loader.exec_module(design)


def behavior(value):
    """Remove just the intended style/presentation fields for comparison."""
    if isinstance(value, list):
        return [behavior(item) for item in value]
    if isinstance(value, dict):
        return {key: behavior(item) for key, item in value.items()
                if key != "card_mod" and not (key == "needle" and
                    value.get("type") == "gauge" and "segments" not in value)}
    return value


class DesignTests(unittest.TestCase):
    def fixture(self):
        return {"title": "Test", "background": "var(--background-image)", "views": [{
            "cards": [{"type": "conditional", "conditions": [
                {"entity": "binary_sensor.grid", "state": "on"}], "card": {
                    "type": "vertical-stack", "cards": [
                        {"type": "gauge", "entity": "sensor.current", "min": 0,
                         "max": 120, "unit": "A", "needle": True,
                         "severity": {"green": 0, "yellow": 80, "red": 100}},
                        {"type": "tile", "entity": "switch.light", "tap_action": {
                            "action": "toggle", "confirmation": {"text": "Confirm?"}}},
                        {"type": "custom:mushroom-template-card", "entity": "sensor.fault",
                         "icon_color": "{{ 'red' if is_state(entity, 'on') else 'green' }}",
                         "primary": "{{ states(entity) }}", "card_mod": {"style": {
                             ".": "ha-card { height: 80px; }",
                             "other-element$": ".label { color: orange; }"}}}]}}]}]}

    def test_preserves_monitoring_and_controls(self):
        original = self.fixture()
        snapshot = deepcopy(original)
        styled, count = design.transform(original)
        self.assertEqual(original, snapshot)
        self.assertEqual(behavior(styled), behavior(original))
        self.assertEqual(count["styled"], 3)
        self.assertEqual(count["filled_gauges"], 1)

    def test_keeps_dynamic_colors_and_existing_shadow_rules(self):
        styled, _ = design.transform(self.fixture())
        mushroom = styled["views"][0]["cards"][0]["card"]["cards"][2]
        style = mushroom["card_mod"]["style"]
        self.assertNotIn("--icon-color:", style["."])
        self.assertIn("height: 80px", style["."])
        self.assertEqual(style["other-element$"], ".label { color: orange; }")
        self.assertIn("background: transparent", style["mushroom-shape-icon$"])

    def test_static_mushroom_icon_follows_theme(self):
        for kind in ("custom:mushroom-template-card", "custom:mushroom-legacy-template-card"):
            doc = {"views": [{"cards": [{"type": kind, "icon_color": "blue"}]}]}
            styled, _ = design.transform(doc)
            self.assertIn("--icon-color:", styled["views"][0]["cards"][0]["card_mod"]["style"]["."])

    def test_segmented_gauge_retains_needle_and_thresholds(self):
        doc = {"views": [{"cards": [{"type": "gauge", "needle": True,
               "entity": "sensor.load", "segments": [{"from": 0, "color": "green"}]}]}]}
        result, count = design.transform(doc)
        self.assertTrue(result["views"][0]["cards"][0]["needle"])
        self.assertEqual(count["segmented_gauges_kept"], 1)
        self.assertEqual(result["views"][0]["cards"][0]["segments"], doc["views"][0]["cards"][0]["segments"])

    def test_idempotent_and_preserves_unrelated_custom_card(self):
        doc = self.fixture()
        doc["views"][0]["cards"].append({"type": "custom:other-card", "card_mod": {
            "style": "ha-card { color: red; }"}, "entity": "sensor.test"})
        once, _ = design.transform(doc)
        twice, _ = design.transform(once)
        self.assertEqual(once, twice)
        self.assertEqual(once["views"][0]["cards"][-1], doc["views"][0]["cards"][-1])

    def test_cli_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.yaml"
            target = Path(directory) / "target.yaml"
            source.write_text(yaml.safe_dump(self.fixture()))
            target.write_text("keep this backup")
            run = subprocess.run([sys.executable, str(TOOL), str(source), str(target)],
                                 capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual(target.read_text(), "keep this backup")

    def test_starter_matches_generated_and_is_read_only(self):
        source = yaml.safe_load((ROOT / "design/ios/starter.source.yaml").read_text())
        expected, _ = design.transform(source)
        actual = yaml.safe_load((ROOT / "design/ios/starter.yaml").read_text())
        self.assertEqual(actual, expected)
        self.assertNotIn("action: toggle", yaml.safe_dump(actual))
        self.assertNotIn("action: perform-action", yaml.safe_dump(actual))

    def test_rejects_non_dashboard(self):
        with self.assertRaisesRegex(ValueError, "views list"):
            design.transform({"frontend": {}})


if __name__ == "__main__":
    unittest.main()
