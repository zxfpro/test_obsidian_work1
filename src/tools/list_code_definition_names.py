import os
from pathlib import Path
from typing import List, Optional, Tuple
import re # For simple pattern matching, as a substitute for tree-sitter for this demo

from pydantic import BaseModel, Field
from llama_index.core.tools import FunctionTool

# --- Helper Stubs and Mocks (as per protocol) ---

# Mock for `getReadablePath`: Already defined in the previous conversion,
# keeping it consistent.
def get_readable_path_mock(base_path: str, target_path: Optional[str]) -> str:
    """
    Mocks the getReadablePath function from TypeScript.
    Returns a user-friendly path relative to the base_path, or an absolute path
    if outside.
    """
    if target_path is None:
        return str(Path(base_path).name)
    
    try:
        relative_path = Path(target_path).relative_to(base_path)
        return str(relative_path)
    except ValueError:
        return str(Path(target_path).absolute())

# Mock for `isPathOutsideWorkspace`: Already defined.
def is_path_outside_workspace_mock(abs_path: str) -> bool:
    """
    Mocks the isPathOutsideWorkspace function from TypeScript.
    Checks if a given absolute path is outside the presumed workspace (current working directory).
    """
    current_cwd = Path(os.getcwd())
    try:
        Path(abs_path).relative_to(current_cwd)
        return False
    except ValueError:
        return True

