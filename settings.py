import json
import os
import sys

DEFAULT_SETTINGS = {
    "keybinds": {
        "initialScreenshot": "f8",
        "scoreboard": "tab"
    }
}

def _base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def load_settings():
    path = os.path.join(_base_dir(), "settings.json")
    if not os.path.exists(path):
        return DEFAULT_SETTINGS

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    keybinds = data.get("keybinds", {})
    return {
        "keybinds": {
            "initialScreenshot": keybinds.get("initialScreenshot", "f8"),
            "scoreboard": keybinds.get("scoreboard", "tab")
        }
    }
