import sys
from pathlib import Path
from typing import Dict, List, Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.status import Status
from rich.markdown import Markdown
from rich import print as rprint

from docuflow.config import load_config, DocuFlowConfig
from docuflow.git_utils import (
    is_git_repo,
    get_git_root,
    get_unstaged_changes,
    get_staged_changes,
    get_branch_diff,
    group_changes_by_module,
    FileChange,
)
from docuflow.context_builder import build_impact_analysis
from docuflow.ai_engine import (
    find_associated_docs,
    execute_llm_update,
    build_orchestrator_prompt,
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
model = "gemini-2.5-flash"
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
    impact_summaries = []

    for module, changes in grouped.items():
        for change in changes:
            diff_lines = len(change.diff.splitlines()) if change.diff else 0
            # Friendly change type labels
            status_map = {"A": "Added 🆕", "M": "Modified 📝", "D": "Deleted 🗑️", "R": "Renamed 🔄"}
            status_label = status_map.get(change.change_type, change.change_type)
            
            table.add_row(module, change.filepath, status_label, str(diff_lines))
            total_changes += 1

            # Extract AST impact on supported code modifications
            if Path(change.filepath).suffix in {".py", ".ts", ".tsx", ".cs", ".dart"}:
                try:
                    analysis = build_impact_analysis(change.filepath, change.diff)
                    if analysis.added_entities or analysis.modified_entities or analysis.removed_entities:
                        impact_summaries.append((change.filepath, analysis))
                except Exception:
                    pass

    console.print(table)
    console.print(f"\n[bold green]📦 Total files changed: {total_changes} across {len(grouped)} modules.[/bold green]")

    # Render Deep AST Structural impact report
    if impact_summaries:
        console.print("\n[bold magenta]🔬 Deep AST Code Impact Analysis[/bold magenta]")
        for filepath, analysis in impact_summaries:
            console.print(f"  [bold cyan]• {filepath}[/bold cyan]")
            
            if analysis.added_entities:
                for ent in analysis.added_entities:
                    doc_flag = " 📝 [dim](has docstring)[/dim]" if ent.docstring else ""
                    console.print(f"    [green]🆕 [Added] {ent.type} [bold]{ent.signature}[/bold][/green]{doc_flag}")
                    
            if analysis.modified_entities:
                for ent in analysis.modified_entities:
                    doc_flag = " 📝 [dim](has docstring)[/dim]" if ent.docstring else ""
                    console.print(f"    [yellow]📝 [Modified] {ent.type} [bold]{ent.signature}[/bold][/yellow]{doc_flag}")
                    
            if analysis.removed_entities:
                for ent in analysis.removed_entities:
                    console.print(f"    [red]🗑️ [Removed] {ent.type} [bold]{ent.name}[/bold][/red]")

    # Showcase what Phase 3 will execute (LLM Execution)
    console.print(
        Panel(
            "[bold white]🚀 Phase 1 & Phase 2 Complete![/bold white]\n"
            "The repository diff has been parsed, and code entities have been extracted at the AST level.\n"
            "In Phase 3, this structural impact context will trigger the AI documentation agent "
            "to perform context-aware updates to relevant markdown files and sync visual Mermaid flowcharts.",
            title="Next Steps (AI Documentation Engine)",
            border_style="magenta",
        )
    )

def check_markdown_content(content: str) -> List[str]:
    """
    Runs a single-pass, stateful line parser to check markdown alignment with guidelines.
    Returns a list of issues found.
    """
    issues = []
    lines = content.splitlines()
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
                specifier = line[3:].strip()
                if not specifier:
                    unspecified_blocks.append(i + 1)
                if specifier == "mermaid":
                    in_mermaid = True
                in_code_block = True
            else:
                in_code_block = False
                in_mermaid = False
            continue

        if in_code_block:
            if in_mermaid:
                if "[" in line and "]" in line and '"' not in line and ("(" in line or ")" in line):
                    mermaid_issues.append(i + 1)
            continue

        # Outside code blocks: Check for guidelines
        if line.startswith("# ") and not line.startswith("##"):
            h1_count += 1
        
        if "TODO" in line or "FIXME" in line:
            todos.append(i + 1)

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

    return issues

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
            issues = check_markdown_content(content)
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

@app.command("sync")
def sync_cmd(
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
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-d",
        help="Run in dry-run mode. Generates and displays prompts without calling LLM or writing files."
    ),
    create_missing: bool = typer.Option(
        False,
        "--create-missing",
        help="Automatically create missing markdown documentation files for new modules."
    )
):
    """
    Automatically synchronize technical markdown documentation with recent code updates using AI.
    """
    console.print("[bold blue]🤖 DocuFlow AI Documentation Orchestration[/bold blue]\n")
    
    config = load_config(config_path)
    branch = target_branch or config.git.target_branch

    if not is_git_repo():
        console.print("[bold red]❌ Error: Current directory is not a Git repository.[/bold red]")
        raise typer.Exit(code=1)

    # 1. Fetch changed files
    all_changes: List[FileChange] = []
    try:
        if config.git.include_staged:
            all_changes.extend(get_staged_changes())
        if config.git.include_unstaged:
            all_changes.extend(get_unstaged_changes())
        if branch and not all_changes:
            all_changes.extend(get_branch_diff(branch))
    except Exception as e:
        console.print(f"[bold red]❌ Error fetching changes: {e}[/bold red]")
        raise typer.Exit(code=1)

    if not all_changes:
        console.print("[bold green]✨ No code modifications detected! Documentation is up to date.[/bold green]")
        return

    # 2. Locate guidelines rules file
    rules_file = Path(".agents/rules/documentation-rules.md")
    rules_content = ""
    if rules_file.exists():
        try:
            rules_content = rules_file.read_text(encoding="utf-8")
        except Exception:
            pass
    if not rules_content:
        rules_content = "# Guidelines\n* Use single standard H1 title.\n* Wrap Mermaid special labels in quotes.\n* Always fence code blocks with languages."

    docs_dir = Path(config.documentation.docs_dir)
    synced_any = False

    for change in all_changes:
        # Check if the file is within any watch_dirs
        try:
            git_root = get_git_root(Path.cwd())
            file_abs = (git_root / change.filepath).resolve()
        except Exception:
            file_abs = Path(change.filepath).resolve()
            
        in_watch_dir = False
        for watch_dir in config.project.watch_dirs:
            wd_abs = Path(watch_dir).resolve()
            try:
                if file_abs.is_relative_to(wd_abs):
                    in_watch_dir = True
                    break
            except ValueError:
                continue
                
        if not in_watch_dir:
            continue

        # We only sync context for modified or added files
        if change.change_type not in ["M", "A"]:
            continue

        # AST analysis
        try:
            analysis = build_impact_analysis(change.filepath, change.diff)
        except Exception as e:
            console.print(f"[yellow]⚠️ Skipped AST parsing for {change.filepath}: {e}[/yellow]")
            continue

        # Find associated markdown files
        associated = find_associated_docs(change.filepath, docs_dir)
        if not associated:
            if create_missing and Path(change.filepath).suffix in {".py", ".ts", ".tsx", ".cs", ".dart"}:
                stem = Path(change.filepath).stem
                new_md_path = docs_dir / f"{stem}.md"
                title = stem.replace("_", " ").replace("-", " ").title()
                
                if not dry_run:
                    try:
                        new_md_path.parent.mkdir(parents=True, exist_ok=True)
                        new_md_path.write_text(f"# {title}\n\n", encoding="utf-8")
                        console.print(f"[bold green]✨ Auto-created missing documentation file: {new_md_path}[/bold green]")
                    except Exception as e:
                        console.print(f"[bold red]❌ Failed to auto-create {new_md_path}: {e}[/bold red]")
                        continue
                else:
                    console.print(f"[bold yellow]✨ Dry-run: Would auto-create missing documentation file: {new_md_path}[/bold yellow]")
                
                associated = [new_md_path]
            else:
                continue

        for md_path in associated:
            synced_any = True
            console.print(f"[bold cyan]🔗 Found associated documentation: {md_path}[/bold cyan]")
            
            try:
                if not md_path.exists() and dry_run:
                    stem = md_path.stem
                    title = stem.replace("_", " ").replace("-", " ").title()
                    md_content = f"# {title}\n\n"
                else:
                    md_content = md_path.read_text(encoding="utf-8")
            except Exception as e:
                console.print(f"[red]❌ Failed to read {md_path}: {e}[/red]")
                continue

            # Build prompt
            prompt = build_orchestrator_prompt(
                rules_content=rules_content,
                md_content=md_content,
                md_filename=md_path.name,
                analysis=analysis
            )

            if dry_run:
                # Pretty print prompt
                console.print(Panel(prompt, title=f"📋 Dry-Run AI Prompt for {md_path.name}", border_style="yellow"))
                console.print(f"[bold yellow]⚠️ Dry-run: skipped API call for {md_path.name}[/bold yellow]\n")
                continue

            # Call AI
            provider_label = config.ai.provider.upper()
            with console.status(f"[bold green]Running AI Sync ({provider_label}) for {md_path.name}...") as status:
                updated_content, err = execute_llm_update(config, prompt)

            if err:
                console.print(f"[bold red]❌ AI Sync Failed: {err}[/bold red]")
                console.print(f"[yellow]💡 Tip: Set the environment variable {provider_label}_API_KEY or run with --dry-run[/yellow]\n")
                continue

            if not updated_content:
                console.print(f"[bold red]❌ AI returned empty response for {md_path.name}[/bold red]\n")
                continue

            # Validate generated markdown before saving
            issues = check_markdown_content(updated_content)
            if issues:
                console.print(f"[bold yellow]⚠️ Warning: AI output for {md_path.name} violated styling rules:[/bold yellow]")
                for issue in issues:
                    console.print(f"  - [yellow]{issue}[/yellow]")
                console.print("[bold yellow]Proceeding to save with warnings...[/bold yellow]")

            # Save the file
            try:
                md_path.write_text(updated_content, encoding="utf-8")
                console.print(f"[bold green]✅ Successfully updated technical documentation: {md_path}[/bold green]\n")
            except Exception as e:
                console.print(f"[bold red]❌ Failed to save changes to {md_path}: {e}[/bold red]\n")

    if not synced_any:
        console.print("[bold yellow]⚠️ No associated documentation files were found in the docs directory for the changed files.[/bold yellow]")
        console.print(f"[dim]Note: Documentation is matched if the file name stem or classes are mentioned in the markdown file.[/dim]")

@app.command("view")
def view_cmd(
    filepath: Path = typer.Argument(
        ...,
        help="Path to the technical markdown (.md) document to view."
    )
):
    """
    Render a technical documentation markdown file directly inside the terminal with beautiful, rich formatting.
    """
    if not filepath.exists():
        console.print(f"[bold red]❌ Error: File '{filepath}' does not exist.[/bold red]")
        raise typer.Exit(code=1)
        
    try:
        content = filepath.read_text(encoding="utf-8")
        md = Markdown(content)
        console.print(md)
    except Exception as e:
        console.print(f"[bold red]❌ Error reading or rendering file: {e}[/bold red]")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
