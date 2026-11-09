# Copyright (c) 2026 Sabareesh M (saba1207B). All Rights Reserved.
#
# This source code is proprietary and confidential.
#
# Unauthorized copying, redistribution, modification, or use — including
# any use for artificial intelligence / machine learning training —
# is strictly prohibited.
#
# See the LICENSE and COPYRIGHT files in the repository root for full terms.

import json
from pathlib import Path

from aquasentinel.main import app

root = Path(__file__).resolve().parents[1]
(root / "contracts").mkdir(exist_ok=True)
(root / "contracts" / "openapi.json").write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
print(root / "contracts" / "openapi.json")

