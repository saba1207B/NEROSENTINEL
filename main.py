# Copyright (c) 2026 Sabareesh M (saba1207B). All Rights Reserved.
#
# This source code is proprietary and confidential.
#
# Unauthorized copying, redistribution, modification, or use — including
# any use for artificial intelligence / machine learning training —
# is strictly prohibited.
#
# See the LICENSE and COPYRIGHT files in the repository root for full terms.

"""Vercel entrypoint for NeroSentinel FastAPI backend service."""
import sys
from pathlib import Path

# Ensure 'src' is in python path so aquasentinel package can be imported
_src_path = str(Path(__file__).parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from aquasentinel.main import app  # noqa: E402, F401
