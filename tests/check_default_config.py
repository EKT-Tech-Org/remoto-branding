"""Fail if our default_config replacement drifts from upstream.

Run inside the image:  python /check.py /config/configuration.yaml
Upstream default_config minus zeroconf must all be listed (backup is an allowed extra).
"""

import json
from pathlib import Path
import re
import sys

import homeassistant.components.default_config as dc

upstream = set(json.loads((Path(dc.__file__).parent / "manifest.json").read_text())["dependencies"])
upstream.discard("zeroconf")
ours = set(re.findall(r"^([a-z0-9_]+):", Path(sys.argv[1]).read_text(), re.M))
missing = sorted(upstream - ours)
if missing:
    sys.exit(f"configuration is missing upstream default_config items: {missing}")
print(f"default_config check ok ({len(upstream)} items)")
