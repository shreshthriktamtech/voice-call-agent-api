import json

def load_config():
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise Exception("❌ config.json not found")
    except json.JSONDecodeError:
        raise Exception("❌ config.json contains invalid JSON")