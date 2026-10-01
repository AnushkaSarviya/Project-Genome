"""Unit tests for RepositoryScanner."""

import os
import shutil
import tempfile
import unittest

from projectgenome.scanner import RepositoryScanner, derive_module_name


class TestRepositoryScanner(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.test_dir, "services"))
        
        with open(os.path.join(self.test_dir, "main.py"), "w") as f:
            f.write("print('hello')\n")
            
        with open(os.path.join(self.test_dir, "services", "user_service.py"), "w") as f:
            f.write("class UserService:\n    pass\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_module_name_derivation(self):
        self.assertEqual(derive_module_name("services/user_service.py"), "services.user_service")
        self.assertEqual(derive_module_name("services/__init__.py"), "services")

    def test_scan(self):
        scanner = RepositoryScanner(self.test_dir)
        entities, relationships = scanner.scan()

        entity_ids = {e.id for e in entities}
        self.assertIn(f"repo:{os.path.basename(self.test_dir)}", entity_ids)
        self.assertIn("dir:services", entity_ids)
        self.assertIn("file:main.py", entity_ids)
        self.assertIn("file:services/user_service.py", entity_ids)

        rel_ids = {r.id for r in relationships}
        self.assertIn(f"rel:contains:repo:{os.path.basename(self.test_dir)}->dir:services", rel_ids)
        self.assertIn("rel:contains:dir:services->file:services/user_service.py", rel_ids)


if __name__ == "__main__":
    unittest.main()
