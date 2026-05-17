import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
import toml

class ProjectConfig(BaseModel):
    name: str = "DocuFlow"
    watch_dirs: List[str] = Field(default_factory=lambda: ["src"])

class DocumentationConfig(BaseModel):
    docs_dir: str = "docs"
    patterns: List[str] = Field(default_factory=lambda: ["*.md"])
    rules_dir: str = ".agents/rules"
    workflows_dir: str = ".agents/workflows"

class AIConfig(BaseModel):
    provider: str = "gemini"
    model: str = "gemini-1.5-pro"
    temperature: float = 0.2
    max_tokens: int = 4096

class GitConfig(BaseModel):
    target_branch: str = "main"
    include_unstaged: bool = True
    include_staged: bool = True

class DocuFlowConfig(BaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    documentation: DocumentationConfig = Field(default_factory=DocumentationConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    git: GitConfig = Field(default_factory=GitConfig)

def load_config(config_path: Optional[Path] = None) -> DocuFlowConfig:
    """
    Loads and parses the docuflow.toml configuration file.
    If no path is provided, checks the current working directory and its parents.
    """
    if config_path is None:
        # Search upward from the current working directory for docuflow.toml
        current_dir = Path.cwd()
        for parent in [current_dir] + list(current_dir.parents):
            candidate = parent / "docuflow.toml"
            if candidate.is_file():
                config_path = candidate
                break
    
    if config_path and config_path.is_file():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = toml.load(f)
            return DocuFlowConfig(**data)
        except Exception:
            # Fallback to default config on parse error
            pass
            
    return DocuFlowConfig()
