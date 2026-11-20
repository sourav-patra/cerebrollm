"""Synthetic search hits and a stand-in for search.run_search. No configuration is read and no service
is probed, so a test module can import these at collection time on any host."""
from unittest import mock


def hit(rank, text="chunk text", path="alpha/review.md", **kw):
    h = {"rank": rank, "score": 0.5, "tier": "T1", "status": "locked", "project": "example", "path": path,
         "ref": "file", "title": "Review", "line_start": 1, "line_end": 3, "source_unchanged": True,
         "heading_path": "Review", "sha256": "ab" * 32, "also_at": [], "mtime": None, "text": text}
    h.update(kw)
    return h


class FakeSearch:
    """Stands in for search.run_search: returns the first k of its hits, best first."""

    def __init__(self, hits, error=None):
        self.hits, self.error, self.calls = hits, error, []

    def __call__(self, cfg, query, k=None, mode=None, all_status=False, project=None, synonyms=None):
        self.calls.append({"k": k, "mode": mode, "all_status": all_status, "project": project})
        if self.error:
            raise self.error
        return [dict(h) for h in self.hits[:k]]


class DepthSensitiveSearch(FakeSearch):
    """Like run_search, the order depends on the depth asked for: from `deeper_than` on, the hit
    `promoted` jumps to rank 1, as rank fusion of two arms fetched deeper can do."""

    def __init__(self, hits, promoted, deeper_than):
        super().__init__(hits)
        self.promoted, self.deeper_than = promoted, deeper_than

    def __call__(self, cfg, query, k=None, mode=None, all_status=False, project=None, synonyms=None):
        self.calls.append({"k": k, "mode": mode, "all_status": all_status, "project": project})
        order = list(self.hits)
        if k > self.deeper_than:
            order.insert(0, order.pop(self.promoted))
        return [dict(h, rank=i + 1) for i, h in enumerate(order[:k])]


def patched_search(fake):
    return mock.patch("cerebrollm.search.run_search", fake)
