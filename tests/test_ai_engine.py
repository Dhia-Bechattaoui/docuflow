import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from docuflow.ai_engine import find_associated_docs, format_ast_summary, build_orchestrator_prompt
from docuflow.context_builder import ImpactAnalysis
from docuflow.parser import EntityInfo

class TestAIEngine(unittest.TestCase):
    def test_find_associated_docs(self):
        """
        Verify that our matching heuristics successfully locate markdown documents
        referencing the changed code filepath or class stems.
        """
        with TemporaryDirectory() as tmp_dir:
            docs_path = Path(tmp_dir)
            
            md_file1 = docs_path / "sample_api.md"
            md_file1.write_text("This documents the GitUtils helper.", encoding="utf-8")
            
            md_file2 = docs_path / "other_docs.md"
            md_file2.write_text("Unrelated content.", encoding="utf-8")
            
            matches = find_associated_docs("src/docuflow/git_utils.py", docs_path)
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0].name, "sample_api.md")

    def test_format_ast_summary(self):
        """
        Verify that AST changes are summarized clearly for prompt consumption.
        """
        analysis = ImpactAnalysis(
            filepath="test.py",
            added_entities=[EntityInfo(
                name="my_func", 
                type="function", 
                signature="def my_func()", 
                line_start=1, 
                line_end=2
            )]
        )
        summary = format_ast_summary(analysis)
        self.assertIn("Added Code Entities:", summary)
        self.assertIn("def my_func()", summary)

    def test_build_orchestrator_prompt_instructions(self):
        """
        Verify that build_orchestrator_prompt includes our new prompt guidance
        for empty or header-only markdown files.
        """
        analysis = ImpactAnalysis(filepath="test.py")
        prompt = build_orchestrator_prompt(
            rules_content="Rule 1",
            md_content="# Header Only",
            md_filename="test.md",
            analysis=analysis
        )
        self.assertIn("If the target technical document is empty or only contains a basic header", prompt)

    def test_language_specific_instructions(self):
        """
        Verify that language-specific framework guidelines are injected in the prompt.
        """
        # 1. C#
        analysis_cs = ImpactAnalysis(filepath="Helper.cs")
        prompt_cs = build_orchestrator_prompt("Rules", "Content", "test.md", analysis_cs)
        self.assertIn("C# / .NET", prompt_cs)
        self.assertIn("Interfaces starting with 'I'", prompt_cs)

        # 2. TypeScript
        analysis_ts = ImpactAnalysis(filepath="component.ts")
        prompt_ts = build_orchestrator_prompt("Rules", "Content", "test.md", analysis_ts)
        self.assertIn("TypeScript / Angular", prompt_ts)
        self.assertIn("Component decorators", prompt_ts)

        # 3. Dart / Flutter
        analysis_dart = ImpactAnalysis(filepath="widget.dart")
        prompt_dart = build_orchestrator_prompt("Rules", "Content", "test.md", analysis_dart)
        self.assertIn("Dart / Flutter", prompt_dart)
        self.assertIn("Widget lifecycles", prompt_dart)

if __name__ == "__main__":
    unittest.main()
