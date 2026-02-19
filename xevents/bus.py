from threading import RLock
from typing import Callable, List
from collections import defaultdict
from fnmatch import fnmatch
import asyncio
import logging

from xevents.channel import Channel
from xevents.constants import CHANNEL_SEP, DEFAULT_HISTORY_LIMIT
from xevents.models import EventRecord, _ListenerKey
from xevents.types import Event, EventData, Events, Listener

logger = logging.getLogger("xEvents")


class xEvents:
    def __init__(
        self,
        events: Events | None = None,
        debug: bool = False,
        history_limit: int = DEFAULT_HISTORY_LIMIT,
    ):
        self.__lock = RLock()
        self.__listeners: dict[Event, List[Listener]] = defaultdict(list)
        self.__once_listeners: set[_ListenerKey] = set()
        self.__wildcard_listeners: list[tuple[str, Listener]] = []
        self.__history: list[EventRecord] = []
        self.__history_limit = history_limit
        self.__channels: dict[str, Channel] = {}
        self.__filters: dict[_ListenerKey, Callable[[EventData], bool]] = {}
        self.enabled: bool = True
        self.debug: bool = debug

        if events:
            for ev in events:
                self.__listeners[ev] = []

        if self.debug:
            print(f"xEvents initialized with events: {events or []}")

    def channel(self, name: str) -> Channel:
        with self.__lock:
            if name not in self.__channels:
                self.__channels[name] = Channel(name, self)
            return self.__channels[name]

    def subscribe(
        self,
        event: Event,
        listener: Listener,
        once: bool = False,
        filter_fn: Callable[[EventData], bool] | None = None,
    ) -> None:
        with self.__lock:
            listeners = self.__listeners[event]
            if listener not in listeners:
                listeners.append(listener)
                key = _ListenerKey(event, id(listener))
                if once:
                    self.__once_listeners.add(key)
                if filter_fn:
                    self.__filters[key] = filter_fn
                if self.debug:
                    print(f"Listener {listener} added to event {event} (once={once})")

    def on(
        self,
        event: Event,
        listener: Listener,
        filter_fn: Callable[[EventData], bool] | None = None,
    ) -> None:
        self.subscribe(event, listener, filter_fn=filter_fn)

    def once(
        self,
        event: Event,
        listener: Listener,
        filter_fn: Callable[[EventData], bool] | None = None,
    ) -> None:
        self.subscribe(event, listener, once=True, filter_fn=filter_fn)

    def on_any(self, pattern: str, listener: Listener) -> None:
        with self.__lock:
            self.__wildcard_listeners.append((pattern, listener))
            if self.debug:
                print(f"Wildcard listener {listener} added for pattern {pattern!r}")

    def off_any(self, pattern: str, listener: Listener) -> None:
        with self.__lock:
            self.__wildcard_listeners = [
                (p, cb)
                for p, cb in self.__wildcard_listeners
                if not (p == pattern and cb is listener)
            ]

    def unsubscribe(self, event: Event, listener: Listener) -> None:
        with self.__lock:
            listeners = self.__listeners.get(event, [])
            if listener in listeners:
                listeners.remove(listener)
                key = _ListenerKey(event, id(listener))
                self.__once_listeners.discard(key)
                self.__filters.pop(key, None)

    def post(self, event: Event, data: EventData) -> None:
        with self.__lock:
            if not self.enabled:
                return

            record = EventRecord(
                event=event,
                data=data,
                channel=self._extract_channel(event),
            )
            self.__history.append(record)
            if len(self.__history) > self.__history_limit:
                self.__history = self.__history[-self.__history_limit:]

            listeners = list(self.__listeners.get(event, []))
            once_keys = set(self.__once_listeners)
            filters = dict(self.__filters)
            wildcards = list(self.__wildcard_listeners)

        to_remove: list[tuple[Event, Listener]] = []

        if self.debug:
            print(f"Event {event} posting to {len(listeners)} listeners")

        for cb in listeners:
            key = _ListenerKey(event, id(cb))
            filter_fn = filters.get(key)
            if filter_fn and not filter_fn(data):
                continue

            try:
                if asyncio.iscoroutinefunction(cb):
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(cb(data))
                    except RuntimeError:
                        asyncio.run(cb(data))
                else:
                    cb(data)
                if self.debug:
                    print(f"Event {event} delivered to {cb}")
            except KeyError as e:
                logger.error(
                    "KeyError in event '%s' listener=%r missing_key=%s payload_keys=%s",
                    event,
                    cb,
                    e.args[0],
                    list(data.keys()) if data else None,
                )
                logger.debug("Payload: %r", data, exc_info=True)
            except Exception:
                logger.exception(
                    "Unhandled error in event '%s' listener=%r payload=%r",
                    event,
                    cb,
                    data,
                )

            if key in once_keys:
                to_remove.append((event, cb))

        for pattern, cb in wildcards:
            if fnmatch(event, pattern):
                try:
                    if asyncio.iscoroutinefunction(cb):
                        try:
                            loop = asyncio.get_running_loop()
                            loop.create_task(cb(event, data))
                        except RuntimeError:
                            asyncio.run(cb(event, data))
                    else:
                        cb(event, data)
                except Exception:
                    logger.exception(
                        "Unhandled error in wildcard listener pattern=%r event=%r",
                        pattern,
                        event,
                    )

        if to_remove:
            with self.__lock:
                for ev, cb in to_remove:
                    key = _ListenerKey(ev, id(cb))
                    listeners_list = self.__listeners.get(ev, [])
                    if cb in listeners_list:
                        listeners_list.remove(cb)
                    self.__once_listeners.discard(key)
                    self.__filters.pop(key, None)

    def replay(
        self,
        event: Event,
        listener: Listener,
        limit: int | None = None,
    ) -> int:
        with self.__lock:
            matching = [r for r in self.__history if r.event == event]
            if limit:
                matching = matching[-limit:]
            records = list(matching)

        for record in records:
            try:
                listener(record.data)
            except Exception:
                logger.exception(
                    "Error during replay event=%r listener=%r",
                    event,
                    listener,
                )
        return len(records)

    def replay_channel(
        self,
        channel_name: str,
        listener: Listener,
        limit: int | None = None,
    ) -> int:
        with self.__lock:
            matching = [r for r in self.__history if r.channel == channel_name]
            if limit:
                matching = matching[-limit:]
            records = list(matching)

        for record in records:
            try:
                listener(record.data)
            except Exception:
                logger.exception(
                    "Error during channel replay channel=%r listener=%r",
                    channel_name,
                    listener,
                )
        return len(records)

    def history(
        self,
        event: Event | None = None,
        channel: str | None = None,
        limit: int | None = None,
    ) -> list[EventRecord]:
        with self.__lock:
            records = list(self.__history)
        if event:
            records = [r for r in records if r.event == event]
        if channel:
            records = [r for r in records if r.channel == channel]
        if limit:
            records = records[-limit:]
        return records

    def clear_history(self) -> None:
        with self.__lock:
            self.__history.clear()

    def events(self) -> list[Event]:
        with self.__lock:
            return list(self.__listeners.keys())

    def channels(self) -> list[str]:
        with self.__lock:
            return list(self.__channels.keys())

    def listener_count(self, event: Event) -> int:
        with self.__lock:
            return len(self.__listeners.get(event, []))

    def reset(self) -> None:
        with self.__lock:
            self.__listeners.clear()
            self.__once_listeners.clear()
            self.__wildcard_listeners.clear()
            self.__history.clear()
            self.__channels.clear()
            self.__filters.clear()

    def _extract_channel(self, event: Event) -> str | None:
        if CHANNEL_SEP in event:
            return event.split(CHANNEL_SEP, 1)[0]
        return None
