"""Unit tests for projectgenome models."""

import unittest
from projectgenome.models import (
    Entity,
    EntityType,
    Relationship,
    RelationshipType,
    RepositoryAnalysisOutput,
    SourceLocation,
)


class TestModels(unittest.TestCase):
    def test_entity_serialization(self):
        loc = SourceLocation(file="src/a.py", start_line=10, end_line=20, start_column=0, end_column=15)
        entity = Entity(
            id="class:src/a.py:Foo",
            type=EntityType.CLASS,
            name="Foo",
            path="src/a.py",
            location=loc,
            properties={"bases": ["Bar"]},
        )
        data = entity.to_dict()
        self.assertEqual(data["id"], "class:src/a.py:Foo")
        self.assertEqual(data["type"], "Class")
        self.assertEqual(data["location"]["start_line"], 10)

    def test_canonical_hash_reproducibility(self):
        e1 = Entity(id="file:a.py", type=EntityType.FILE, name="a.py", path="a.py")
        e2 = Entity(id="dir:src", type=EntityType.DIRECTORY, name="src", path="src")

        r1 = Relationship(
            id="rel:contains:dir:src->file:a.py",
            source="dir:src",
            type=RelationshipType.CONTAINS,
            target="file:a.py",
        )

        out1 = RepositoryAnalysisOutput(
            repository_identity="repo:test",
            root_path="/path/test",
            extracted_at="2026-09-26T12:00:00Z",
            entities=[e1, e2],
            relationships=[r1],
        )

        out2 = RepositoryAnalysisOutput(
            repository_identity="repo:test",
            root_path="/path/test",
            extracted_at="2026-09-26T15:30:00Z",  # Different timestamp
            entities=[e2, e1],  # Swapped order
            relationships=[r1],
        )

        # Canonical hashes MUST match 100% despite timestamp differences & input array ordering!
        self.assertEqual(out1.compute_canonical_hash(), out2.compute_canonical_hash())


if __name__ == "__main__":
    unittest.main()
