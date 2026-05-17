# DocuFlow: AI-Native Documentation & Architecture Maintenance Agent

DocuFlow is an automated, AI-powered system that runs locally or in CI/CD pipelines to ensure your project's technical documentation, API specifications, and architectural diagrams (Mermaid) never go out of date.

## 🚀 The Problem
In the AI era, code is written faster than ever. However, technical documentation, system design documents, and API references are rarely updated, leading to **massive cognitive debt** and stale documentation that misleads both human developers and AI coding agents.

## 💡 The Solution
DocuFlow acts as an autonomous documentation manager. It:
1. Watches your repository for git changes or pull requests.
2. Extracts abstract syntax tree (AST) changes and code diffs.
3. Automatically updates relevant markdown documentation.
4. Regenerates or modifies Mermaid architecture diagrams to match new code structures.
5. Performs a "Doc Health check" to flag missing explanations.

---

## 🛠️ Tech Stack
*   **CLI / Core**: Python (with `typer` or `click`) or Node.js/TypeScript. Python is chosen here for its rich parser ecosystem and ease of integrating LLM/Agentic libraries.
*   **Parsing**: Language-specific AST parsers (tree-sitter).
*   **AI Engine**: Integrates with Gemini / OpenAI / Anthropic APIs to contextually update existing markdown files instead of overwriting them.

---

## 🗺️ Implementation Plan

### Phase 1: Core CLI & Git Integration
- [x] Initialize the CLI tool (`docuflow`).
- [x] Implement a command to analyze the current Git diff or a specific PR.
- [x] Extract file changes and group them by modules/folders.

### Phase 2: Code Parsing & Context Extraction
- [x] Implement AST parser (using Python native AST visitor) to detect added/modified classes, functions, and interfaces.
- [x] Design the context-builder that extracts the "impacted area" of a code change.

### Phase 3: AI Documentation Engine
- [x] Implement the agentic workflow (`docuflow sync` command) to update existing `.md` files.
- [x] Create robust prompts that instruct the LLM to perform precise, non-destructive updates to documentation.
- [x] Build automatic Mermaid diagram generator/updater to visualize state machines or class diagrams.

### Phase 4: CI/CD & Formatting
- [x] Add GitHub Actions workflow integrations (`docuflow-ci.yml`).
- [x] Support custom configuration files (`docuflow.toml`) to target specific directories and documentation rules.
- [x] Build a local CLI markdown viewer/TUI dashboard (`docuflow view` command).

### Phase 5: Polyglot (Multi-Language) Support
- [ ] Refactor `parser.py` into a modular `BaseParser` interface (Factory Pattern).
- [ ] Integrate `tree-sitter` and `tree-sitter-languages` for universal syntax parsing.
- [ ] Add parsing support for TypeScript/Angular and C#/.NET.
- [ ] Add parsing support for Dart/Flutter.
- [ ] Update `ai_engine.py` to use framework-aware instructions based on detected languages.

---

## 📂 Project Directory Structure

```
docuflow/
├── .agents/
│   ├── rules/
│   │   └── documentation_rules.md  # Rules for AI documentation style
│   └── workflows/
│       └── auto_document.md       # AI workflows for updating documentation
├── src/                           # Source code of the CLI tool
├── tests/                         # Integration & unit tests
├── docuflow.toml                  # Default config template
├── plan.md                        # This project plan
└── README.md                      # General introduction
```
