import os
import json
from pathlib import Path
from backend.tools.registry import Tool, registry
from backend.rag.retriever import Retriever

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
retriever = Retriever()

def _is_safe_path(target_path: str) -> bool:
    """Ensure the path resolves within the WORKSPACE_ROOT and blocks traversal."""
    try:
        # Resolve to absolute path
        abs_path = (WORKSPACE_ROOT / target_path).resolve()
        # Check if it starts with the workspace root
        return str(abs_path).startswith(str(WORKSPACE_ROOT))
    except Exception:
        return False

def exec_knowledge_search(query: str, top_k: int = 3) -> str:
    results = retriever.retrieve_context(query=query, top_k=top_k)
    if not results:
        return "No relevant information found in the knowledge base."
    
    # Format the evidence nicely so the agent can read it
    formatted_results = []
    for r in results:
        filename = r.get("filename", "Unknown")
        page = r.get("page", "N/A")
        text = r.get("text", "")
        score = r.get("score", 0.0)
        formatted_results.append(f"[Source: {filename}, Page: {page}, Score: {score:.2f}]\n{text}\n")

    
    return "\n---\n".join(formatted_results)

def exec_list_project_files(path: str = ".") -> str:
    if not _is_safe_path(path):
        return f"Error: Access denied. Path '{path}' is outside the allowed workspace."
    
    target = (WORKSPACE_ROOT / path).resolve()
    if not target.exists():
        return f"Error: Path '{path}' does not exist."
    if not target.is_dir():
        return f"Error: Path '{path}' is not a directory."
        
    try:
        items = os.listdir(target)
        # Limit to prevent massive outputs
        if len(items) > 100:
            return f"Directory contains {len(items)} items. Showing first 100:\n" + "\n".join(items[:100])
        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

def exec_read_file(path: str) -> str:
    if not _is_safe_path(path):
        return f"Error: Access denied. Path '{path}' is outside the allowed workspace."
        
    target = (WORKSPACE_ROOT / path).resolve()
    if not target.exists():
        return f"Error: File '{path}' does not exist."
    if not target.is_file():
        return f"Error: Path '{path}' is not a file."
        
    try:
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()
            # truncate if extremely large to save context window
            if len(content) > 10000:
                return content[:10000] + "\n...[TRUNCATED for length]"
            return content
    except Exception as e:
        return f"Error reading file: {str(e)}"


# Register Tools
registry.register(Tool(
    name="knowledge_search",
    description="Search the local vector knowledge base for information in indexed SOPs, manuals, and reports.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"},
            "top_k": {"type": "integer", "description": "Number of results to return", "default": 3}
        },
        "required": ["query"]
    },
    permission="read_only",
    execute_method=exec_knowledge_search
))

registry.register(Tool(
    name="list_project_files",
    description="List files and directories in the local project workspace.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative directory path (e.g., '.', 'backend')", "default": "."}
        }
    },
    permission="read_only",
    execute_method=exec_list_project_files
))

registry.register(Tool(
    name="read_file",
    description="Read the contents of a local file in the project workspace.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative path to the file to read"}
        },
        "required": ["path"]
    },
    permission="read_only",
    execute_method=exec_read_file
))
