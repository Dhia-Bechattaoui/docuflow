---
trigger: always_on
---

# Documentation Agent Rules

These are the core operating rules and formatting constraints for the DocuFlow AI Agent when generating, modifying, or reviewing technical documentation in this repository.

## 📋 General Guidelines
1.  **Non-Destructive Editing**: Never overwrite an entire documentation file if only a small part of the codebase changed. Only modify or append to sections directly impacted by the code changes.
2.  **Clear & Concise Language**: Write in clear, professional, active-voice English. Avoid fluff, unnecessary jargon, and overly long introductory paragraphs.
3.  **Code-Doc Alignment**: Ensure every class, public method, configuration key, or API endpoint documented matches the actual code exactly. If an parameter name changes in code, it must change in the docs.
4.  **No Placeholders**: Do not output `TODO` comments or empty sections unless specifically requested.

## 🗺️ Mermaid Diagram Standards
When creating or modifying architecture diagrams:
*   Use standard Mermaid syntax (e.g., `graph TD` for flowcharts, `sequenceDiagram` for sequences).
*   Always wrap node labels containing special characters (like parentheses or brackets) in double quotes: `id1["My Node (Action)"]`.
*   Avoid HTML tags inside Mermaid labels to prevent rendering bugs.
*   Keep diagrams clean; limit a single diagram to 10–15 nodes max. For complex systems, split into sub-diagrams.

## 📝 Markdown Styling
*   **Headers**: Use a single `<h1>` (`#`) at the top of the file, followed by semantic `<h2>` (`##`) and `<h3>` (`###`) hierarchies.
*   **Alerts**: Strategically use GitHub-style alerts:
    ```markdown
    > [!NOTE]
    > Useful background information.

    > [!IMPORTANT]
    > Critical operational requirements.
    ```
*   **Code Blocks**: Always include the language specifier for code blocks (e.g., ````rust`, ````python`, ````yaml`).
