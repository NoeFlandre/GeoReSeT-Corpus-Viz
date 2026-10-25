import numpy as np
import pytest

from georeset_viz.embedder import Embedder, l2_normalize, mean_pool


def test_mean_pool_ignores_padding():
    hidden = np.array([[[1.0, 2.0], [3.0, 4.0], [100.0, 100.0]]])
    mask = np.array([[1, 1, 0]])
    np.testing.assert_allclose(mean_pool(hidden, mask), [[2.0, 3.0]])


def test_l2_normalize_gives_unit_rows():
    out = l2_normalize(np.array([[3.0, 4.0], [0.0, 2.0]]))
    np.testing.assert_allclose(out, [[0.6, 0.8], [0.0, 1.0]])


@pytest.fixture(scope="module")
def embedder() -> Embedder:
    return Embedder.from_hub()


@pytest.mark.network
def test_query_ranks_related_passage_first(embedder):
    passages = embedder.encode(
        ["Une tourbière drainée au bord du lac.", "Le menu du restaurant change chaque jour."],
        "passage",
    )
    scores = passages @ embedder.query("zone humide")
    assert passages.shape == (2, 384)
    assert scores[0] > scores[1]


@pytest.mark.network
def test_batching_barely_changes_vectors(embedder):
    texts = ["forêt de sapins", "vignoble en terrasses sur les coteaux", "glacier"]
    cosine = (
        embedder.encode(texts, "passage", batch_size=2) * embedder.encode(texts, "passage")
    ).sum(1)
    assert cosine.min() > 0.99


@pytest.mark.network
def test_encode_keeps_input_order(embedder):
    texts = ["Un très long paragraphe sur les prairies humides de montagne et leurs usages.", "lac"]
    together = embedder.encode(texts, "passage", batch_size=1)
    alone = np.vstack([embedder.encode([t], "passage") for t in texts])
    assert (together * alone).sum(1).min() > 0.999
