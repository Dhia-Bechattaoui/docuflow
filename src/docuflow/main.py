import sys
from pathlib import Path
from typing import Dict, List, Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.status import Status
from rich import print as rprint

from docuflow.config import load_config, DocuFlowConfig
from docuflow.git_utils import (
    is_git_repo,
    get_unstaged_changes,
    get_staged_changes,
    get_branch_diff,
    group_changes_by_module,
    FileChange,
)

app = typer.Typer(
    name="docuflow",
    help="🤖 AI-Native Documentation & Architecture Maintenance Agent",
    no_args_is_help=True,
)
console = Console()

@app.command("init")
def init_cmd(
    config_path: Path = typer.Option(
        Path("docuflow.toml"),
        "--config",
        "-c",
        help="Path where the configuration file should be created."
    )
):
    """
    Initialize a new DocuFlow configuration and workspace structure.
    """
    console.print("[bold blue]⚡ Initializing DocuFlow Project...[/bold blue]\n")
    
    # 1. Create docuflow.toml if not exists
    if config_path.exists():
        console.print(f"[yellow]⚠️  Configuration file '{config_path}' already exists. Skipping creation.[/yellow]")
    else:
        # Create a basic default template config
        config_content = """# DocuFlow Configuration Template
# This file controls targeting, rules, and LLM providers for the DocuFlow agent.

[project]
name = "DocuFlow"
watch_dirs = ["src"]

[documentation]
docs_dir = "docs"
patterns = ["*.md"]
rules_dir = ".agents/rules"
workflows_dir = ".agents/workflows"

[ai]
provider = "gemini"
model = "gemini-1.5-pro"
temperature = 0.2
max_tokens = 4096

[git]
target_branch = "main"
include_unstaged = true
include_staged = true
"""
        try:
            config_path.write_text(config_content, encoding="utf-8")
            console.print(f"[green]✅ Created configuration template: [bold]{config_path}[/bold][/green]")
        except Exception as e:
            console.print(f"[red]❌ Failed to create config file: {e}[/red]")
            raise typer.Exit(code=1)

    # 2. Create docs directory if it doesn't exist
    config = load_config(config_path)
    docs_dir = Path(config.documentation.docs_dir)
    if not docs_dir.exists():
        docs_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✅ Created documentation directory: [bold]{docs_dir}/[/bold][/green]")
    else:
        console.print(f"[yellow]ℹ️  Documentation directory '{docs_dir}/' already exists.[/yellow]")

    # 3. Create .agents rules/workflows subdirectories if needed
    rules_dir = Path(config.documentation.rules_dir)
    rules_dir.mkdir(parents=True, exist_ok=True)
    
    workflows_dir = Path(config.documentation.workflows_dir)
    workflows_dir.mkdir(parents=True, exist_ok=True)
    
    console.print("\n[bold green]🎉 DocuFlow project successfully initialized! Ready to manage technical documentation.[/bold green]")

@app.command("run")
def run_cmd(
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to the docuflow.toml configuration file."
    ),
    target_branch: Optional[str] = typer.Option(
        None,
        "--branch",
        "-b",
        help="Target branch/ref to compare against (e.g., origin/main)."
    ),
    staged: Optional[bool] = typer.Option(
        None,
        "--staged/--no-staged",
        help="Force include/exclude staged changes in the analysis."
    ),
    unstaged: Optional[bool] = typer.Option(
        None,
        "--unstaged/--no-unstaged",
        help="Force include/exclude unstaged changes in the analysis."
    ),
):
    """
    Analyze repository changes, group by module, and show what DocuFlow will process.
    """
    console.print("[bold blue]🔍 DocuFlow Git Analysis Engine[/bold blue]\n")
    
    config = load_config(config_path)
    
    # Resolve overrides vs config file defaults
    inc_staged = staged if staged is not None else config.git.include_staged
    inc_unstaged = unstaged if unstaged is not None else config.git.include_unstaged
    branch = target_branch or config.git.target_branch

    if not is_git_repo():
        console.print("[bold red]❌ Error: Current directory is not a Git repository.[/bold red]")
        raise typer.Exit(code=1)

    all_changes: List[FileChange] = []
    
    with console.status("[bold green]Analyzing workspace changes...") as status:
        # Get staged changes
        if inc_staged:
            try:
                staged_changes = get_staged_changes()
                # Label change_type inside representation for display if needed
                all_changes.extend(staged_changes)
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not fetch staged changes: {e}[/yellow]")

        # Get unstaged changes
        if inc_unstaged:
            try:
                unstaged_changes = get_unstaged_changes()
                all_changes.extend(unstaged_changes)
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not fetch unstaged changes: {e}[/yellow]")

        # Get branch difference if specified or fallback
        if branch and not all_changes:
            try:
                branch_changes = get_branch_diff(branch)
                all_changes.extend(branch_changes)
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not fetch diff against '{branch}': {e}[/yellow]")

    if not all_changes:
        console.print("[bold green]✨ No file modifications detected! Documentation is up to date.[/bold green]")
        return

    # Group changes by module
    grouped = group_changes_by_module(all_changes)
    
    # Display the summary table
    table = Table(title="Detected Code Changes grouped by Modules", title_style="bold magenta")
    table.add_column("Module / Folder", style="cyan", no_wrap=True)
    table.add_column("File Path", style="green")
    table.add_column("Status", style="yellow", justify="center")
    table.add_column("Lines of Diff", style="white", justify="right")

    total_changes = 0
    for module, changes in grouped.items():
        for change in changes:
            diff_lines = len(change.diff.splitlines()) if change.diff else 0
            # Friendly change type labels
            status_map = {"A": "Added 🆕", "M": "Modified 📝", "D": "Deleted 🗑️", "R": "Renamed 🔄"}
            status_label = status_map.get(change.change_type, change.change_type)
            
            table.add_row(module, change.filepath, status_label, str(diff_lines))
            total_changes += 1

    console.print(table)
    console.print(f"\n[bold green]📦 Total files changed: {total_changes} across {len(grouped)} modules.[/bold green]")
    
    # Showcase what Phase 3 will execute (LLM Execution)
    console.print(
        Panel(
            "[bold white]🚀 Phase 1 complete![/bold white]\n"
            "In Phase 3, this change context will automatically trigger context-aware LLM agents "
            "to perform non-destructive updates to your markdown documentation and automatically synchronize "
            "your Mermaid architecture diagrams to keep everything in sync.",
            title="Next Steps (AI Documentation Engine)",
            border_style="magenta",
        )
    )

