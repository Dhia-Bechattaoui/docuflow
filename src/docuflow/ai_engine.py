import os
from pathlib import Path
from typing import List, Optional, Tuple
from google import generativeai as genai
from openai import OpenAI

from docuflow.config import DocuFlowConfig
from docuflow.context_builder import ImpactAnalysis

def find_associated_docs(filepath: str, docs_dir: Path) -> List[Path]:
    """
    Scans the documentation directory and matches markdown files that refer
    to the given code filepath, filename, or module parent.
    Normalizes casing, underscores, and hyphens to maximize match accuracy.
    """
    associated: List[Path] = []
    if not docs_dir.exists():
        return associated

    filename = Path(filepath).name
    basename = Path(filepath).stem
    
    # Pre-calculate normalized flat values for code file
    flat_basename = basename.replace("_", "").replace("-", "").lower()
    flat_filename = filename.replace("_", "").replace("-", "").lower()
    
    for md_file in docs_dir.glob("**/*.md"):
        # Skip hidden or temporary files
        if md_file.name.startswith("."):
            continue
        try:
            content = md_file.read_text(encoding="utf-8")
            flat_content = content.replace("_", "").replace("-", "").lower()
            flat_md_filename = md_file.name.replace("_", "").replace("-", "").lower()
            
            # Match if:
            # - Flat filename stem (e.g., 'gitutils') is in the flat markdown content
            # - Flat filename (e.g., 'gitutils.py') is in the flat markdown content
            # - Flat filename stem (e.g., 'gitutils') matches the flat markdown filename stem
            if (flat_filename in flat_content or 
                flat_basename in flat_content or 
                flat_basename in flat_md_filename):
                associated.append(md_file)
        except Exception:
            pass
            
    return associated

def format_ast_summary(analysis: ImpactAnalysis) -> str:
    """
    Formats a clean, human-readable summary of the AST modifications for the prompt.
    """
    summary = []
    if analysis.added_entities:
        summary.append("Added Code Entities:")
        for ent in analysis.added_entities:
            summary.append(f"  - {ent.type.capitalize()} `{ent.name}` with signature: `{ent.signature}`")
    if analysis.modified_entities:
        summary.append("Modified Code Entities:")
        for ent in analysis.modified_entities:
            summary.append(f"  - {ent.type.capitalize()} `{ent.name}` with signature: `{ent.signature}`")
    if analysis.removed_entities:
        summary.append("Removed/Deleted Code Entities:")
        for ent in analysis.removed_entities:
            summary.append(f"  - {ent.type.capitalize()} `{ent.name}`")
            
    return "\n".join(summary) if summary else "No high-level AST structural changes."

def build_orchestrator_prompt(
    rules_content: str,
    md_content: str,
    md_filename: str,
    analysis: ImpactAnalysis
) -> str:
    """
    Assembles the detailed prompt for the AI documentation agent, passing the style rules,
    current markdown file content, git diff, and AST modifications.
    """
    ast_summary = format_ast_summary(analysis)
    
    prompt = f"""You are the DocuFlow AI Documentation Agent. Your job is to update the technical documentation markdown file to accurately reflect recent code modifications.

--- SYSTEM STYLING & FORMATTING RULES (documentation-rules.md) ---
{rules_content}

--- TARGET TECHNICAL DOCUMENT TO UPDATE ---
File Name: {md_filename}
Content:
```markdown
{md_content}
```

--- RAW CODE DIFF MODIFICATIONS ---
File: {analysis.filepath}
Diff:
```diff
{analysis.raw_diff}
```

--- EXTRACTED CODE AST CHANGES ---
{ast_summary}

--- MANDATORY INSTRUCTIONS ---
1. Analyze the raw code changes and the high-level AST modifications.
2. Update the target documentation file so it perfectly matches the new code structure (e.g., class names, function parameters, return types, or architectural flows).
3. Perform a NON-DESTRUCTIVE update: only modify, add, or delete details that directly correspond to the code changes. Do NOT touch, rewrite, or delete surrounding unrelated text, descriptions, or headers.
4. Synchronize or update any visual Mermaid diagrams inside the documentation to match the new code relationships or state flows, adhering strictly to the Mermaid standards (e.g., wrap node labels containing special characters in double quotes).
5. Keep formatting intact. Return ONLY the complete, updated markdown content. Do not include any introductory remarks, conversational preambles, or markdown fences wrap outside the file itself.
"""
    return prompt

def execute_llm_update(
    config: DocuFlowConfig,
    prompt: str
) -> Tuple[Optional[str], str]:
    """
    Executes the LLM request using the active configuration provider (Gemini or OpenAI).
    Returns a tuple of (updated_markdown_content, error_message).
    """
    provider = config.ai.provider.lower()
    model_name = config.ai.model
    temp = config.ai.temperature
    max_t = config.ai.max_tokens

    if provider == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None, "GEMINI_API_KEY environment variable is not set."
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    "temperature": temp,
                    "max_output_tokens": max_t
                }
            )
            response = model.generate_content(prompt)
            content = response.text.strip()
            
            # Strip outer markdown fences if returned
            if content.startswith("```markdown"):
                content = content[11:]
                if content.endswith("```"):
                    content = content[:-3]
            elif content.startswith("```") and content.endswith("```"):
                content = content[3:-3]
                
            return content.strip(), ""
        except Exception as e:
            return None, f"Gemini API call failed: {e}"

    elif provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None, "OPENAI_API_KEY environment variable is not set."
        try:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temp,
                max_tokens=max_t
            )
            content = response.choices[0].message.content.strip()
            
            # Strip outer markdown fences if returned
            if content.startswith("```markdown"):
                content = content[11:]
                if content.endswith("```"):
                    content = content[:-3]
            elif content.startswith("```") and content.endswith("```"):
                content = content[3:-3]
                
            return content.strip(), ""
        except Exception as e:
            return None, f"OpenAI API call failed: {e}"

    return None, f"Unsupported AI provider: {provider}"
