import asyncio
import unittest

from qwenapi.agent import AgentRunner
from qwenapi.search import SearchCache, SearchResult


class FakeBackend:
    def __init__(self):
        self.calls = 0

    async def complete(self, messages, tools=None):
        self.calls += 1
        if tools and self.calls == 1:
            return {"message": {"tool_calls": [{"function": {"name": "web_search", "arguments": {"query": "Qwen3.5 release"}}}]}}
        return {"message": {"content": "Answer with evidence."}}


class FakeSearch:
    def __init__(self):
        self.calls = 0

    async def search(self, query, *, category, depth="basic", limit=5):
        self.calls += 1
        return [SearchResult("Qwen source", "https://example.com/qwen", "snippet", "S1", 1.0)]


class AgentTests(unittest.TestCase):
    def test_tool_turn_then_final_answer(self):
        backend, search = FakeBackend(), FakeSearch()
        result = asyncio.run(AgentRunner(backend, search, cache=SearchCache()).run([{"role": "user", "content": "Explain Qwen3.5"}]))
        self.assertEqual(result.content, "Answer with evidence.")
        self.assertEqual(result.search_calls, 1)
        self.assertEqual(search.calls, 1)
        self.assertFalse(result.safeguard_triggered)


if __name__ == "__main__":
    unittest.main()
