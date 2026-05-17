import ast
from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field
from tree_sitter_languages import get_parser

class ParameterInfo(BaseModel):
    """
    Represents metadata for a function or method parameter.
    """
    name: str
    type_annotation: Optional[str] = None

class EntityInfo(BaseModel):
    """
    Represents a structural code entity (class, function, or method).
    """
    name: str
    type: str  # "class", "function", "method"
    signature: str
    docstring: Optional[str] = None
    line_start: int
    line_end: int
    parameters: List[ParameterInfo] = Field(default_factory=list)
    return_type: Optional[str] = None

class BaseParser(ABC):
    """
    Abstract Base Class for all language-specific AST parsers.
    """
    @abstractmethod
    def parse(self, code: str) -> List[EntityInfo]:
        """
        Parses source code string and returns a list of high-level code entities.
        """
        pass

class PythonASTVisitor(ast.NodeVisitor):
    """
    AST Visitor to traverse and extract high-level structural classes and functions.
    """
    def __init__(self):
        self.entities: List[EntityInfo] = []
        self.current_class: Optional[str] = None

    def visit_ClassDef(self, node: ast.ClassDef):
        docstring = ast.get_docstring(node)
        # Class bases / inheritance
        bases = [ast.unparse(b) for b in node.bases]
        bases_str = f"({', '.join(bases)})" if bases else ""
        signature = f"class {node.name}{bases_str}"
        
        self.entities.append(EntityInfo(
            name=node.name,
            type="class",
            signature=signature,
            docstring=docstring,
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
        ))
        
        # Save context to visit methods inside this class
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.visit_any_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.visit_any_function(node)

    def visit_any_function(self, node):
        docstring = ast.get_docstring(node)
        
        # Extract parameter details
        params = []
        for arg in node.args.args:
            annotation = ast.unparse(arg.annotation) if arg.annotation else None
            params.append(ParameterInfo(name=arg.arg, type_annotation=annotation))
            
        return_type = ast.unparse(node.returns) if node.returns else None
        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        func_type = "method" if self.current_class else "function"
        
        # Format human-readable signature
        args_str = ", ".join([p.name + (f": {p.type_annotation}" if p.type_annotation else "") for p in params])
        signature = f"{prefix} {node.name}({args_str})"
        if return_type:
            signature += f" -> {return_type}"
            
        self.entities.append(EntityInfo(
            name=f"{self.current_class}.{node.name}" if self.current_class else node.name,
            type=func_type,
            signature=signature,
            docstring=docstring,
            line_start=node.lineno,
            line_end=getattr(node, "end_lineno", node.lineno),
            parameters=params,
            return_type=return_type
        ))
        
        # Keep walking to capture nested structures if any
        self.generic_visit(node)

class PythonNativeParser(BaseParser):
    """
    Python-specific AST parser using the native ast library.
    """
    def parse(self, code: str) -> List[EntityInfo]:
        try:
            tree = ast.parse(code)
            visitor = PythonASTVisitor()
            visitor.visit(tree)
            return visitor.entities
        except (SyntaxError, ValueError, TypeError):
            return []

