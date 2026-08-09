"""CrewAI runtime evidence adapter for ChartworkAI."""

__version__ = "0.1.0"

from .adapter import CrewAIAdapter
from .models import CapturePolicy, HandoffSpec, RecordedRun, RecordWriteError

__all__ = [
    "CapturePolicy",
    "CrewAIAdapter",
    "HandoffSpec",
    "RecordedRun",
    "RecordWriteError",
]
