"""Multilingual E5 sentence embeddings with ONNX Runtime (no torch)."""

from collections.abc import Sequence

import numpy as np
import onnxruntime as ort
from huggingface_hub import hf_hub_download
from tokenizers import Tokenizer

from georeset_viz import config


def mean_pool(hidden: np.ndarray, mask: np.ndarray) -> np.ndarray:
    weights = mask[..., None].astype(hidden.dtype)
    return (hidden * weights).sum(axis=1) / np.clip(weights.sum(axis=1), 1e-9, None)


def l2_normalize(vectors: np.ndarray) -> np.ndarray:
    return vectors / np.clip(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12, None)


class Embedder:
    def __init__(self, tokenizer: Tokenizer, session: ort.InferenceSession) -> None:
        tokenizer.enable_truncation(config.MAX_TOKENS)
        tokenizer.enable_padding()
        self._tokenizer = tokenizer
        self._session = session
        self._inputs = [i.name for i in session.get_inputs()]

    @classmethod
    def from_hub(cls) -> "Embedder":
        model = hf_hub_download(config.MODEL_REPO, config.MODEL_FILE)
        tokenizer = hf_hub_download(config.MODEL_REPO, config.TOKENIZER_FILE)
        return cls(Tokenizer.from_file(tokenizer), ort.InferenceSession(model))

    def _encode_batch(self, texts: Sequence[str]) -> np.ndarray:
        encodings = self._tokenizer.encode_batch(list(texts))
        arrays = {
            "input_ids": np.array([e.ids for e in encodings], dtype=np.int64),
            "attention_mask": np.array([e.attention_mask for e in encodings], dtype=np.int64),
            "token_type_ids": np.array([e.type_ids for e in encodings], dtype=np.int64),
        }
        hidden = np.asarray(self._session.run(None, {n: arrays[n] for n in self._inputs})[0])
        return l2_normalize(mean_pool(hidden, arrays["attention_mask"]))

    def encode(self, texts: Sequence[str], prefix: str, batch_size: int = 64) -> np.ndarray:
        """Embed texts in length-sorted batches (less padding), returned in input order."""
        order = np.argsort([len(t) for t in texts], kind="stable")
        prefixed = [f"{prefix}: {texts[i]}" for i in order]
        batches = range(0, len(prefixed), batch_size)
        vectors = np.vstack([self._encode_batch(prefixed[i : i + batch_size]) for i in batches])
        return vectors[np.argsort(order)]

    def query(self, text: str) -> np.ndarray:
        return self.encode([text], "query")[0]
