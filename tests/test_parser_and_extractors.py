"""Comprehensive synthetic test suite covering all 8 research test scenarios and deterministic reproducibility."""

import os
import shutil
import tempfile
import unittest

from projectgenome.main import analyze_repository
from projectgenome.models.entities import EntityType
from projectgenome.models.relationships import RelationshipType


class TestSyntheticScenarios(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _write_file(self, rel_path: str, content: str):
        full_path = os.path.join(self.test_dir, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

    def test_scenario_1_classes_and_functions(self):
        """Test 1: Simple classes, top-level functions, and line locations."""
        self._write_file("main.py", "class User:\n    pass\n\ndef login():\n    pass\n")
        output = analyze_repository(self.test_dir)

        entities_by_id = {e.id: e for e in output.entities}
        self.assertIn("class:main.py:User", entities_by_id)
        self.assertIn("func:main.py:login", entities_by_id)

        user_cls = entities_by_id["class:main.py:User"]
        self.assertEqual(user_cls.location.start_line, 1)

    def test_scenario_2_inheritance(self):
        """Test 2: Class inheritance (local and raw base names)."""
        self._write_file(
            "models.py",
            "class Base:\n    pass\n\nclass User(Base):\n    pass\n"
        )
        output = analyze_repository(self.test_dir)

        inherits_rels = [r for r in output.relationships if r.type == RelationshipType.INHERITS]
        self.assertEqual(len(inherits_rels), 1)
        rel = inherits_rels[0]
        self.assertEqual(rel.source, "class:models.py:User")
        self.assertEqual(rel.target, "class:models.py:Base")

    def test_scenario_3_and_8_calls_and_unresolved(self):
        """Test 3 & 8: Intra-file calls and non-hallucinating unresolved dynamic calls."""
        self._write_file(
            "app.py",
            "def authenticate():\n    pass\n\ndef login(user):\n    authenticate()\n    user.save()\n"
        )
        output = analyze_repository(self.test_dir)

        call_rels = {r.target: r for r in output.relationships if r.type == RelationshipType.CALLS}
        # authenticate() resolved
        self.assertIn("func:app.py:authenticate", call_rels)
        self.assertTrue(call_rels["func:app.py:authenticate"].properties["resolved"])

        # user.save() unresolved
        self.assertIn("unresolved:user.save", call_rels)
        self.assertFalse(call_rels["unresolved:user.save"].properties["resolved"])
        self.assertEqual(call_rels["unresolved:user.save"].properties["confidence"], "syntactic_only")

    def test_scenario_4_and_5_imports_and_cross_file_calls(self):
        """Test 4 & 5: Imports and cross-file symbol resolution."""
        self._write_file("auth.py", "def verify_token():\n    return True\n")
        self._write_file(
            "service.py",
            "from auth import verify_token\n\ndef check_access():\n    verify_token()\n"
        )
        output = analyze_repository(self.test_dir)

        # Cross file call resolution
        call_rels = [r for r in output.relationships if r.type == RelationshipType.CALLS]
        check_rel = [r for r in call_rels if r.source == "func:service.py:check_access"][0]
        self.assertEqual(check_rel.target, "func:auth.py:verify_token")
        self.assertTrue(check_rel.properties["resolved"])

    def test_scenario_6_duplicate_names_id_isolation(self):
        """Test 6: Duplicate function names in different files must have distinct IDs."""
        self._write_file("module_a.py", "def process():\n    pass\n")
        self._write_file("module_b.py", "def process():\n    pass\n")
        output = analyze_repository(self.test_dir)

        func_ids = {e.id for e in output.entities if e.type == EntityType.FUNCTION}
        self.assertIn("func:module_a.py:process", func_ids)
        self.assertIn("func:module_b.py:process", func_ids)
        self.assertNotEqual("func:module_a.py:process", "func:module_b.py:process")

    def test_scenario_7_nested_function_lexical_scoping(self):
        """Test 7: Nested functions must use qualified lexical scope in IDs."""
        self._write_file(
            "nested.py",
            "def outer():\n    def helper():\n        pass\n\ndef another():\n    def helper():\n        pass\n"
        )
        output = analyze_repository(self.test_dir)

        func_ids = {e.id for e in output.entities if e.type == EntityType.FUNCTION}
        self.assertIn("func:nested.py:outer", func_ids)
        self.assertIn("func:nested.py:outer.helper", func_ids)
        self.assertIn("func:nested.py:another.helper", func_ids)

    def test_scenario_9_deterministic_reproducibility(self):
        """Test 9: Re-analyzing the repository produces 100% identical canonical SHA-256 hashes."""
        self._write_file("a.py", "class A:\n    def foo(self):\n        pass\n")
        self._write_file("b.py", "from a import A\ndef bar():\n    a = A()\n    a.foo()\n")

        run1 = analyze_repository(self.test_dir)
        run2 = analyze_repository(self.test_dir)

        hash1 = run1.compute_canonical_hash()
        hash2 = run2.compute_canonical_hash()

        self.assertEqual(hash1, hash2)


if __name__ == "__main__":
    unittest.main()
