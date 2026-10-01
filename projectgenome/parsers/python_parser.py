"""Python AST Parser module for extracting raw AST symbol definitions, calls, imports, and inheritance from Python source files."""

import ast
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ParsedImport:
    module: str
    symbol: Optional[str]
    alias: Optional[str]
    is_wildcard: bool
    line: int
    col: int


@dataclass
class ParsedBaseClass:
    raw_name: str
    line: int
    col: int


@dataclass
class ParsedCall:
    raw_call: str
    caller_scope: str
    line: int
    col: int


@dataclass
class ParsedFunction:
    name: str
    qualified_name: str
    scope_path: List[str]  # Lexical scope hierarchy (e.g. ["UserService"] or ["outer"])
    is_method: bool
    is_async: bool
    parameters: List[str]
    return_type: Optional[str]
    docstring: Optional[str]
    decorators: List[str]
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    calls: List[ParsedCall] = field(default_factory=list)


@dataclass
class ParsedClass:
    name: str
    qualified_name: str
    docstring: Optional[str]
    decorators: List[str]
    bases: List[ParsedBaseClass]
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    methods: List[ParsedFunction] = field(default_factory=list)


@dataclass
class ParsedFileAST:
    file_path: str
    imports: List[ParsedImport] = field(default_factory=list)
    classes: List[ParsedClass] = field(default_factory=list)
    functions: List[ParsedFunction] = field(default_factory=list)
    top_level_calls: List[ParsedCall] = field(default_factory=list)


class ASTSymbolVisitor(ast.NodeVisitor):
    """AST visitor that collects classes, methods, functions, calls, imports, and inheritance."""

    def __init__(self, file_path: str, source_code: str):
        self.file_path = file_path
        self.source_code = source_code
        self.lines = source_code.splitlines()

        self.imports: List[ParsedImport] = []
        self.classes: List[ParsedClass] = []
        self.functions: List[ParsedFunction] = []
        self.top_level_calls: List[ParsedCall] = []

        # Scope stack: tracks current class/function scope hierarchy
        self._scope_stack: List[str] = []
        self._current_function: Optional[ParsedFunction] = None

    def _get_qualified_name(self, symbol_name: str) -> str:
        if self._scope_stack:
            return ".".join(self._scope_stack) + "." + symbol_name
        return symbol_name

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(
                ParsedImport(
                    module=alias.name,
                    symbol=None,
                    alias=alias.asname,
                    is_wildcard=False,
                    line=node.lineno,
                    col=node.col_offset,
                )
            )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        # Handle relative imports (e.g. from .base import X)
        if node.level > 0:
            module = "." * node.level + module

        for alias in node.names:
            is_wildcard = alias.name == "*"
            self.imports.append(
                ParsedImport(
                    module=module,
                    symbol=alias.name if not is_wildcard else None,
                    alias=alias.asname,
                    is_wildcard=is_wildcard,
                    line=node.lineno,
                    col=node.col_offset,
                )
            )
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        qual_name = self._get_qualified_name(node.name)
        docstring = ast.get_docstring(node)

        # Base classes
        bases: List[ParsedBaseClass] = []
        for base in node.bases:
            raw_base = ast.unparse(base) if hasattr(ast, "unparse") else str(base)
            bases.append(
                ParsedBaseClass(
                    raw_name=raw_base,
                    line=getattr(base, "lineno", node.lineno),
                    col=getattr(base, "col_offset", node.col_offset),
                )
            )

        decorators = [ast.unparse(d) if hasattr(ast, "unparse") else str(d) for d in node.decorator_list]

        parsed_class = ParsedClass(
            name=node.name,
            qualified_name=qual_name,
            docstring=docstring,
            decorators=decorators,
            bases=bases,
            start_line=node.lineno,
            end_line=getattr(node, "end_lineno", node.lineno),
            start_column=node.col_offset,
            end_column=getattr(node, "end_col_offset", 0),
        )
        self.classes.append(parsed_class)

        # Enter class scope
        self._scope_stack.append(node.name)
        self.generic_visit(node)
        self._scope_stack.pop()

    def _visit_func_def(self, node: Any, is_async: bool) -> None:
        qual_name = self._get_qualified_name(node.name)
        is_method = len(self._scope_stack) > 0 and not self._is_inside_function()
        docstring = ast.get_docstring(node)
        decorators = [ast.unparse(d) if hasattr(ast, "unparse") else str(d) for d in node.decorator_list]

        # Parameters
        parameters = [arg.arg for arg in node.args.args]
        return_type = ast.unparse(node.returns) if getattr(node, "returns", None) and hasattr(ast, "unparse") else None

        parsed_func = ParsedFunction(
            name=node.name,
            qualified_name=qual_name,
            scope_path=list(self._scope_stack),
            is_method=is_method,
            is_async=is_async,
            parameters=parameters,
            return_type=return_type,
            docstring=docstring,
            decorators=decorators,
            start_line=node.lineno,
            end_line=getattr(node, "end_lineno", node.lineno),
            start_column=node.col_offset,
            end_column=getattr(node, "end_col_offset", 0),
        )

        if is_method and self.classes:
            # Associate method with current class
            self.classes[-1].methods.append(parsed_func)
        else:
            self.functions.append(parsed_func)

        # Enter function scope
        parent_func = self._current_function
        self._current_function = parsed_func
        self._scope_stack.append(node.name)

        self.generic_visit(node)

        self._scope_stack.pop()
        self._current_function = parent_func

    def _is_inside_function(self) -> bool:
        return self._current_function is not None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_func_def(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_func_def(node, is_async=True)

    def visit_Call(self, node: ast.Call) -> None:
        raw_call = ast.unparse(node.func) if hasattr(ast, "unparse") else str(node.func)
        caller_scope = self._get_current_caller_scope()

        call_info = ParsedCall(
            raw_call=raw_call,
            caller_scope=caller_scope,
            line=node.lineno,
            col=node.col_offset,
        )

        if self._current_function:
            self._current_function.calls.append(call_info)
        else:
            self.top_level_calls.append(call_info)

        self.generic_visit(node)

    def _get_current_caller_scope(self) -> str:
        if self._scope_stack:
            return ".".join(self._scope_stack)
        return "<top_level>"


def parse_python_file(file_path: str, source_code: str) -> ParsedFileAST:
    """Parses Python source code string into a structured ParsedFileAST."""
    try:
        tree = ast.parse(source_code, filename=file_path)
    except SyntaxError:
        # Return empty AST on syntax error to prevent analyzer crash
        return ParsedFileAST(file_path=file_path)

    visitor = ASTSymbolVisitor(file_path, source_code)
    visitor.visit(tree)

    return ParsedFileAST(
        file_path=file_path,
        imports=visitor.imports,
        classes=visitor.classes,
        functions=visitor.functions,
        top_level_calls=visitor.top_level_calls,
    )
