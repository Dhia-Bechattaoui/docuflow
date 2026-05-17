# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2026-05-17

### Added

- **Packaging Quality**: Created beautiful `README.md` and standard open-source `LICENSE` in the root repository.

### Changed

- **Version Upgrades**: Incremented project and package versions from `0.3.0` to `0.3.1` to publish package metadata and descriptive pages to PyPI.

## [0.3.0] - 2026-05-17

### Added

- **Technical Documentation TUI Viewer**: Implemented the `view` CLI command in `main.py` using `rich.markdown.Markdown` to parse and render styled, technical documentation documents directly within the developer's console workspace.
- **GitHub Actions CI/CD Integration**: Engineered the `.github/workflows/docuflow-ci.yml` pipeline that triggers on all pushes and pull requests to automate code compilation checks, run the python unittest discover suite, and execute `docuflow check` documentation quality audits.

### Changed

- **Version Upgrades**: Incremented project and package versions from `0.2.0` to `0.3.0` to represent the Phase 4 feature milestone.

## [0.2.0] - 2026-05-17

### Added

- **AI Documentation Orchestrator Module**: Created `ai_engine.py` incorporating autonomous matching heuristics (scanning and locating markdown documentation files associated with modified source files via normalized character comparisons), guidelines rules loader, and multi-provider (Google Gemini and OpenAI) API call executors.
- **AI Sync CLI Command**: Added `sync` command to `main.py` allowing developers to trigger context-aware AI synchronizations for their repository's modified directories.
- **Integrated Health Verification**: The synchronizer automatically validates newly generated LLM outputs against the single H1, placeholder-free, language-fenced, and quoted Mermaid rules using the extracted checker helper before writing them to disk.
- **Robust Dry-Run Support**: Added `--dry-run` (`-d`) flag to `docuflow sync`, printing complete structured AI prompts and execution previews in beautiful Rich console panels without hitting remote networks.
- **AI Orchestration Test Suite**: Created a unit test suite in `tests/test_ai_engine.py` validating the normalized matching heuristics and AST changes summary formatting.

### Changed

- **Version Upgrades**: Incremented project and package versions from `0.1.0` to `0.2.0` to represent the Phase 3 milestone.

## [0.1.0] - 2026-05-17

### Added

- **Python AST Parser Module**: Implemented a modular syntax parser in `parser.py` using Python's native `ast` library. It extracts rich structural metadata from Python files including class hierarchies, bases, docstrings, method signatures, line ranges, and parameters.
- **AST Change Impact Engine**: Created a code context diff module in `context_builder.py` that downloads base file contents from Git, parses both the original and current file AST structures, and computes a deep structural diff identifying added, modified, or removed classes, functions, and methods.
- **Enhanced Git CLI Output**: Upgraded the `run` command in `main.py` to calculate and render a comprehensive, beautiful terminal AST Code Impact analysis sub-report using `rich` console highlights.
- **AST Parsing Test Suite**: Added a robust unit test suite in `tests/test_parser.py` verifying AST extraction of classes, async functions, methods, parameter types, and docstrings.

### Changed

- **Version Upgrades**: Incremented project and package versions from `0.0.1` to `0.1.0` to represent the Phase 2 feature milestone.

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

[Unreleased]: https://github.com/dhia-bechattaoui/docuflow/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/dhia-bechattaoui/docuflow/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/dhia-bechattaoui/docuflow/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/dhia-bechattaoui/docuflow/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/dhia-bechattaoui/docuflow/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/dhia-bechattaoui/docuflow/releases/tag/v0.0.1
