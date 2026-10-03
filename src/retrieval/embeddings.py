"""CodeBERT Embedding Engine for ProjectGenome.

Generates dense 768-dimensional vector embeddings for code chunks and natural language queries
using microsoft/codebert-base.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from .chunker import CodeChunk


class CodeBERTEmbedder:
    """Encoder for generating dense vector embeddings using CodeBERT."""

    def __init__(
        self,
        model_name: str = "microsoft/codebert-base",
        device: str | None = None,
        max_length: int = 512,
    ) -> None:
        """Initialize CodeBERTEmbedder.

        Args:
            model_name: Hugging Face model identifier (default: microsoft/codebert-base).
            device: Computing device ('cpu', 'cuda', etc.). If None, autodetects.
            max_length: Maximum token sequence length for truncation/padding.
        """
        self.model_name = model_name
        self.max_length = max_length
        self._device_override = device

        # Lazy-loaded attributes
        self._tokenizer = None
        self._model = None
        self._device = None

    def _load_model(self) -> None:
        """Lazy load tokenizer and model."""
        if self._model is not None:
            return

        import torch
        from transformers import AutoModel, AutoTokenizer

        if self._device_override:
            self._device = torch.device(self._device_override)
        else:
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModel.from_pretrained(self.model_name)
        self._model.to(self._device)
        self._model.eval()

    def embed_texts(self, texts: list[str], batch_size: int = 16) -> np.ndarray:
        """Generate normalized vector embeddings for a list of text strings.

        Args:
            texts: List of input strings.
            batch_size: Processing batch size.

        Returns:
            2D numpy array of shape (N, 768) with unit L2-normalized embeddings.
        """
        if not texts:
            return np.empty((0, 768), dtype=np.float32)

        self._load_model()
        import torch

        all_embeddings: list[np.ndarray] = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            encoded = self._tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            )
            input_ids = encoded["input_ids"].to(self._device)
            attention_mask = encoded["attention_mask"].to(self._device)

            with torch.no_grad():
                outputs = self._model(input_ids=input_ids, attention_mask=attention_mask)
                # Mean pooling over non-padded token representations
                token_embeddings = outputs.last_hidden_state  # (B, L, H)
                input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
                sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, dim=1)
                sum_mask = torch.clamp(input_mask_expanded.sum(dim=1), min=1e-9)
                mean_pooled = sum_embeddings / sum_mask

                # L2 normalize
                normalized = torch.nn.functional.normalize(mean_pooled, p=2, dim=1)
                all_embeddings.append(normalized.cpu().numpy())

        return np.vstack(all_embeddings).astype(np.float32)

    def embed_text(self, text: str) -> np.ndarray:
        """Generate vector embedding for a single text query."""
        embeddings = self.embed_texts([text], batch_size=1)
        return embeddings[0]

    def embed_chunks(self, chunks: list[CodeChunk], batch_size: int = 16) -> np.ndarray:
        """Generate vector embeddings for a list of CodeChunk objects."""
        texts = [chunk.text_representation for chunk in chunks]
        return self.embed_texts(texts, batch_size=batch_size)
