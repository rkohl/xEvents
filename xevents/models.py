from dataclasses import dataclass, field
from typing import Any, Optional
import time


@dataclass
class EventRecord:
    event: str
    data: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    channel: Optional[str] = None


@dataclass(frozen=True)
class _ListenerKey:
    event: str
    listener_id: int
