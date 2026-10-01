"""Entity Extractor module for converting parsed AST structures into canonical IR Entity objects and structural CONTAINS edges."""

from typing import List, Tuple

from projectgenome.models.entities import Entity, EntityType, SourceLocation
from projectgenome.models.relationships import Relationship, RelationshipType
from projectgenome.parsers.python_parser import ParsedClass, ParsedFileAST, ParsedFunction


class EntityExtractor:
    """Transforms ParsedFileAST into canonical Entity objects and top-down CONTAINS edges."""

    def __init__(self, rel_file_path: str, parsed_ast: ParsedFileAST):
        self.rel_file_path = rel_file_path
        self.parsed_ast = parsed_ast
        self.file_id = f"file:{self.rel_file_path}"

    def extract(self) -> Tuple[List[Entity], List[Relationship]]:
        entities: List[Entity] = []
        relationships: List[Relationship] = []

        # 1. Process top-level and nested classes
        for parsed_class in self.parsed_ast.classes:
            class_entity, class_contains = self._extract_class(parsed_class)
            entities.append(class_entity)
            relationships.extend(class_contains)

        # 2. Process top-level standalone functions
        for parsed_func in self.parsed_ast.functions:
            func_entity, func_contains = self._extract_function(parsed_func)
            entities.append(func_entity)
            relationships.extend(func_contains)

        return entities, relationships

    def _extract_class(self, parsed_class: ParsedClass) -> Tuple[Entity, List[Relationship]]:
        class_id = f"class:{self.rel_file_path}:{parsed_class.qualified_name}"
        location = SourceLocation(
            file=self.rel_file_path,
            start_line=parsed_class.start_line,
            end_line=parsed_class.end_line,
            start_column=parsed_class.start_column,
            end_column=parsed_class.end_column,
        )

        class_entity = Entity(
            id=class_id,
            type=EntityType.CLASS,
            name=parsed_class.name,
            path=self.rel_file_path,
            location=location,
            properties={
                "qualified_name": parsed_class.qualified_name,
                "docstring": parsed_class.docstring,
                "decorators": parsed_class.decorators,
                "bases": [b.raw_name for b in parsed_class.bases],
            },
        )

        relationships: List[Relationship] = []
        
        # File CONTAINS Class
        rel_id = f"rel:contains:{self.file_id}->{class_id}"
        relationships.append(
            Relationship(
                id=rel_id,
                source=self.file_id,
                type=RelationshipType.CONTAINS,
                target=class_id,
                properties={"confidence": "certain"},
            )
        )

        # Class CONTAINS Methods
        for method in parsed_class.methods:
            method_entity, method_rel = self._extract_method(class_id, method)
            # Add method entity directly to return list? We will yield entities and relationships
            # We add method to internal list via helper
            self._extra_entities.append(method_entity)
            relationships.append(method_rel)

        return class_entity, relationships

    def _extract_method(self, parent_class_id: str, method: ParsedFunction) -> Tuple[Entity, Relationship]:
        method_id = f"method:{self.rel_file_path}:{method.qualified_name}"
        location = SourceLocation(
            file=self.rel_file_path,
            start_line=method.start_line,
            end_line=method.end_line,
            start_column=method.start_column,
            end_column=method.end_column,
        )

        method_entity = Entity(
            id=method_id,
            type=EntityType.METHOD,
            name=method.name,
            path=self.rel_file_path,
            location=location,
            properties={
                "qualified_name": method.qualified_name,
                "docstring": method.docstring,
                "decorators": method.decorators,
                "is_async": method.is_async,
                "parameters": method.parameters,
                "return_type": method.return_type,
            },
        )

        rel_id = f"rel:contains:{parent_class_id}->{method_id}"
        contains_rel = Relationship(
            id=rel_id,
            source=parent_class_id,
            type=RelationshipType.CONTAINS,
            target=method_id,
            properties={"confidence": "certain"},
        )

        return method_entity, contains_rel

    def _extract_function(self, func: ParsedFunction) -> Tuple[Entity, List[Relationship]]:
        func_id = f"func:{self.rel_file_path}:{func.qualified_name}"
        location = SourceLocation(
            file=self.rel_file_path,
            start_line=func.start_line,
            end_line=func.end_line,
            start_column=func.start_column,
            end_column=func.end_column,
        )

        func_entity = Entity(
            id=func_id,
            type=EntityType.FUNCTION,
            name=func.name,
            path=self.rel_file_path,
            location=location,
            properties={
                "qualified_name": func.qualified_name,
                "docstring": func.docstring,
                "decorators": func.decorators,
                "is_async": func.is_async,
                "parameters": func.parameters,
                "return_type": func.return_type,
            },
        )

        relationships: List[Relationship] = []

        # Determine parent for containment (File or outer Function)
        if func.scope_path:
            # Nested function inside another function!
            parent_qual = ".".join(func.scope_path)
            parent_id = f"func:{self.rel_file_path}:{parent_qual}"
        else:
            parent_id = self.file_id

        rel_id = f"rel:contains:{parent_id}->{func_id}"
        relationships.append(
            Relationship(
                id=rel_id,
                source=parent_id,
                type=RelationshipType.CONTAINS,
                target=func_id,
                properties={"confidence": "certain"},
            )
        )

        return func_entity, relationships

    def extract_all(self) -> Tuple[List[Entity], List[Relationship]]:
        """Extracts all entities and containment edges from the parsed AST."""
        self._extra_entities: List[Entity] = []
        entities, relationships = self.extract()
        all_entities = entities + self._extra_entities
        return all_entities, relationships
