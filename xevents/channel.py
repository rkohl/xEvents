from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from xevents.constants import CHANNEL_SEP
from xevents.types import Event, EventData, Listener

if TYPE_CHECKING:
    from xevents.bus import xEvents


class Channel:
    def __init__(self, name: str, parent: xEvents):
        self.name = name
        self._parent = parent

    def subscribe(
        self,
        event: Event,
        listener: Listener,
        once: bool = False,
        filter_fn: Callable[[EventData], bool] | None = None,
    ) -> None:
        self._parent.subscribe(self._scoped(event), listener, once=once, filter_fn=filter_fn)

    def unsubscribe(self, event: Event, listener: Listener) -> None:
        self._parent.unsubscribe(self._scoped(event), listener)

    def post(self, event: Event, data: EventData) -> None:
        self._parent.post(self._scoped(event), data)

    def on(self, event: Event, listener: Listener) -> None:
        self.subscribe(event, listener)

    def once(self, event: Event, listener: Listener) -> None:
        self.subscribe(event, listener, once=True)

    def _scoped(self, event: Event) -> Event:
        return f"{self.name}{CHANNEL_SEP}{event}"

    def __repr__(self) -> str:
        return f"Channel({self.name!r})"
