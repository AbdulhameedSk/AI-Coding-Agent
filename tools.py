"""
tools.py — the agent's hands.

An LLM can't actually DO anything. It only produces text (or structured JSON
like {"tool": "read_file", "path": "README.md"}). These functions are what
turn that request into a real action on your machine, and return a string
result that gets fed back to the model as a "tool_result" message.
"""
import os
import subprocess

# All file tools are sandboxed to this directory so the agent can't
# wander around your whole filesystem.
WORKSPACE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandbox")
os.makedirs(WORKSPACE, exist_ok=True)


def _resolve(path: str) -> str:
    """Resolve a user/agent-supplied path inside the sandbox."""
    full = os.path.abspath(os.path.join(WORKSPACE, path))
    if not full.startswith(os.path.abspath(WORKSPACE)):
        raise ValueError("Path escapes the sandbox workspace.")
    return full


def read_file(path: str) -> str:
    try:
        with open(_resolve(path), "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"ERROR: {e}"


def write_file(path: str, content: str) -> str:
    try:
        full = _resolve(path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Wrote {len(content)} characters to {path}"
    except Exception as e:
        return f"ERROR: {e}"


def list_files(directory: str = ".") -> str:
    try:
        base = _resolve(directory)
        entries = []
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
            for name in files:
                entries.append(os.path.relpath(os.path.join(root, name), base))
        return "\n".join(sorted(entries)) or "(empty)"
    except Exception as e:
        return f"ERROR: {e}"


def run_command(command: str) -> str:
    """Run a shell command inside the sandbox. 30s timeout."""
    try:
        proc = subprocess.run(
            command, shell=True, cwd=WORKSPACE,
            capture_output=True, text=True, timeout=30,
        )
        out = (proc.stdout + proc.stderr).strip()
        return out[:4000] or f"(no output, exit code {proc.returncode})"
    except subprocess.TimeoutExpired:
        return "ERROR: command timed out after 30s"
    except Exception as e:
        return f"ERROR: {e}"


# --- Tool schemas: this is the JSON we hand to the API so Claude knows ---
# --- which tools exist, what they do, and what arguments they take.    ---
TOOL_SCHEMAS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file in the workspace.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Relative path to the file"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Create or overwrite a file in the workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string", "description": "Full file content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "list_files",
        "description": "List all files in a workspace directory.",
        "input_schema": {
            "type": "object",
            "properties": {"directory": {"type": "string", "default": "."}},
        },
    },
    {
        "name": "run_command",
        "description": "Run a shell command inside the workspace directory.",
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
]

# Dispatch table: tool name -> Python function.
def dispatch(name: str, inputs: dict) -> str:
    fn = {"read_file": read_file, "write_file": write_file,
          "list_files": list_files, "run_command": run_command}.get(name)
    if fn is None:
        return f"ERROR: unknown tool {name}"
    return fn(**inputs)
