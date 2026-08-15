import unittest
from src.brain import brain
from src.memory import memory

class TestBrainRouter(unittest.TestCase):

    def setUp(self):
        memory.clear_history()

    def test_browser_search_intent(self):
        reply = brain.process_query("search noise cancelling headphones")
        self.assertIn("Opening Google search results", reply)

    def test_fast_volume_intent(self):
        reply = brain.process_query("set volume to 45")
        self.assertIn("45%", reply)

    def test_relative_volume_intent(self):
        brain.process_query("set volume to 50")
        reply = brain.process_query("reduce volume")
        self.assertIn("35%", reply)
        reply_inc = brain.process_query("increase volume")
        self.assertIn("50%", reply_inc)

    def test_compound_multi_command_intent(self):
        reply = brain.process_query("open Calculator and set volume to 40")
        self.assertIn("calculator", reply.lower())
        self.assertIn("40%", reply)

    def test_memory_context_persistence(self):
        brain.process_query("Hello Jarvis!")
        history = memory.get_recent_history()
        self.assertGreaterEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")

if __name__ == "__main__":
    unittest.main()
