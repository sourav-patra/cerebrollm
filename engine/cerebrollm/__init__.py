"""cerebrollm: local retrieval over your own authoritative documents, with quote verification."""
import os

__version__ = "0.1.0"

# Local only: no telemetry, no hub downloads. Set before any library import.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("DO_NOT_TRACK", "1")
os.environ.setdefault("OLLAMA_HOST", "http://127.0.0.1:11434")
