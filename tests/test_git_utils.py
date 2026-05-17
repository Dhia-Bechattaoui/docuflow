import unittest
from docuflow.git_utils import extract_module

class TestGitUtils(unittest.TestCase):
    def test_extract_module(self):
        """
        Verify that file paths are grouped correctly into their respective parent modules.
        """
        self.assertEqual(extract_module("src/auth/login.py"), "src/auth")
        self.assertEqual(extract_module("src/main.py"), "src")
        self.assertEqual(extract_module("plan.md"), ".")
        self.assertEqual(extract_module("tests/unit/test_core.py"), "tests/unit")

if __name__ == "__main__":
    unittest.main()
