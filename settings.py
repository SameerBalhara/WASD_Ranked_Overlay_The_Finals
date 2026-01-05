import json
import os
import sys

DEFAULT_SETTINGS = {
    "keybinds": {
        "initialScreenshot": "f8",
        "scoreboard": "tab"
    }
}

def _first_existing(*paths):
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None

def load_settings():
    exe_dir = os.path.dirname(sys.executable)
    mod_dir = os.path.dirname(os.path.abspath(__file__))
    cwd = os.getcwd()

    path = _first_existing(
        os.path.join(exe_dir, "settings.json"),
        os.path.join(cwd, "settings.json"),
        os.path.join(mod_dir, "settings.json"),
    )

    if path is None:
        return DEFAULT_SETTINGS

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    keybinds = data.get("keybinds", {})
    init_key = str(keybinds.get("initialScreenshot", "f8")).lower()
    score_key = str(keybinds.get("scoreboard", "tab")).lower()

    return {"keybinds": {"initialScreenshot": init_key, "scoreboard": score_key}}
