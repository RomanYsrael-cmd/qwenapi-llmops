import unittest

from qwenapi.search import SearchCache, SearchResult, canonical_url, dedupe_results


class SearchTests(unittest.TestCase):
    def test_canonical_url_removes_default_port_and_fragment(self):
        self.assertEqual(canonical_url("HTTPS://Example.COM:443/a/#part"), "https://example.com/a")

    def test_dedupe_caps_one_domain(self):
        rows = [
            SearchResult("best", "https://a.example/1", score=1.0),
            SearchResult("second", "https://a.example/2", score=0.9),
            SearchResult("third", "https://a.example/3", score=0.8),
            SearchResult("other", "https://b.example/1", score=0.7),
        ]
        output = dedupe_results(rows)
        self.assertEqual([item.title for item in output], ["best", "second", "other"])

    def test_cache_is_bounded_and_expires(self):
        now = [100.0]
        cache = SearchCache(max_entries=1, clock=lambda: now[0])
        result = [SearchResult("title", "https://example.com")]
        cache.put("one", "general", "basic", result)
        self.assertIsNotNone(cache.get("one", "general", "basic"))
        cache.put("two", "general", "basic", result)
        self.assertIsNone(cache.get("one", "general", "basic"))
        now[0] += 601
        self.assertIsNone(cache.get("two", "general", "basic"))


if __name__ == "__main__":
    unittest.main()
