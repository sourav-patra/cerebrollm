"""Cross-encoder rerank of search hits (BAAI/bge-reranker-v2-m3, Apache-2.0), loaded from a local folder.

The model, its pinned revision and its folder are in the [reranker] section of engine/models.toml. Nothing
is downloaded here: `scripts` in the run record show the one-time fetch. The model loads on first use, on CUDA
when it is visible, else on the CPU; `release()` frees it (the `ask` command does this before generation so
the generator has the GPU memory)."""
import os
import sys
import tomllib

from .config import data_file

MODELS_TOML = data_file("models.toml")
_model = None


def settings():
    """The single [reranker."NAME"] entry of models.toml as (name, entry)."""
    with open(MODELS_TOML, "rb") as f:
        entries = tomllib.load(f)["reranker"]
    (name, entry), = entries.items()
    return name, entry


def _load():
    global _model
    if _model is None:
        try:
            import torch
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise ImportError("the reranker needs the rerank extra: pip install 'cerebrollm[rerank]' "
                              "(or run ask with --no-rerank)") from exc
        name, entry = settings()
        folder = os.path.expanduser(entry["local_dir"])
        if not os.path.isdir(folder):
            raise FileNotFoundError("reranker %s is not downloaded: %s (steps: README, section The reranker)" % (name, folder))
        # a local folder: nothing is fetched at query time
        _model = CrossEncoder(folder, max_length=entry["max_length"],
                              device="cuda" if torch.cuda.is_available() else "cpu")
    return _model


def release():
    """Drop the model and give its GPU memory back."""
    global _model
    if _model is not None:
        _model = None
        import gc
        gc.collect()
        torch = sys.modules.get("torch")   # absent when a test replaced the model
        if torch and torch.cuda.is_available():
            torch.cuda.empty_cache()


def score(query, texts):
    """One relevance score per text (higher is better)."""
    if not texts:
        return []
    return [float(s) for s in _load().predict([(query, t) for t in texts], batch_size=8)]


def rerank(query, hits, top=8):
    """The best `top` hits by cross-encoder score, best first, ranks renumbered from 1. Each hit gets
    `rerank_score` and `search_rank` (its rank before reranking). The input list is not changed."""
    scores = score(query, [h["text"] for h in hits])
    order = sorted(range(len(hits)), key=lambda i: -scores[i])[:top]
    out = []
    for rank, i in enumerate(order, 1):
        out.append(dict(hits[i], rank=rank, search_rank=hits[i]["rank"], rerank_score=round(scores[i], 5)))
    return out
