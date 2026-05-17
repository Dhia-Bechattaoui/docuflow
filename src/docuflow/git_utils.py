import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel

class FileChange(BaseModel):
    """
    Represents a single file change extracted from Git.
    """
    filepath: str
    change_type: str  # 'A' (Added), 'M' (Modified), 'D' (Deleted), 'R' (Renamed), etc.
    diff: str
    module: str

def run_git_command(args: List[str], cwd: Optional[Path] = None) -> str:
    """
    Executes a git command and returns the stdout string.
    Raises RuntimeError if the command fails.
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=True,
            cwd=cwd or Path.cwd()
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git command failed: {' '.join(e.cmd)}\nError: {e.stderr.strip()}") from e
    except FileNotFoundError as e:
        raise RuntimeError("Git executable not found on system path.") from e

def is_git_repo(cwd: Optional[Path] = None) -> bool:
    """
    Checks if the given directory is inside a git repository.
    """
    try:
        output = run_git_command(["rev-parse", "--is-inside-work-tree"], cwd=cwd)
        return output == "true"
    except RuntimeError:
        return False

def get_git_root(cwd: Optional[Path] = None) -> Path:
    """
    Gets the absolute Path of the Git repository root.
    """
    output = run_git_command(["rev-parse", "--show-toplevel"], cwd=cwd)
    return Path(output).resolve()

def extract_module(filepath: str) -> str:
    """
    Helper to extract the module/folder name for grouping.
    e.g., 'src/auth/login.py' -> 'src/auth'
          'src/main.py' -> 'src'
          'plan.md' -> '.'
    """
    path = Path(filepath)
    parts = path.parts
    if len(parts) > 2:
        return str(Path(*parts[:2]))
    elif len(parts) == 2:
        return parts[0]
    else:
        return "."

def parse_name_status_line(line: str) -> Optional[tuple[str, str]]:
    """
    Parses a line from `git diff --name-status`
    e.g., 'M\tsrc/main.py' -> ('M', 'src/main.py')
    """
    if not line.strip():
        return None
    parts = line.split("\t")
    if len(parts) >= 2:
        # handle renamed status which could be 'R100\told_name\tnew_name'
        status = parts[0][0]  # Just take the first character (e.g. 'R', 'M', 'A')
        filepath = parts[-1]  # Take the final destination file path
        return status, filepath
    return None

def get_file_diff(filepath: str, extra_args: List[str], cwd: Optional[Path] = None) -> str:
    """
    Gets the diff content for a specific file.
    """
    try:
        # run git diff with specific arguments and targeting the file
        return run_git_command(["diff"] + extra_args + ["--", filepath], cwd=cwd)
    except RuntimeError:
        return ""

def get_unstaged_changes(cwd: Optional[Path] = None) -> List[FileChange]:
    """
    Retrieves all unstaged file modifications and their diffs.
    """
    if not is_git_repo(cwd):
        return []
    
    # Get the status list of unstaged files
    status_output = run_git_command(["diff", "--name-status"], cwd=cwd)
    changes = []
    
    for line in status_output.splitlines():
        parsed = parse_name_status_line(line)
        if not parsed:
            continue
        status, filepath = parsed
        # Get diff for this specific unstaged file
        diff = get_file_diff(filepath, [], cwd=cwd)
        changes.append(FileChange(
            filepath=filepath,
            change_type=status,
            diff=diff,
            module=extract_module(filepath)
        ))
        
    return changes

def get_staged_changes(cwd: Optional[Path] = None) -> List[FileChange]:
    """
    Retrieves all staged file modifications and their diffs.
    """
    if not is_git_repo(cwd):
        return []
    
    # Get the status list of staged files
    status_output = run_git_command(["diff", "--cached", "--name-status"], cwd=cwd)
    changes = []
    
    for line in status_output.splitlines():
        parsed = parse_name_status_line(line)
        if not parsed:
            continue
        status, filepath = parsed
        # Get diff for this specific staged file
        diff = get_file_diff(filepath, ["--cached"], cwd=cwd)
        changes.append(FileChange(
            filepath=filepath,
            change_type=status,
            diff=diff,
            module=extract_module(filepath)
        ))
        
    return changes

def get_branch_diff(target_branch: str, cwd: Optional[Path] = None) -> List[FileChange]:
    """
    Retrieves file modifications and diffs between current branch (HEAD) and a target branch/commit.
    Uses target_branch...HEAD (triple dot) to see changes introduced on current branch since it split from target.
    """
    if not is_git_repo(cwd):
        return []
    
    try:
        # Check if the target branch exists or can be resolved
        run_git_command(["rev-parse", "--verify", target_branch], cwd=cwd)
    except RuntimeError:
        # Fallback to single-dot or direct branch comparison if the reference is different
        pass

    # Get status list comparing the target branch to current HEAD
    status_output = run_git_command(["diff", f"{target_branch}...HEAD", "--name-status"], cwd=cwd)
    changes = []
    
    for line in status_output.splitlines():
        parsed = parse_name_status_line(line)
        if not parsed:
            continue
        status, filepath = parsed
        # Get diff comparison
        diff = get_file_diff(filepath, [f"{target_branch}...HEAD"], cwd=cwd)
        changes.append(FileChange(
            filepath=filepath,
            change_type=status,
            diff=diff,
            module=extract_module(filepath)
        ))
        
    return changes

def group_changes_by_module(changes: List[FileChange]) -> Dict[str, List[FileChange]]:
    """
    Groups a list of FileChange objects by their module folder.
    """
    grouped: Dict[str, List[FileChange]] = {}
    for change in changes:
        grouped.setdefault(change.module, []).append(change)
    return grouped
