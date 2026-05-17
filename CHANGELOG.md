# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.1] - 2026-05-17

### Added

- **Core Packaging Structure**: Configured standard `pyproject.toml` (PEP 621) with complete dependencies (`typer`, `rich`, `pydantic`, `toml`, `gitpython`, `google-generativeai`, `openai`) and backward-compatible `setup.py` shim for older pip versions.
- **Base CLI Interface**: Created main CLI entry point `main.py` implementing modular user commands: `docuflow init`, `docuflow run`, and `docuflow check` using `typer`.
- **Elegant Terminal UI**: Integrated the `rich` framework to output gorgeous, colorized Unicode tables, status indicators, and panel dividers.
- **Configuration Parsing Engine**: Created `config.py` using Pydantic models for type-safe validation, parsing the default `docuflow.toml` template, and automatically resolving default config directories.
- **Robust Git Analysis Engine**: Created `git_utils.py` running native `git` commands through Python subprocess pipes to safely pull staged changes, unstaged edits, and branch-level diffs, and group modifications by their module directory.
- **Stateful Markdown Health Checker**: Implemented a custom stateful, single-pass parser in the `check` command. It correctly parses and enforces technical documentation guidelines (single title H1, no placeholders/TODOs, explicit code-fencing language tags, and quoted Mermaid parentheses) while avoiding false positives on comment lines inside programming code blocks.
- **Git Ignoring Setup**: Added standard `.gitignore` file to isolate local virtual environments (`.venv`), Python compiled bytecode, and package builds from git tracking.
- **Documentation Setup**: Automated the initial creation of target `docs/` folder structures via `docuflow init`.

[0.0.1]: https://github.com/dhia/docuflow/releases/tag/v0.0.1
