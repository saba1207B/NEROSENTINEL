"""Vercel entrypoint for NeroSentinel FastAPI backend service."""
import sys
from pathlib import Path

# Ensure 'src' is in python path so aquasentinel package can be imported
_src_path = str(Path(__file__).parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

from aquasentinel.main import app  # noqa: E402, F401
