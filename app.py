"""
Hugging Face Spaces entry point.
HF Spaces expects the app to be importable as `app` from this file.
"""
from server import app  # noqa: F401 — re-exported for uvicorn / HF
