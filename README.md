# xEvents
### 1.0.0

A lightweight, thread-safe event system for Python. Use it to wire up different parts of your application so they can communicate through events — like a message bus that lives inside your process.

## Features

- **Subscribe & Post** — Register listeners for named events and fire them with data.
- **Channels** — Group related events under a namespace (e.g., `orders`, `users`) to keep things organized.
- **Once Listeners** — Listeners that automatically remove themselves after firing once.
- **Wildcard Subscriptions** — Listen to multiple events at once using patterns like `orders:*`.
- **Event Filters** — Attach a condition to a listener so it only fires when the data matches your criteria.
- **Event History & Replay** — Past events are recorded. Late subscribers can catch up by replaying history.
- **Async Support** — Async functions work as listeners alongside regular functions.
- **Thread-Safe** — All operations are protected by a reentrant lock, safe for multi-threaded apps.
- **Zero Dependencies** — Built entirely on the Python standard library.

## Requirements

- Python 3.12+

## Installation

Install the package or copy the `xevents/` directory into your project — there are no external dependencies.

```bash
pip install git+https://github.com/rkohl/xEvents.git
```

```python
from xevents import xEvents
```

## Quick Start

```python
from xevents import xEvents

# Create an event bus
bus = xEvents()

# Subscribe to an event
def on_user_login(data):
    print(f"Welcome, {data['name']}!")

bus.on("user:login", on_user_login)

# Fire the event
bus.post("user:login", {"name": "Alice"})
# Output: Welcome, Alice!
```

## API Reference

### Creating an Event Bus

```python
bus = xEvents()
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `events` | `list[str]` or `None` | `None` | Optional list of event names to pre-register. If not provided, events are created dynamically on first subscription. |
| `debug` | `bool` | `False` | When `True`, prints debug info for subscribe/post operations. |
| `history_limit` | `int` | `100` | Maximum number of events to keep in history. |

```python
# Pre-register events
bus = xEvents(events=["start", "stop", "error"])

# Enable debug logging
bus = xEvents(debug=True)

# Keep more history
bus = xEvents(history_limit=500)
```

### Subscribing to Events

#### `bus.on(event, listener)` / `bus.subscribe(event, listener)`

Register a listener that fires every time the event is posted.

```python
def handle_order(data):
    print(f"Order #{data['id']} received")

bus.on("order:created", handle_order)
```

#### `bus.once(event, listener)`

Register a listener that fires only once, then removes itself.

```python
def on_ready(data):
    print("App is ready!")

bus.once("app:ready", on_ready)

bus.post("app:ready", {})   # Prints: App is ready!
bus.post("app:ready", {})   # Nothing happens — listener was removed
```

#### `bus.on_any(pattern, listener)`

Subscribe to all events matching a wildcard pattern. The listener receives both the event name and the data.

```python
def log_all_orders(event, data):
    print(f"[{event}] {data}")

bus.on_any("orders:*", log_all_orders)

bus.post("orders:created", {"id": 1})   # Fires the listener
bus.post("orders:shipped", {"id": 1})   # Fires the listener
bus.post("users:created", {"id": 5})    # Does NOT fire — different namespace
```

Pattern examples:
- `*` — matches every event
- `orders:*` — matches `orders:created`, `orders:deleted`, etc.
- `*.error` — matches `db.error`, `api.error`, etc.

### Subscribing with Filters

Add a condition so the listener only fires when the data matches.

```python
def on_paid_order(data):
    print(f"Paid order: #{data['id']}")

bus.on("order", on_paid_order, filter_fn=lambda d: d.get("status") == "paid")

bus.post("order", {"id": 1, "status": "pending"})   # Skipped
bus.post("order", {"id": 2, "status": "paid"})       # Fires
bus.post("order", {"id": 3, "status": "refunded"})   # Skipped
```

### Unsubscribing

#### `bus.unsubscribe(event, listener)`

Remove a specific listener from an event.

```python
def handler(data):
    print(data)

bus.on("test", handler)
bus.unsubscribe("test", handler)
bus.post("test", {"msg": "hello"})  # Nothing happens
```

#### `bus.off_any(pattern, listener)`

Remove a wildcard listener.

```python
bus.on_any("*", my_logger)
bus.off_any("*", my_logger)
```

### Posting Events

#### `bus.post(event, data)`

Fire an event with a data dictionary. All matching listeners are called immediately.

```python
bus.post("user:signup", {"email": "bob@example.com", "plan": "pro"})
```

### Channels

Channels let you group related events under a namespace. Instead of manually writing `"orders:created"`, you work with a channel object that handles the prefixing for you.

```python
orders = bus.channel("orders")
users = bus.channel("users")

# These are equivalent:
orders.on("created", handler)       # Subscribes to "orders:created"
bus.on("orders:created", handler)   # Same thing

# Post through the channel
orders.post("created", {"id": 100, "total": 59.99})

# Once listener on a channel
orders.once("cancelled", handle_cancellation)

