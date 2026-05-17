import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from docuflow.context_builder import build_impact_analysis

class TestContextBuilder(unittest.TestCase):
    def test_build_impact_analysis_python(self):
        """
        Verify that impact analysis works on Python files.
        """
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            file_path = tmp_path / "test.py"
            file_path.write_text("class MyClass:\n    pass\n", encoding="utf-8")
            
            analysis = build_impact_analysis("test.py", "diff content", cwd=tmp_path)
            self.assertEqual(analysis.filepath, "test.py")
            self.assertEqual(len(analysis.added_entities), 1)
            self.assertEqual(analysis.added_entities[0].name, "MyClass")
            self.assertEqual(analysis.raw_diff, "diff content")

    def test_build_impact_analysis_typescript(self):
        """
        Verify that impact analysis works on TypeScript files.
        """
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            file_path = tmp_path / "test.ts"
            file_path.write_text("class MyTSClass {}\n", encoding="utf-8")
            
            analysis = build_impact_analysis("test.ts", "diff content", cwd=tmp_path)
            self.assertEqual(analysis.filepath, "test.ts")
            self.assertEqual(len(analysis.added_entities), 1)
            self.assertEqual(analysis.added_entities[0].name, "MyTSClass")

    def test_build_impact_analysis_unsupported(self):
        """
        Verify that impact analysis gracefully returns raw diff only for unsupported extensions.
        """
        with TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            file_path = tmp_path / "test.txt"
            file_path.write_text("plain text", encoding="utf-8")
            
            analysis = build_impact_analysis("test.txt", "diff content", cwd=tmp_path)
            self.assertEqual(analysis.filepath, "test.txt")
            self.assertEqual(len(analysis.added_entities), 0)
            self.assertEqual(analysis.raw_diff, "diff content")

if __name__ == "__main__":
    unittest.main()
