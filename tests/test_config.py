import unittest
from pathlib import Path
from docuflow.config import load_config, DocuFlowConfig

class TestConfig(unittest.TestCase):
    def test_default_config(self):
        """
        Verify that configuration loads default values correctly when no config is found.
        """
        config = load_config(Path("non_existent_file.toml"))
        self.assertEqual(config.project.name, "DocuFlow")
        self.assertEqual(config.project.watch_dirs, ["src"])
        self.assertEqual(config.ai.provider, "gemini")
        self.assertEqual(config.ai.temperature, 0.2)
        self.assertEqual(config.git.target_branch, "main")

if __name__ == "__main__":
    unittest.main()