@app.command("check")
def check_cmd(
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to the docuflow.toml configuration file."
    ),
    docs_dir: Optional[Path] = typer.Option(
        None,
        "--docs-dir",
        "-d",
        help="Override path to the documentation directory."
    )
):
    """
    Perform a health check on technical documentation files to ensure alignment with rules.
    """
    console.print("[bold blue]🩺 DocuFlow Documentation Health Checker[/bold blue]\n")
    
    config = load_config(config_path)
    target_docs = docs_dir or Path(config.documentation.docs_dir)
    
    if not target_docs.exists():
        console.print(f"[bold red]❌ Error: Documentation directory '{target_docs}' does not exist.[/bold red]")
        console.print("[yellow]💡 Run [bold]docuflow init[/bold] to set up the default structure.[/yellow]")
        raise typer.Exit(code=1)

    md_files = list(target_docs.glob("**/*.md"))
    if not md_files:
        console.print(f"[yellow]⚠️ No markdown (.md) files found in documentation directory '{target_docs}'.[/yellow]")
        return

    console.print(f"Checking {len(md_files)} markdown files in '[bold]{target_docs}[/bold]'...\n")
    
    table = Table(title="Documentation Health Check Report", title_style="bold magenta")
    table.add_column("Markdown File", style="cyan")
    table.add_column("Status", style="bold", justify="center")
    table.add_column("Details / Recommendations", style="white")

    passed_count = 0
    failed_count = 0

    for md_file in md_files:
        issues = []
        try:
            content = md_file.read_text(encoding="utf-8")
            lines = content.splitlines()
            
            # Run a single-pass, stateful line parser to check all guidelines
            in_code_block = False
            in_mermaid = False
            h1_count = 0
            todos = []
            unspecified_blocks = []
            mermaid_issues = []

            for i, line in enumerate(lines):
                # Handle code block state toggle
                if line.startswith("```"):
                    if not in_code_block:
                        # Opening code block
                        specifier = line[3:].strip()
                        if not specifier:
                            unspecified_blocks.append(i + 1)
                        if specifier == "mermaid":
                            in_mermaid = True
                        in_code_block = True
                    else:
                        # Closing code block
                        in_code_block = False
                        in_mermaid = False
                    continue

                if in_code_block:
                    if in_mermaid:
                        # check for common mermaid label issues like special characters without quotes
                        if "[" in line and "]" in line and '"' not in line and ("(" in line or ")" in line):
                            mermaid_issues.append(i + 1)
                    continue

                # Outside code blocks: Check for guidelines
                if line.startswith("# ") and not line.startswith("##"):
                    h1_count += 1
                
                if "TODO" in line or "FIXME" in line:
                    todos.append(i + 1)

            # Accumulate findings
            if h1_count == 0:
                issues.append("Missing single standard H1 header (`# Title`)")
            elif h1_count > 1:
                issues.append(f"Multiple H1 headers found ({h1_count})")

            if todos:
                issues.append(f"Contains TODO / placeholders on line(s): {', '.join(map(str, todos))}")

            if unspecified_blocks:
                issues.append(f"Code block missing language specifier on line(s): {', '.join(map(str, unspecified_blocks))}")

            if mermaid_issues:
                issues.append(f"Mermaid label with special characters missing quotes on line(s): {', '.join(map(str, mermaid_issues))}")

        except Exception as e:
            issues.append(f"Failed to read file: {e}")

        # Determine file path relative to workspace root
        try:
            rel_path = md_file.relative_to(Path.cwd())
        except ValueError:
            rel_path = md_file

        if not issues:
            table.add_row(str(rel_path), "[bold green]PASS ✅[/bold green]", "Perfect! Alignment with all formatting rules.")
            passed_count += 1
        else:
            issues_joined = "; ".join(issues)
            table.add_row(str(rel_path), "[bold red]FAIL ❌[/bold red]", f"[yellow]{issues_joined}[/yellow]")
            failed_count += 1

    console.print(table)
    
    console.print(f"\n[bold]Summary:[/bold] [green]{passed_count} Passed[/green], [red]{failed_count} Failed[/red].")
    
    if failed_count > 0:
        console.print("\n[bold yellow]💡 Recommendation:[/bold yellow] Clean up the failed files above to comply with [bold]documentation-rules.md[/bold].")

if __name__ == "__main__":
    app()
