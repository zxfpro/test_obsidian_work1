import os
from pathlib import Path
from typing import List, Tuple, Optional
from pydantic import BaseModel, Field
from llama_index.core.tools import FunctionTool

# --- Helper Stubs and Mocks (as per protocol) ---

# Mock for `getReadablePath`: In a real scenario, this would likely be part of
# a utility library or handled by Path objects directly.
# For this tool, it simply returns the relative path for display.
def get_readable_path_mock(base_path: str, target_path: Optional[str]) -> str:
    """
    Mocks the getReadablePath function from TypeScript.
    Returns a user-friendly path relative to the base_path, or an absolute path
    if outside.
    """
    if target_path is None:
        return str(Path(base_path).name) # Return base folder name
    
    try:
        # Attempt to make target_path relative to base_path
        relative_path = Path(target_path).relative_to(base_path)
        return str(relative_path)
    except ValueError:
        # If target_path is not relative to base_path, return its absolute path
        return str(Path(target_path).absolute())

# Mock for `isPathOutsideWorkspace`: Assumes a simple check for demonstration.
# In a real Llama-Index setup, workspace definition would be external to the tool.
# Here, we assume "workspace" is the current working directory for simplicity.
def is_path_outside_workspace_mock(abs_path: str) -> bool:
    """
    Mocks the isPathOutsideWorkspace function from TypeScript.
    Checks if a given absolute path is outside the presumed workspace (current working directory).
    """
    # This is a simplification. In a real system, the "workspace" concept would be
    # more formally defined and passed or accessed.
    current_cwd = Path(os.getcwd())
    try:
        Path(abs_path).relative_to(current_cwd)
        return False # It's within or identical to the workspace
    except ValueError:
        return True # It's outside

# Mock for `listFiles`: Simulates the file listing behavior.
# This stub does not handle `rooIgnoreController` or `showRooIgnoredFiles`
# as these are considered host-environment specific for the Llama-Index tool.
def list_files_mock(
    absolute_path: str, recursive: bool, limit: int
) -> Tuple[List[str], bool]:
    """
    Mocks the listFiles function from TypeScript.
    Lists files and directories in the given path, optionally recursively, up to a limit.
    Note: This mock does not handle `.rooignore` or similar external ignore patterns.
    """
    all_items = []
    base_path = Path(absolute_path)

    if not base_path.exists():
        return [], False

    if recursive:
        for root, dirs, files in os.walk(base_path):
            for name in dirs:
                item_path = Path(root) / name
                try:
                    all_items.append(str(item_path.relative_to(base_path)))
                except ValueError:
                    # Handle cases where item_path is not relative to base_path (e.g., symlinks)
                    all_items.append(str(item_path.absolute()))
            for name in files:
                item_path = Path(root) / name
                try:
                    all_items.append(str(item_path.relative_to(base_path)))
                except ValueError:
                    all_items.append(str(item_path.absolute()))
    else:
        for item in base_path.iterdir():
            try:
                all_items.append(str(item.relative_to(base_path)))
            except ValueError:
                all_items.append(str(item.absolute()))

    did_hit_limit = len(all_items) > limit
    return all_items[:limit], did_hit_limit

# Mock for `formatResponse.formatFilesList`: Simplifies formatting for Python.
# Original includes `rooIgnoreController`, `showRooIgnoredFiles`, `rooProtectedController`
# which are host-specific and removed from the tool's direct responsibility.
def format_files_list_mock(
    abs_path: str, files: List[str], did_hit_limit: bool
) -> str:
    """
    Mocks the formatResponse.formatFilesList function from TypeScript.
    Formats the list of files for display.
    """
    header = f"Files/directories in '{abs_path}':"
    if not files:
        return f"{header}\n(No items found or allowed to list in this directory.)"

    formatted_files = "\n".join([f"- {item}" for item in files])
    limit_message = "\n(Limit hit, some files may not be shown.)" if did_hit_limit else ""
    return f"{header}\n{formatted_files}{limit_message}"

# --- Pydantic BaseModel for Tool Parameters ---

class ListFilesToolParams(BaseModel):
    """Parameters for the list_files tool."""
    path: Optional[str] = Field(
        None,
        description=(
            "The relative path to the directory to list files from. "
            "If not provided, the current working directory will be used."
        ),
    )
    recursive: Optional[bool] = Field(
        False,
        description=(
            "Boolean flag indicating whether to list files recursively in subdirectories. "
            "Set to true for recursive listing, false otherwise. Defaults to false."
        ),
    )

# --- Python Tool Logic ---

def list_files_function(path: Optional[str] = None, recursive: Optional[bool] = False) -> str:
    """
    Lists files and directories in a specified path.

    This tool is designed to help understand the file structure of the project.
    It can list contents of a directory, optionally including subdirectories.

    Args:
        path (str, optional): The relative path to the directory to list.
                              If omitted, the current working directory is used.
        recursive (bool, optional): If set to `true`, the tool will list files
                                    and directories recursively in all subdirectories.
                                    Defaults to `false` (only lists top-level items).

    Returns:
        str: A formatted string containing the list of files and directories.
             Includes a note if a limit was hit.
    """
    # Assuming the "current working directory" for the tool is os.getcwd()
    # This is a key decoupling from `cline.cwd`
    current_working_dir = os.getcwd()

    absolute_path = Path(current_working_dir) / (path if path is not None else "")
    absolute_path = str(absolute_path.resolve()) # Resolve to an absolute path

    # All UI/interaction/context-specific logic removed.
    # No `cline.consecutiveMistakeCount`, `cline.recordToolError`, `pushToolResult`, etc.
    # No `block.partial` handling.

    # Use mocks for external dependencies
    files, did_hit_limit = list_files_mock(absolute_path, recursive, 200) # Hardcoded limit 200
    
    # Simplified formatting without `rooIgnoreController` etc.
    result = format_files_list_mock(absolute_path, files, did_hit_limit)

    return result

# --- FunctionTool Instantiation ---

list_files_tool = FunctionTool.from_defaults(
    fn=list_files_function,
    name="list_files",
    description="""
## list_files
Description: Request to list files and directories within the specified directory. If recursive is true, it will list all files and directories recursively. If recursive is false or not provided, it will only list the top-level contents. Do not use this tool to confirm the existence of files you may have created, as the user will let you know if the files were created successfully or not.
Parameters:
- path: (required) The path of the directory to list contents for (relative to the current workspace directory /Users/zhaoxuefeng/GitHub/test_obsidian_work1)
- recursive: (optional) Whether to list files recursively. Use true for recursive listing, false or omit for top-level only.
Usage:
<list_files>
<path>Directory path here</path>
<recursive>true or false (optional)</recursive>
</list_files>

Example: Requesting to list all files in the current directory
<list_files>
<path>.</path>
<recursive>false</recursive>
</list_files>

""",
    fn_schema=ListFilesToolParams,
)