from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from docuflow.parser import EntityInfo, parse_code_structure
from docuflow.git_utils import run_git_command, is_git_repo

class ImpactAnalysis(BaseModel):
    """
    Represents the full structural impact analysis of changes made to a file.
    """
    filepath: str
    added_entities: List[EntityInfo] = Field(default_factory=list)
    modified_entities: List[EntityInfo] = Field(default_factory=list)
    removed_entities: List[EntityInfo] = Field(default_factory=list)
    raw_diff: str = ""

def get_git_file_content(filepath: str, ref: str = "HEAD", cwd: Optional[Path] = None) -> str:
    """
    Retrieves the content of a file from Git history at a specific reference.
    Returns an empty string if the file did not exist yet (e.g. newly added).
    """
    try:
        return run_git_command(["show", f"{ref}:{filepath}"], cwd=cwd)
    except Exception:
        return ""

def build_impact_analysis(filepath: str, raw_diff: str, base_ref: str = "HEAD", cwd: Optional[Path] = None) -> ImpactAnalysis:
    """
    Compares the AST structures of a file between its Git base state and current filesystem state
    to identify added, modified, or removed classes, functions, and methods.
    """
    # 1. Fetch original content from Git
    original_content = get_git_file_content(filepath, ref=base_ref, cwd=cwd)
    
    # 2. Fetch current content from local disk
    current_path = (cwd or Path.cwd()) / filepath
    current_content = ""
    if current_path.is_file():
        try:
            current_content = current_path.read_text(encoding="utf-8")
        except Exception:
            pass
            
    # 3. For supported code files, parse and compare ASTs
    from docuflow.parser import ParserFactory
    ext = Path(filepath).suffix.lower()
    if ext in (".py", ".ts", ".tsx", ".cs", ".dart"):
        parser = ParserFactory.get_parser(ext)
        old_entities = {e.name: e for e in parser.parse(original_content)}
        new_entities = {e.name: e for e in parser.parse(current_content)}
        
        added_entities = []
        modified_entities = []
        removed_entities = []
        
        # Check added and modified entities
        for name, new_ent in new_entities.items():
            if name not in old_entities:
                added_entities.append(new_ent)
            else:
                old_ent = old_entities[name]
                # Consider it modified if signature or docstring changes, or if the size/bounds of implementation changed
                if (new_ent.signature != old_ent.signature or
                    new_ent.docstring != old_ent.docstring or
                    (new_ent.line_end - new_ent.line_start) != (old_ent.line_end - old_ent.line_start)):
                    modified_entities.append(new_ent)
                    
        # Check removed entities
        for name, old_ent in old_entities.items():
            if name not in new_entities:
                removed_entities.append(old_ent)
                
        return ImpactAnalysis(
            filepath=filepath,
            added_entities=added_entities,
            modified_entities=modified_entities,
            removed_entities=removed_entities,
            raw_diff=raw_diff
        )
        
    # Unsupported files just map the raw diff without AST structures
    return ImpactAnalysis(
        filepath=filepath,
        raw_diff=raw_diff
    )
