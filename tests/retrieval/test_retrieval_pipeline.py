"""Deterministic unit and integration tests for Phase 5 retrieval pipeline.

Verifies:
1. Structural validity of chunking (every analyzer entity -> valid CodeChunk, metadata preserved).
2. CodeBERT embedding properties (768-dim, finite, unit-normalized).
3. Vector index mechanics (exact cosine ranking, top-k bounds, filtering, persistence, determinism).
4. End-to-end pipeline smoke test without brittle heuristics.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import numpy as np

from src.retrieval.chunker import CodeChunk, CodeEntityChunker
from src.retrieval.embeddings import CodeBERTEmbedder
from src.retrieval.index import CodeVectorIndex


class TestChunkerStructuralValidation(unittest.TestCase):
    """Deterministic structural validation for CodeEntityChunker."""

    def setUp(self):
        self.sample_analysis_path = Path("sample_analysis.json")
        self.sample_repo_path = Path("sample_repo")
        self.chunker = CodeEntityChunker(repo_path=self.sample_repo_path)

    def test_all_code_entities_become_valid_chunks(self):
        """Every file, class, function, and method in analyzer JSON produces a valid CodeChunk."""
        with open(self.sample_analysis_path, encoding="utf-8") as f:
            data = json.load(f)

        code_entity_ids = {
            e["id"]
            for e in data.get("entities", [])
            if str(e.get("type", "")).lower() in ("file", "class", "function", "method")
        }

        chunks = self.chunker.chunk_analysis_file(self.sample_analysis_path)
        chunk_entity_ids = {c.entity_id for c in chunks}

        # Verify all code entities from analysis are present in chunks
        self.assertEqual(code_entity_ids, chunk_entity_ids)
        self.assertGreater(len(chunks), 0)

    def test_chunk_metadata_and_text_representation(self):
        """Verify chunk metadata preservation and text representation completeness."""
        chunks = self.chunker.chunk_analysis_file(self.sample_analysis_path)

        for chunk in chunks:
            self.assertIsInstance(chunk, CodeChunk)
            self.assertTrue(chunk.entity_id)
            self.assertIn(chunk.entity_type, ("file", "class", "function", "method"))
            self.assertTrue(chunk.name)
            self.assertTrue(chunk.qualified_name)
            self.assertTrue(chunk.file_path)

            # Text representation must be non-empty and contain core entity headers
            self.assertTrue(len(chunk.text_representation.strip()) > 0)
            self.assertIn(f"Entity Type: {chunk.entity_type.capitalize()}", chunk.text_representation)
            self.assertIn(f"Name: {chunk.name}", chunk.text_representation)
            self.assertIn(f"File: {chunk.file_path}", chunk.text_representation)

            # If source code exists, it must appear in text representation
            if chunk.source_code:
                self.assertIn(chunk.source_code.strip(), chunk.text_representation)


class TestVectorIndexDeterminismAndRanking(unittest.TestCase):
    """Deterministic unit tests for CodeVectorIndex ranking and persistence."""

    def setUp(self):
        self.chunk_a = CodeChunk(
            repository_id="repo",
            entity_id="func:a.py:fn_a",
            entity_type="function",
            name="fn_a",
            qualified_name="fn_a",
            file_path="a.py",
            text_representation="Function fn_a",
        )
        self.chunk_b = CodeChunk(
            repository_id="repo",
            entity_id="class:b.py:ClassB",
            entity_type="class",
            name="ClassB",
            qualified_name="ClassB",
            file_path="b.py",
            text_representation="Class ClassB",
        )
        self.chunk_c = CodeChunk(
            repository_id="repo",
            entity_id="method:c.py:ClassC.method_c",
            entity_type="method",
            name="method_c",
            qualified_name="ClassC.method_c",
            file_path="c.py",
            text_representation="Method method_c",
        )

    def test_index_insertion_and_length(self):
        index = CodeVectorIndex()
        self.assertEqual(len(index), 0)

        vecs = np.eye(3, dtype=np.float32)
        index.add_chunks([self.chunk_a, self.chunk_b, self.chunk_c], vecs)
        self.assertEqual(len(index), 3)

    def test_cosine_similarity_ranking(self):
        """Verify mathematical correctness of cosine similarity ranking."""
        index = CodeVectorIndex()

        # Construct orthogonal basis vectors
        # e0 corresponds to chunk_a (similarity with e0 = 1.0)
        # e1 corresponds to chunk_b (similarity with e0 = 0.0)
        # 0.6 * e0 + 0.8 * e1 corresponds to chunk_c (similarity with e0 = 0.6)
        vec_a = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec_b = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        vec_c = np.array([0.6, 0.8, 0.0], dtype=np.float32)

        index.add_chunks([self.chunk_a, self.chunk_b, self.chunk_c], np.vstack([vec_a, vec_b, vec_c]))

        # Query along vec_a
        query = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        results = index.search(query, top_k=3)

        self.assertEqual(len(results), 3)
        self.assertEqual(results[0][0].entity_id, self.chunk_a.entity_id)
        self.assertAlmostEqual(results[0][1], 1.0, places=5)

        self.assertEqual(results[1][0].entity_id, self.chunk_c.entity_id)
        self.assertAlmostEqual(results[1][1], 0.6, places=5)

        self.assertEqual(results[2][0].entity_id, self.chunk_b.entity_id)
        self.assertAlmostEqual(results[2][1], 0.0, places=5)

    def test_top_k_bounds(self):
        index = CodeVectorIndex()
        vecs = np.eye(3, dtype=np.float32)
        index.add_chunks([self.chunk_a, self.chunk_b, self.chunk_c], vecs)

        results_1 = index.search(vecs[0], top_k=1)
        self.assertEqual(len(results_1), 1)

        results_10 = index.search(vecs[0], top_k=10)
        self.assertEqual(len(results_10), 3)

    def test_entity_type_filtering(self):
        index = CodeVectorIndex()
        vecs = np.eye(3, dtype=np.float32)
        index.add_chunks([self.chunk_a, self.chunk_b, self.chunk_c], vecs)

        results = index.search(vecs[0], top_k=5, entity_type_filter="class")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0].entity_id, self.chunk_b.entity_id)

    def test_persistence_and_reload(self):
        index = CodeVectorIndex()
        vecs = np.eye(3, dtype=np.float32)
        index.add_chunks([self.chunk_a, self.chunk_b, self.chunk_c], vecs)

        with tempfile.TemporaryDirectory() as tmp_dir:
            index.save(tmp_dir)
            loaded_index = CodeVectorIndex.load(tmp_dir)

            self.assertEqual(len(loaded_index), 3)
            query = vecs[0]
            orig_res = index.search(query, top_k=3)
            loaded_res = loaded_index.search(query, top_k=3)

            for (c1, s1), (c2, s2) in zip(orig_res, loaded_res):
                self.assertEqual(c1.entity_id, c2.entity_id)
                self.assertAlmostEqual(s1, s2, places=6)

    def test_query_determinism(self):
        index = CodeVectorIndex()
        vecs = np.eye(3, dtype=np.float32)
        index.add_chunks([self.chunk_a, self.chunk_b, self.chunk_c], vecs)

        query = np.array([0.5, 0.5, 0.0], dtype=np.float32)
        res1 = index.search(query, top_k=3)
        res2 = index.search(query, top_k=3)

        self.assertEqual([(c.entity_id, s) for c, s in res1], [(c.entity_id, s) for c, s in res2])


class TestCodeBERTEndToEndPipeline(unittest.TestCase):
    """Integration verification of CodeBERT embedding and end-to-end retrieval pipeline."""

    @classmethod
    def setUpClass(cls):
        cls.sample_analysis_path = Path("sample_analysis.json")
        cls.sample_repo_path = Path("sample_repo")
        cls.embedder = CodeBERTEmbedder()

    def test_embedding_dimensionality_finiteness_and_normalization(self):
        """CodeBERT embeddings must be (N, 768), finite, and unit L2 normalized."""
        test_texts = [
            "def add(a, b): return a + b",
            "class UserService: pass",
        ]
        embeddings = self.embedder.embed_texts(test_texts, batch_size=2)

        self.assertEqual(embeddings.shape, (2, 768))
        self.assertTrue(np.all(np.isfinite(embeddings)), "Embeddings must contain only finite numbers")

        # Verify unit L2 normalization
        norms = np.linalg.norm(embeddings, axis=1)
        self.assertTrue(np.allclose(norms, 1.0, atol=1e-5), "Embeddings must be L2 normalized to 1.0")

    def test_pipeline_smoke_test(self):
        """End-to-end pipeline execution from analysis file to indexed retrieval."""
        # 1. Chunker
        chunker = CodeEntityChunker(repo_path=self.sample_repo_path)
        chunks = chunker.chunk_analysis_file(self.sample_analysis_path)
        self.assertGreater(len(chunks), 0)

        # 2. Embedder
        embeddings = self.embedder.embed_chunks(chunks, batch_size=8)
        self.assertEqual(embeddings.shape, (len(chunks), 768))
        self.assertTrue(np.all(np.isfinite(embeddings)))

        # 3. Vector Index
        index = CodeVectorIndex()
        index.add_chunks(chunks, embeddings)
        self.assertEqual(len(index), len(chunks))

        # 4. Smoke test query
        query_text = "def get_user(self, user_id):"
        query_vec = self.embedder.embed_text(query_text)
        self.assertEqual(query_vec.shape, (768,))
        self.assertTrue(np.all(np.isfinite(query_vec)))

        results = index.search(query_vec, top_k=3)
        self.assertEqual(len(results), 3)

        for chunk, score in results:
            self.assertIsInstance(chunk, CodeChunk)
            self.assertTrue(np.isfinite(score))
            self.assertGreaterEqual(score, -1.0)
            self.assertLessEqual(score, 1.0 + 1e-5)


if __name__ == "__main__":
    unittest.main()
