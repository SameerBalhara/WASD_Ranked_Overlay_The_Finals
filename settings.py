import json
import os

DEFAULT_SETTINGS = {
    "keybinds": {
        "initialScreenshot": "f8",
        "scoreboard": "tab"
    }
}

def load_settings(path = "settings.json"):
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
