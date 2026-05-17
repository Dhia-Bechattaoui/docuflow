import unittest
from docuflow.parser import parse_code_structure

class TestParser(unittest.TestCase):
    def test_parse_simple_code(self):
        """
        Verify that classes, methods, docstrings, and parameter lists are parsed correctly.
        """
        code = """
class MyClass:
    \"\"\"This is a sample class.\"\"\"
    def my_method(self, name: str) -> bool:
        return True

async def my_async_func(x: int):
    pass
"""
        entities = parse_code_structure(code)
        
        # 1. Verify Class
        classes = [e for e in entities if e.type == "class"]
        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0].name, "MyClass")
        self.assertEqual(classes[0].docstring, "This is a sample class.")
        
        # 2. Verify Method
        methods = [e for e in entities if e.type == "method"]
        self.assertEqual(len(methods), 1)
        self.assertEqual(methods[0].name, "MyClass.my_method")
        self.assertEqual(methods[0].return_type, "bool")
        self.assertEqual(len(methods[0].parameters), 2)
        self.assertEqual(methods[0].parameters[0].name, "self")
        self.assertEqual(methods[0].parameters[1].name, "name")
        self.assertEqual(methods[0].parameters[1].type_annotation, "str")
        
        # 3. Verify Async Function
        functions = [e for e in entities if e.type == "function"]
        self.assertEqual(len(functions), 1)
        self.assertEqual(functions[0].name, "my_async_func")
        self.assertTrue(functions[0].signature.startswith("async def"))

if __name__ == "__main__":
    unittest.main()