# Mock for `parseSourceCodeDefinitionsForFile`:
# This is a **SIGNIFICANT SIMPLIFICATION/STUB**.
# The original uses `tree-sitter` for robust code parsing.
# This mock uses simple regex patterns for common definitions in Python and JS/TS.
# It does NOT provide the same accuracy or language-agnostic parsing.
#
# TODO: For a production-ready system, consider integrating a robust code parsing library
# like `tree_sitter` (Python binding) or `pygments` (for basic tokenization)
# or even a dedicated AST parser for specific languages if complexity allows.
def parse_source_code_definitions_for_file_stub(file_path: str) -> Optional[str]:
    """
    STUB: Mocks parseSourceCodeDefinitionsForFile using basic regex.
    This is a highly simplified version that attempts to find function/class/variable
    definitions using common patterns. It is NOT as robust as Tree-sitter.

    Assumes common patterns for Python, JavaScript, TypeScript.
    Ignores `cline.rooIgnoreController` as it's host-specific.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        definitions = []

        # Simple patterns (Python, JS/TS) - these are very basic
        # Python: def func_name(...), class ClassName(...)
        py_patterns = [
            re.compile(r"^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE),
            re.compile(r"^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)(?:\(|:)", re.MULTILINE),
        ]
        # JS/TS: function funcName(...), const/let/var funcName = (...) =>, class ClassName
        js_ts_patterns = [
            re.compile(r"^\s*(?:async\s+)?function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE),
            re.compile(r"^\s*(?:const|let|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:function|\()", re.MULTILINE),
            re.compile(r"^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)(?:\s*{|\s+implements|\s+extends)", re.MULTILINE),
            re.compile(r"^\s*export\s+(?:const|let|var|function|class)\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.MULTILINE)
        ]

        # Combine based on typical file extensions
        file_ext = Path(file_path).suffix
        patterns_to_use = []
        if file_ext == '.py':
            patterns_to_use.extend(py_patterns)
        elif file_ext in ['.js', '.ts', '.jsx', '.tsx']:
            patterns_to_use.extend(js_ts_patterns)
        else: # Try both for generic text files or unknown types
            patterns_to_use.extend(py_patterns)
            patterns_to_use.extend(js_ts_patterns)


        for pattern in patterns_to_use:
            for match in pattern.finditer(content):
                if match.group(1):
                    definitions.append(f"- {match.group(1)}")

        if definitions:
            return f"Definitions found in '{Path(file_path).name}':\n" + "\n".join(definitions)
        else:
            return f"No common code definitions found in '{Path(file_path).name}' using simple patterns."

    except Exception as e:
        return f"Could not read or parse file '{file_path}': {e}"

# Mock for `parseSourceCodeForDefinitionsTopLevel`:
# This is also a **SIGNIFICANT SIMPLIFICATION/STUB**.
# The original would likely traverse directories and use tree-sitter.
# This mock simply lists files and then applies the file-level stub.
#
# TODO: A more robust implementation would recursively find relevant code files
# and apply a proper parser. This current stub is very basic.
def parse_source_code_for_definitions_top_level_stub(directory_path: str) -> str:
    """
    STUB: Mocks parseSourceCodeForDefinitionsTopLevel.
    This is a simplified version that tries to read common code files
    (.py, .js, .ts) in the top level of the given directory and
    applies the definition parsing stub.
    Ignores `cline.rooIgnoreController` as it's host-specific.
    """
    base_path = Path(directory_path)
    if not base_path.is_dir():
        return f"Path '{directory_path}' is not a directory."

    results = []
    found_any_definitions = False
    
    # List only common code files at the top level (non-recursive)
    for item in base_path.iterdir():
        if item.is_file():
            if item.suffix in ['.py', '.js', '.ts', '.jsx', '.tsx']:
                file_result = parse_source_code_definitions_for_file_stub(str(item))
                if file_result and "No common code definitions found" not in file_result:
                    results.append(file_result)
                    found_any_definitions = True
                else:
                    results.append(f"Skipped {item.name} (no definitions or unsupported file type for simple parsing).")

    if not found_any_definitions:
        return f"No code definitions found in the top-level files of '{directory_path}'."
    
    return f"Code definitions in top-level files of '{directory_path}':\n" + "\n\n".join(results)


# --- Pydantic BaseModel for Tool Parameters ---

class ListCodeDefinitionNamesParams(BaseModel):
    """Parameters for the list_code_definition_names tool."""
    path: str = Field(
        ...,
        description=(
            "The relative path to a file or directory for which to list code definitions. "
            "Examples: `src/my_module.py`, `src/utils/`."
        ),
    )

# --- Python Tool Logic ---

def list_code_definition_names_function(path: str) -> str:
    """
    Lists the names of code definitions (e.g., functions, classes, variables)
    found within a specified file or directory.

    This tool helps understand the internal structure and available components
    of code files without reading their full content.

    Args:
        path (str): The relative path to the file or directory.
                    If a file, it parses that file. If a directory, it attempts
                    to parse top-level files within it.

    Returns:
        str: A formatted string listing the detected code definitions,
             or a message indicating if no definitions were found,
             or if the path does not exist/is inaccessible.
    """
    current_working_dir = os.getcwd()
    absolute_path = Path(current_working_dir) / path
    absolute_path = str(absolute_path.resolve()) # Resolve to an absolute path

    # All UI/interaction/context-specific logic removed.
    # No `cline.consecutiveMistakeCount`, `cline.recordToolError`, `pushToolResult`, etc.
    # No `block.partial` handling.
    # `cline.fileContextTracker` is also removed as it's host-specific.

    result: str
    try:
        path_obj = Path(absolute_path)
        if not path_obj.exists():
            result = f"Path '{path}' ({absolute_path}): does not exist."
        elif path_obj.is_file():
            # Use the stub for file parsing
            file_result = parse_source_code_definitions_for_file_stub(absolute_path)
            result = file_result if file_result is not None else "No source code definitions found in file."
        elif path_obj.is_dir():
            # Use the stub for directory parsing
            result = parse_source_code_for_definitions_top_level_stub(absolute_path)
        else:
            result = f"The specified path '{path}' ({absolute_path}) is neither a file nor a directory."
    except Exception as e:
        result = f"An error occurred while processing path '{path}' ({absolute_path}): {e}"

    return result

# --- FunctionTool Instantiation ---

list_code_definition_names_tool = FunctionTool.from_defaults(
    fn=list_code_definition_names_function,
    name="list_code_definition_names",
    description="""
## list_code_definition_names
Description: Request to list definition names (classes, functions, methods, etc.) from source code. This tool can analyze either a single file or all files at the top level of a specified directory. It provides insights into the codebase structure and important constructs, encapsulating high-level concepts and relationships that are crucial for understanding the overall architecture.
Parameters:
- path: (required) The path of the file or directory (relative to the current working directory /Users/zhaoxuefeng/GitHub/test_obsidian_work1) to analyze. When given a directory, it lists definitions from all top-level source files.
Usage:
<list_code_definition_names>
<path>Directory path here</path>
</list_code_definition_names>

Examples:

1. List definitions from a specific file:
<list_code_definition_names>
<path>src/main.ts</path>
</list_code_definition_names>

2. List definitions from all files in a directory:
<list_code_definition_names>
<path>src/</path>
</list_code_definition_names>

""",
    fn_schema=ListCodeDefinitionNamesParams,
)