import asyncio
import unittest
from xevents import xEvents


class TestAsyncListeners(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bus = xEvents()
        self.received = []

    async def test_async_listener(self):
        async def handler(d):
            self.received.append(d)

        self.bus.subscribe("test", handler)
        self.bus.post("test", {"v": 1})
        await asyncio.sleep(0.05)
        self.assertEqual(len(self.received), 1)
        self.assertEqual(self.received[0]["v"], 1)

    async def test_async_wildcard_listener(self):
        async def handler(ev, d):
            self.received.append((ev, d))

        self.bus.on_any("data:*", handler)
        self.bus.post("data:update", {"v": 2})
        await asyncio.sleep(0.05)
        self.assertEqual(len(self.received), 1)
        self.assertEqual(self.received[0][0], "data:update")


if __name__ == "__main__":
    unittest.main()
