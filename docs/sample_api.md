# Sample API Reference

This document describes the API entry points for DocuFlow. The primary entry point is defined in `main.py`, which invokes native git helper functions in `git_utils.py` to analyze modified repository paths.

## Sub-Header (Complies with single H1 Rule)

Here is a quick sample of code:

```python
# This code block has python syntax highlighting
def get_status():
    return "ok"
```

The system uses standard JSON-based API keys to authenticate and authorize every CLI request.

## Architecture

```mermaid
graph TD
    Start["Launch (App)"] --> Process[Run Checks (Auto)]
```
