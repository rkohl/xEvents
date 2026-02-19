from typing import Any, Callable

type Event = str
type EventData = dict[str, Any]
type Listener = Callable
type Events = list[Event]
