import json
from pathlib import Path

from aquasentinel.main import app

root = Path(__file__).resolve().parents[1]
(root / "contracts").mkdir(exist_ok=True)
(root / "contracts" / "openapi.json").write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
print(root / "contracts" / "openapi.json")

