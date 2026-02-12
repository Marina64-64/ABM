"""Shared utilities across all tasks."""

import os
from pathlib import Path


def ensure_dir(path: str) -> Path:
    """Ensure directory exists, create if not."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent.parent


def get_data_dir() -> Path:
    """Get data directory."""
    return get_project_root() / "data"


def get_logs_dir() -> Path:
    """Get logs directory."""
    return ensure_dir(get_data_dir() / "logs")


def get_results_dir() -> Path:
    """Get results directory."""
    return ensure_dir(get_data_dir() / "results")


def get_output_dir() -> Path:
    """Get output directory."""
    return ensure_dir(get_data_dir() / "output")
