import ast
from typing import List, Optional
from pydantic import BaseModel, Field

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

def parse_code_structure(code: str) -> List[EntityInfo]:
    """
    Parses a string of Python code and returns a list of high-level code entities.
    Returns an empty list if compilation fails (e.g., SyntaxError).
    """
    try:
        tree = ast.parse(code)
        visitor = PythonASTVisitor()
        visitor.visit(tree)
        return visitor.entities
    except (SyntaxError, ValueError, TypeError):
        return []
