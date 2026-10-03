"""Unit tests for CodeEntityChunker."""

import unittest
from pathlib import Path
from src.retrieval.chunker import CodeEntityChunker, CodeChunk
from src.knowledge_graph.builder import build_from_analysis


class TestCodeEntityChunker(unittest.TestCase):
    def setUp(self):
        self.sample_analysis_path = Path("sample_analysis.json")
        self.sample_repo_path = Path("sample_repo")

    def test_chunk_analysis_file_with_sample_repo(self):
        chunker = CodeEntityChunker(repo_path=self.sample_repo_path)
        chunks = chunker.chunk_analysis_file(self.sample_analysis_path)

        self.assertGreater(len(chunks), 0)

        # Verify chunk structure
        for chunk in chunks:
            self.assertIsInstance(chunk, CodeChunk)
            self.assertIn(chunk.entity_type, ("file", "class", "function", "method"))
            self.assertTrue(chunk.entity_id)
            self.assertTrue(chunk.name)
            self.assertTrue(chunk.text_representation)

        # Check a specific method chunk
        user_service_chunks = [c for c in chunks if c.name == "UserService.get_user" or c.name == "get_user"]
        self.assertGreater(len(user_service_chunks), 0)
        user_chunk = user_service_chunks[0]
        self.assertEqual(user_chunk.file_path, "services/user_service.py")
        self.assertIn("def get_user", user_chunk.source_code)

    def test_chunk_knowledge_graph(self):
        kg = build_from_analysis(self.sample_analysis_path)
        chunker = CodeEntityChunker(repo_path=self.sample_repo_path)
        chunks = chunker.chunk_knowledge_graph(kg)

        self.assertGreater(len(chunks), 0)
        entity_types = {c.entity_type for c in chunks}
        self.assertTrue(entity_types.issubset({"file", "class", "function", "method"}))


if __name__ == "__main__":
    unittest.main()
