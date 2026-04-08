"""
server/app.py — OpenEnv multi-mode deployment entry point.
The validator expects this file at server/app.py.
Imports the FastAPI app from the root server module.
"""
import sys
import os

# Ensure repo root is on path so we can import server.py from root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import app  # noqa: F401 — re-exported for uvicorn / openenv-core

__all__ = ["app"]
