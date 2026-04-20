import json
import os

HISTORY_FILE = "history.json"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []

    with open(HISTORY_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return []

def save_history(entry: dict):
    history = load_history()
    history.append(entry)

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def get_recent_history(n=3):
    return load_history()[-n:]