class TreeSitterParser(BaseParser):
    """
    Parser that leverages Tree-Sitter to extract structures for multi-language projects.
    """
    def __init__(self, language_key: str):
        self.language_key = language_key
        # tree-sitter-languages uses c_sharp instead of csharp
        ts_key = "c_sharp" if language_key == "csharp" else language_key
        try:
            self.parser = get_parser(ts_key)
        except Exception:
            self.parser = None

    def parse(self, code: str) -> List[EntityInfo]:
        if not self.parser:
            return []
        try:
            tree = self.parser.parse(bytes(code, "utf8"))
            entities = []
            self._traverse(tree.root_node, code, entities, None)
            return entities
        except Exception:
            return []

    def _traverse(self, node, code: str, entities: List[EntityInfo], current_class: Optional[str]):
        node_type = node.type
        
        # 1. CLASS & INTERFACE extraction
        if node_type in ("class_declaration", "interface_declaration", "record_declaration", "class_definition"):
            # Find the identifier node for the class name
            name = ""
            for child in node.children:
                if child.type in ("identifier", "type_identifier"):
                    name = code[child.start_byte:child.end_byte]
                    break
            
            if name:
                signature = code[node.start_byte:node.children[min(len(node.children)-1, 3)].end_byte].split("{")[0].strip()
                # Find docstring/comment right before the class
                docstring = self._extract_leading_comment(node, code)
                
                entities.append(EntityInfo(
                    name=name,
                    type="class",
                    signature=signature or f"class {name}",
                    docstring=docstring,
                    line_start=node.start_point[0] + 1,
                    line_end=node.end_point[0] + 1,
                ))
                
                # Recursively parse children inside this class context
                for child in node.children:
                    self._traverse(child, code, entities, name)
                return

        # 2. METHOD extraction
        elif node_type in ("method_definition", "method_declaration") and current_class:
            name = ""
            for child in node.children:
                if child.type in ("property_identifier", "identifier"):
                    name = code[child.start_byte:child.end_byte]
                    break
            
            if name:
                signature = code[node.start_byte:node.end_byte].split("{")[0].strip().split("\n")[0]
                docstring = self._extract_leading_comment(node, code)
                
                # Parameters
                params = []
                for child in node.children:
                    if child.type in ("formal_parameters", "formal_parameter_list", "parameter_list"):
                        for param_node in child.children:
                            if param_node.type in ("formal_parameter", "parameter"):
                                param_name = code[param_node.start_byte:param_node.end_byte].strip()
                                params.append(ParameterInfo(name=param_name))
                
                entities.append(EntityInfo(
                    name=f"{current_class}.{name}",
                    type="method",
                    signature=signature or f"def {name}",
                    docstring=docstring,
                    line_start=node.start_point[0] + 1,
                    line_end=node.end_point[0] + 1,
                    parameters=params
                ))
                return

        # 3. FUNCTION extraction
        elif node_type in ("function_declaration", "function_definition"):
            name = ""
            for child in node.children:
                if child.type == "identifier":
                    name = code[child.start_byte:child.end_byte]
                    break
            
            if name:
                signature = code[node.start_byte:node.end_byte].split("{")[0].strip().split("\n")[0]
                docstring = self._extract_leading_comment(node, code)
                
                entities.append(EntityInfo(
                    name=name,
                    type="function",
                    signature=signature or f"def {name}",
                    docstring=docstring,
                    line_start=node.start_point[0] + 1,
                    line_end=node.end_point[0] + 1,
                ))
                return

        # Keep traversing
        for child in node.children:
            self._traverse(child, code, entities, current_class)

    def _extract_leading_comment(self, node, code: str) -> Optional[str]:
        prev = node.prev_sibling
        if prev and prev.type in ("comment", "line_comment", "block_comment"):
            comment_text = code[prev.start_byte:prev.end_byte].strip()
            cleaned = []
            for line in comment_text.split("\n"):
                line = line.strip().lstrip("/*").rstrip("*/").lstrip("*").lstrip("//").strip()
                if line:
                    cleaned.append(line)
            return "\n".join(cleaned) if cleaned else None
        return None

class ParserFactory:
    """
    Factory to retrieve language-specific parsers.
    """
    @staticmethod
    def get_parser(language_or_ext: str) -> BaseParser:
        clean_key = language_or_ext.lower().strip(".")
        if clean_key in ("py", "python"):
            return PythonNativeParser()
        elif clean_key in ("ts", "tsx", "typescript", "js", "javascript"):
            return TreeSitterParser("typescript")
        elif clean_key in ("cs", "csharp", "c_sharp"):
            return TreeSitterParser("csharp")
        elif clean_key in ("dart", "flutter"):
            return TreeSitterParser("dart")
        # Default fallback to Python parser
        return PythonNativeParser()

def parse_code_structure(code: str) -> List[EntityInfo]:
    """
    Legacy helper function for backward compatibility.
    """
    return ParserFactory.get_parser("python").parse(code)