# Unsubscribe from a channel event
orders.unsubscribe("created", handler)
```

**Channel methods:** `on`, `once`, `subscribe`, `unsubscribe`, `post`

### Event History

Events are automatically recorded in a capped history (default: last 100 events).

#### `bus.history(event=None, channel=None, limit=None)`

Retrieve past event records.

```python
# Get all history
all_records = bus.history()

# Filter by event name
login_records = bus.history(event="user:login")

# Filter by channel
order_records = bus.history(channel="orders")

# Get only the last 5
recent = bus.history(limit=5)

# Combine filters
recent_orders = bus.history(channel="orders", limit=10)
```

Each record is an `EventRecord` with these fields:

| Field | Type | Description |
|---|---|---|
| `event` | `str` | The event name |
| `data` | `dict` | The data that was posted |
| `timestamp` | `float` | Unix timestamp when the event was posted |
| `channel` | `str` or `None` | The channel name, if the event used `channel:event` format |

#### `bus.clear_history()`

Remove all event history.

```python
bus.clear_history()
```

### Replay

Deliver past events to a listener that subscribed late — useful for catching up on what already happened.

#### `bus.replay(event, listener, limit=None)`

Replay past occurrences of a specific event.

```python
# Post some events
bus.post("price:update", {"symbol": "BTC", "price": 50000})
bus.post("price:update", {"symbol": "BTC", "price": 51000})
bus.post("price:update", {"symbol": "BTC", "price": 52000})

# A new listener joins late and wants to catch up
def show_price(data):
    print(f"{data['symbol']}: ${data['price']}")

count = bus.replay("price:update", show_price, limit=2)
# Prints the last 2 price updates
# Returns: 2 (number of events replayed)
```

#### `bus.replay_channel(channel_name, listener, limit=None)`

Replay all past events from a specific channel.

```python
count = bus.replay_channel("orders", process_order, limit=10)
```

### Utility Methods

#### `bus.events()`

List all event names that have listeners registered.

```python
bus.on("a", handler)
bus.on("b", handler)
print(bus.events())  # ["a", "b"]
```

#### `bus.channels()`

List all channel names that have been created.

```python
bus.channel("orders")
bus.channel("users")
print(bus.channels())  # ["orders", "users"]
```

#### `bus.listener_count(event)`

Get the number of listeners for a specific event.

```python
bus.on("test", handler_a)
bus.on("test", handler_b)
print(bus.listener_count("test"))  # 2
```

#### `bus.enabled`

Disable or enable the entire event system. When disabled, `post()` silently does nothing.

```python
bus.enabled = False
bus.post("test", {"a": 1})  # Nothing happens

bus.enabled = True
bus.post("test", {"a": 1})  # Listeners fire normally
```

#### `bus.reset()`

Clear everything — all listeners, channels, history, and filters.

```python
bus.reset()
```

### Async Listeners

Async functions work as listeners. When called from within a running event loop, they're scheduled as tasks. Otherwise, they're run to completion.

```python
import asyncio

bus = xEvents()

async def async_handler(data):
    await asyncio.sleep(0.1)
    print(f"Processed: {data}")

bus.on("task:complete", async_handler)

# Inside an async context
async def main():
    bus.post("task:complete", {"task_id": 42})
    await asyncio.sleep(0.2)  # Give the task time to complete

asyncio.run(main())
```

### Error Handling

If a listener throws an error, it's caught and logged — other listeners still get called normally.

```python
def bad_listener(data):
    raise RuntimeError("Something broke")

def good_listener(data):
    print(f"Got: {data}")

bus.on("test", bad_listener)
bus.on("test", good_listener)
bus.post("test", {"msg": "hello"})
# bad_listener error is logged
# good_listener still prints: Got: {'msg': 'hello'}
```

## Full Example: Task Queue

```python
from xevents import xEvents

bus = xEvents(debug=False)

# Set up channels
tasks = bus.channel("tasks")
notifications = bus.channel("notifications")

# Worker that processes tasks
def process_task(data):
    print(f"Processing task: {data['name']}")
    tasks.post("completed", {"name": data["name"], "result": "success"})

# Notification system
def send_notification(data):
    print(f"Notification: Task '{data['name']}' finished with result: {data['result']}")

# Logger that watches everything
def log_everything(event, data):
    print(f"  [LOG] {event} -> {data}")

# Wire it up
tasks.on("new", process_task)
tasks.on("completed", send_notification)
bus.on_any("tasks:*", log_everything)

# Submit a task
tasks.post("new", {"name": "Generate Report"})
```

Output:
```
  [LOG] tasks:new -> {'name': 'Generate Report'}
Processing task: Generate Report
  [LOG] tasks:completed -> {'name': 'Generate Report', 'result': 'success'}
Notification: Task 'Generate Report' finished with result: success
```

## Running Tests

```bash
python -m unittest discover -s tests -v
```

## License

See [LICENSE.md](LICENSE.md) for details.
