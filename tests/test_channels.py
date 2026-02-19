import unittest
from xevents import xEvents


class TestChannels(unittest.TestCase):
    def setUp(self):
        self.bus = xEvents()
        self.received = []

    def test_channel_subscribe_and_post(self):
        ch = self.bus.channel("orders")
        ch.subscribe("created", lambda d: self.received.append(d))
        ch.post("created", {"order_id": 1})
        self.assertEqual(len(self.received), 1)
        self.assertEqual(self.received[0]["order_id"], 1)

    def test_channel_isolation(self):
        orders = self.bus.channel("orders")
        users = self.bus.channel("users")
        order_data = []
        user_data = []
        orders.subscribe("created", lambda d: order_data.append(d))
        users.subscribe("created", lambda d: user_data.append(d))
        orders.post("created", {"order_id": 1})
        users.post("created", {"user_id": 5})
        self.assertEqual(len(order_data), 1)
        self.assertEqual(len(user_data), 1)
        self.assertEqual(order_data[0]["order_id"], 1)
        self.assertEqual(user_data[0]["user_id"], 5)

    def test_channel_on_alias(self):
        ch = self.bus.channel("tasks")
        ch.on("done", lambda d: self.received.append(d))
        ch.post("done", {"task": "a"})
        self.assertEqual(len(self.received), 1)

    def test_channel_once(self):
        ch = self.bus.channel("tasks")
        ch.once("done", lambda d: self.received.append(d))
        ch.post("done", {"task": "a"})
        ch.post("done", {"task": "b"})
        self.assertEqual(len(self.received), 1)

    def test_channel_unsubscribe(self):
        ch = self.bus.channel("tasks")
        listener = lambda d: self.received.append(d)
        ch.subscribe("done", listener)
        ch.post("done", {"a": 1})
        ch.unsubscribe("done", listener)
        ch.post("done", {"a": 2})
        self.assertEqual(len(self.received), 1)

    def test_channels_list(self):
        self.bus.channel("a")
        self.bus.channel("b")
        names = self.bus.channels()
        self.assertIn("a", names)
        self.assertIn("b", names)


if __name__ == "__main__":
    unittest.main()
