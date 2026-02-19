import unittest
from xevents import xEvents


class TestReset(unittest.TestCase):
    def test_reset_clears_everything(self):
        bus = xEvents()
        bus.subscribe("a", lambda d: None)
        bus.channel("ch")
        bus.post("a", {"v": 1})
        bus.on_any("*", lambda e, d: None)
        bus.reset()
        self.assertEqual(bus.events(), [])
        self.assertEqual(bus.channels(), [])
        self.assertEqual(bus.history(), [])


class TestListenerCount(unittest.TestCase):
    def test_count(self):
        bus = xEvents()
        bus.subscribe("a", lambda d: None)
        bus.subscribe("a", lambda d: None)
        self.assertEqual(bus.listener_count("a"), 2)
        self.assertEqual(bus.listener_count("nonexistent"), 0)


class TestErrorHandling(unittest.TestCase):
    def test_listener_error_does_not_break_others(self):
        bus = xEvents()
        results = []

        def bad_listener(d):
            raise RuntimeError("boom")

        def good_listener(d):
            results.append(d)

        bus.subscribe("test", bad_listener)
        bus.subscribe("test", good_listener)
        bus.post("test", {"a": 1})
        self.assertEqual(len(results), 1)


class TestReentrancy(unittest.TestCase):
    def test_listener_can_post_events(self):
        bus = xEvents()
        results = []

        def on_a(d):
            results.append(("a", d))
            if d.get("trigger_b"):
                bus.post("b", {"from": "a"})

        def on_b(d):
            results.append(("b", d))

        bus.subscribe("a", on_a)
        bus.subscribe("b", on_b)
        bus.post("a", {"trigger_b": True})
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][0], "a")
        self.assertEqual(results[1][0], "b")


if __name__ == "__main__":
    unittest.main()
