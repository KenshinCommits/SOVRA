import os
import json
from pathlib import Path
import uuid
import docx
import openpyxl
from pptx import Presentation
from backend.tools.registry import Tool, registry
from backend.rag.retriever import Retriever
from backend.sandbox.executor import SandboxExecutor
from backend.tools.vision import exec_analyze_engineering_drawing
from backend.tools.tabular import exec_analyze_tabular_data

sandbox = SandboxExecutor()

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

ARTIFACTS_DIR = WORKSPACE_ROOT / "backend" / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def exec_sandboxed_code(code: str) -> str:
    result = sandbox.execute(code)
    return json.dumps(result, indent=2)

def exec_generate_docx(content: str, filename: str) -> str:
    if ".." in filename or "/" in filename:
        return "Error: Invalid filename. Path traversal is not allowed."
    if not filename.endswith(".docx"):
        filename += ".docx"
    target_path = ARTIFACTS_DIR / filename
    try:
        doc = docx.Document()
        doc.add_paragraph(content)
        doc.save(str(target_path))
        return f"Success: DOCX generated at {target_path}"
    except Exception as e:
        return f"Error generating DOCX: {str(e)}"

def exec_generate_xlsx(data_json: str, filename: str) -> str:
    """data_json should be a json string of list of lists (rows)"""
    if ".." in filename or "/" in filename:
        return "Error: Invalid filename. Path traversal is not allowed."
    if not filename.endswith(".xlsx"):
        filename += ".xlsx"
    target_path = ARTIFACTS_DIR / filename
    try:
        data = json.loads(data_json)
        wb = openpyxl.Workbook()
        ws = wb.active
        for row in data:
            if isinstance(row, list):
                ws.append(row)
            elif isinstance(row, dict):
                ws.append(list(row.values()))
        wb.save(str(target_path))
        return f"Success: XLSX generated at {target_path}"
    except json.JSONDecodeError:
        return "Error: Invalid JSON data provided for XLSX generation."
    except Exception as e:
        return f"Error generating XLSX: {str(e)}"

def exec_generate_pptx(content_json: str, filename: str) -> str:
    """content_json should be a json string of list of dicts with 'title' and 'content'"""
    if ".." in filename or "/" in filename:
        return "Error: Invalid filename. Path traversal is not allowed."
    if not filename.endswith(".pptx"):
        filename += ".pptx"
    target_path = ARTIFACTS_DIR / filename
    try:
        slides_data = json.loads(content_json)
        prs = Presentation()
        title_slide_layout = prs.slide_layouts[0]
        bullet_slide_layout = prs.slide_layouts[1]
        
        for slide_data in slides_data:
            if isinstance(slide_data, dict):
                title = slide_data.get("title", "Slide Title")
                content = slide_data.get("content", "")
                
                # Use bullet slide for everything after first slide
                slide = prs.slides.add_slide(bullet_slide_layout)
                shapes = slide.shapes
                title_shape = shapes.title
                body_shape = shapes.placeholders[1]
                
                title_shape.text = title
                tf = body_shape.text_frame
                tf.text = content
        
        prs.save(str(target_path))
        return f"Success: PPTX generated at {target_path}"
    except json.JSONDecodeError:
        return "Error: Invalid JSON data provided for PPTX generation."
    except Exception as e:
        return f"Error generating PPTX: {str(e)}"

# Register new tools
registry.register(Tool(
    name="execute_sandboxed_code",
    description="Execute Python code securely in a Docker sandbox. Use this to calculate things or run scripts safely. The code must print its final answer or result so you can observe it in stdout.",
    input_schema={
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "The Python code to execute. It must be valid Python 3."}
        },
        "required": ["code"]
    },
    permission="execute",
    execute_method=exec_sandboxed_code
))

registry.register(Tool(
    name="generate_docx",
    description="Generate a Word document (DOCX) artifact.",
    input_schema={
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "The text content of the document."},
            "filename": {"type": "string", "description": "The filename (e.g. report.docx). No paths allowed."}
        },
        "required": ["content", "filename"]
    },
    permission="execute",
    execute_method=exec_generate_docx
))

registry.register(Tool(
    name="generate_xlsx",
    description="Generate an Excel spreadsheet (XLSX) artifact.",
    input_schema={
        "type": "object",
        "properties": {
            "data_json": {"type": "string", "description": "A JSON string of a list of lists representing rows (e.g. '[[\"Header1\", \"Header2\"], [\"Val1\", \"Val2\"]]')."},
            "filename": {"type": "string", "description": "The filename (e.g. data.xlsx). No paths allowed."}
        },
        "required": ["data_json", "filename"]
    },
    permission="execute",
    execute_method=exec_generate_xlsx
))

registry.register(Tool(
    name="generate_pptx",
    description="Generate a PowerPoint presentation (PPTX) artifact.",
    input_schema={
        "type": "object",
        "properties": {
            "content_json": {"type": "string", "description": "A JSON string of a list of dictionaries with 'title' and 'content' keys (e.g. '[{\"title\": \"Slide 1\", \"content\": \"Text\"}]')."},
            "filename": {"type": "string", "description": "The filename (e.g. presentation.pptx). No paths allowed."}
        },
        "required": ["content_json", "filename"]
    },
    permission="execute",
    execute_method=exec_generate_pptx
))

registry.register(Tool(
    name="analyze_engineering_drawing",
    description="Inspect an engineering drawing, P&ID diagram, or equipment schematic image using a local vision model. Extracts equipment tags, valves, instrument loops, headers, and notes strictly from visual evidence. Does not invent unconfirmed conclusions.",
    input_schema={
        "type": "object",
        "properties": {
            "image_path": {"type": "string", "description": "Path to the image file (e.g. data/pid_cooling_loop.png)."},
            "focus_query": {"type": "string", "description": "Optional focus query or question about the schematic."}
        },
        "required": ["image_path"]
    },
    permission="read",
    execute_method=exec_analyze_engineering_drawing
))

registry.register(Tool(
    name="analyze_tabular_data",
    description="Deterministically calculate statistics, averages, and threshold violations on CSV or XLSX telemetry datasets without mental arithmetic hallucinations.",
    input_schema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to CSV or XLSX file (e.g. data/vibration_telemetry.csv)."},
            "threshold_col": {"type": "string", "description": "Optional column name to audit against a threshold limit (e.g. vibration_rms_mms)."},
            "threshold_val": {"type": "number", "description": "Optional numeric threshold limit (e.g. 4.5)."}
        },
        "required": ["file_path"]
    },
    permission="read",
    execute_method=exec_analyze_tabular_data
))
