# Replit Agent Guide

## Overview

xEvents is a Python event system library that provides pub/sub (publish/subscribe) functionality. It allows subscribing listeners to named events, posting events with data, and organizing events into channels. The library supports features like wildcard event matching, one-time listeners, event filtering, event history recording, and both sync and async usage.

This is a library/package project (not a web application), structured as a proper Python package.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Project Structure
```
xevents/                     # Main package
├── __init__.py              # Public API exports (xEvents, Channel, EventRecord, etc.)
├── bus.py                   # xEvents class — the core event bus
├── channel.py               # Channel class — namespaced event scoping
├── models.py                # EventRecord and _ListenerKey dataclasses
├── types.py                 # Type aliases (Event, EventData, Listener, Events)
└── constants.py             # Constants (CHANNEL_SEP, WILDCARD, DEFAULT_HISTORY_LIMIT)

tests/                       # Test suite (unittest)
├── __init__.py
├── test_subscribe.py        # Subscribe, unsubscribe, on, once, disabled, duplicates
├── test_channels.py         # Channel creation, isolation, scoping
├── test_wildcards.py        # Wildcard pattern matching (on_any, off_any)
├── test_filters.py          # Filter functions on listeners
├── test_history.py          # Event history recording, filtering, capping
├── test_replay.py           # Replay events and channels
├── test_async.py            # Async listener support
└── test_misc.py             # Reset, listener count, error handling, re-entrancy

pyproject.toml               # Package metadata, tooling config (pyright, ruff)
README.md                    # Full documentation with examples
LICENSE.md                   # BSD-3-Clause license
```

### Core Components

**xEvents** (`xevents/bus.py`)
- Central event bus that manages subscriptions and event dispatching
- Uses a dictionary mapping event names to lists of listener callbacks
- Thread-safe via `RLock` — lock is released before invoking listeners
- Supports enabling/disabling the entire event system
- Maintains event history via `EventRecord` dataclass
- Supports wildcard (`*`) pattern matching for event names using `fnmatch`

**Channel** (`xevents/channel.py`)
- Provides namespaced/scoped events using a colon (`:`) separator
- Wraps the parent `xEvents` instance, prefixing event names with the channel name
- Allows logical grouping of related events

**EventRecord** (`xevents/models.py`)
- Dataclass storing event name, data, timestamp, and channel for history

**Types** (`xevents/types.py`)
- Type aliases: `Event`, `EventData`, `Listener`, `Events`

### Key Features
- `subscribe` / `on` — Register a listener for an event
- `unsubscribe` — Remove a listener
- `post` — Fire an event with data
- `once` — One-time listener support (fires once then auto-unsubscribes)
- `on_any` / `off_any` — Wildcard pattern subscriptions
- `filter_fn` — Optional filter function to conditionally invoke listeners
- `replay` / `replay_channel` — Deliver past events to late subscribers
- `history` — Query recorded event history with filtering
- Duplicate listener prevention
- Async listener support via `asyncio`

### Design Patterns
- **Observer/Pub-Sub Pattern** — Core architecture; decouples event producers from consumers
- **Decorator Pattern** — Channel wraps xEvents to add scoping behavior
- **Data Classes** — `EventRecord` and `_ListenerKey` use Python dataclasses for clean data modeling

### Language & Runtime
- Python 3.12+ (uses modern type alias syntax: `type Event = str`)
- No external dependencies — pure standard library
- Testing with `unittest`

## External Dependencies

This project has **no external dependencies**. It relies entirely on the Python standard library:
- `threading` (RLock for thread safety)
- `asyncio` (async event support)
- `logging` (debug logging)
- `dataclasses` (data modeling)
- `collections` (defaultdict)
- `fnmatch` (wildcard pattern matching)
- `unittest` (testing)

There are no databases, APIs, or third-party service integrations.

## Running Tests

```bash
python -m unittest discover -s tests -v
```

## Recent Changes
- Refactored from single-file (`src/client.py`) into proper `xevents/` package with separate modules
- Split tests from single `tests/tests.py` into feature-specific test files
- Updated pyproject.toml to point to new package structure
- Updated README.md imports and installation instructions
