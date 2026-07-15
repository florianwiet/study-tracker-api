from pathlib import Path
from datetime import date, datetime
import json

DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "entries.json"

def _json_default(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"Not serializable: {type(value)}")


def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE,"r") as f:
            content = f.read()
            if content.strip():
                return json.loads(content)
    return []

def save_data(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=_json_default)