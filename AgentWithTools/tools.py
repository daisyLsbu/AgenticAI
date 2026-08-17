"""
Example tools the agent can call - this is what turns it from a pure chat
agent into a tool-using one.

Each tool has two parts:
  1. A JSON schema (in TOOL_SCHEMAS) describing its name, purpose, and
     parameters - this is what the *model* reads to decide when and how
     to call it.
  2. A Python function (in AVAILABLE_FUNCTIONS) that actually runs locally
     when the model calls it - this never touches the network or needs
     any API key, it's just regular Python.

To add your own tool: write the function, add its schema to TOOL_SCHEMAS,
and map its name to the function in AVAILABLE_FUNCTIONS. That's the whole
pattern.
"""

from __future__ import annotations

import ast
import json
import operator
from datetime import datetime
from pathlib import Path

# File tools are restricted to this folder only - the model can never read
# or write anything outside it, no matter what it's asked to do.
WORKSPACE_DIR = Path(__file__).parent / "workspace"
WORKSPACE_DIR.mkdir(exist_ok=True)


def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def _safe_eval(node: ast.AST):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("unsupported expression")


def calculate(expression: str) -> str:
    """Safely evaluate basic arithmetic (+ - * / ** %) - no eval(), no arbitrary code."""
    try:
        tree = ast.parse(expression, mode="eval")
        return str(_safe_eval(tree.body))
    except Exception as e:
        return f"error: could not evaluate '{expression}': {e}"


def list_workspace_files() -> str:
    files = sorted(p.name for p in WORKSPACE_DIR.iterdir() if p.is_file())
    return json.dumps(files) if files else "no files in workspace/ yet"


def read_workspace_file(filename: str) -> str:
    # Resolve and confirm the result is still inside WORKSPACE_DIR, so
    # something like "../../secrets.txt" can't escape the sandbox.
    path = (WORKSPACE_DIR / filename).resolve()
    if WORKSPACE_DIR.resolve() not in path.parents:
        return "error: access outside workspace/ is not allowed"
    if not path.exists() or not path.is_file():
        return f"error: '{filename}' not found in workspace/"
    return path.read_text(encoding="utf-8", errors="replace")[:4000]  # cap size fed back to the model


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current local date and time.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a basic arithmetic expression, e.g. '12 * (3 + 4)'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "The arithmetic expression to evaluate"}
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_workspace_files",
            "description": "List the files available in the agent's local workspace/ folder.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_workspace_file",
            "description": "Read the text contents of a file in the agent's workspace/ folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "File name inside workspace/"}
                },
                "required": ["filename"],
            },
        },
    },
]

AVAILABLE_FUNCTIONS = {
    "get_current_time": lambda **_: get_current_time(),
    "calculate": lambda expression, **_: calculate(expression),
    "list_workspace_files": lambda **_: list_workspace_files(),
    "read_workspace_file": lambda filename, **_: read_workspace_file(filename),
}
