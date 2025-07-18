import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field
from llama_index.core.tools import FunctionTool

# --- Helper Stubs and Mocks (as per protocol) ---

# Mock for `getReadablePath`: Re-using previous mock.
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

# Mock for `fileExistsAtPath`: Re-using previous mock.
def file_exists_at_path_mock(abs_path: str) -> bool:
    """Mocks fileExistsAtPath, using Path.exists()."""
    return Path(abs_path).exists()

# Simplified `insertGroups` function:
# This simulates the behavior of inserting content into a list of lines.
# It handles negative line numbers as insertion at the beginning/end relative to content length.
def insert_groups_mock(original_lines: List[str], insert_specs: List[dict]) -> List[str]:
    """
    STUB: Simulates the `insertGroups` function.
    Inserts content into a list of lines at specified indices.

    Args:
        original_lines (List[str]): The original content split into lines.
        insert_specs (List[dict]): A list of dictionaries, each with:
            - `index` (int): The 0-based index before which to insert.
            - `elements` (List[str]): The lines to insert.

    Returns:
        List[str]: The updated list of lines.

    Note: This simplified version does not handle complex merging or boundary conditions
    as robustly as a production-grade diff/patch library might.
    """
    updated_lines = list(original_lines) # Create a copy to modify

    # Process specs from end to beginning to avoid index shifting issues
    # For a single insert as in the original TS tool, order doesn't strictly matter here.
    for spec in sorted(insert_specs, key=lambda x: x['index'], reverse=True):
        index = spec['index']
        elements = spec['elements']

        # Adjust index for negative values (from end) or out-of-bounds (clamp to end)
        if index < 0:
            index = max(0, len(updated_lines) + index + 1) # python list.insert uses index to mean "before this index"
        elif index > len(updated_lines):
            index = len(updated_lines) # Append to end

        # Perform the insertion
        # `list.insert()` shifts elements, so insert each element one by one in reverse order
        # or use slicing for better performance if inserting many:
        # updated_lines[index:index] = elements
        
        # To match the original behavior of `insertGroups` (which appears to be inserting *before* the given index)
        # if line 0, insert at beginning. if line 1, insert after line 0.
        # TS `insertGroups` uses index 0 for before first line, 1 for before second line etc.
        # This translates directly to Python list slicing: `list[index:index] = new_elements`
        
        updated_lines[index:index] = elements
        
    return updated_lines


# --- Pydantic BaseModel for Tool Parameters ---

class InsertContentToolParams(BaseModel):
    """Parameters for the insert_content tool."""
    path: str = Field(
        ...,
        description=(
            "The relative path to the file where content should be inserted. "
            "If the file does not exist, it will be created. "
            "Example: `src/new_feature.ts`."
        ),
    )
    line: int = Field(
        ...,
        description=(
            "The 1-based line number before which to insert the content. "
            "For example, `line=1` inserts at the beginning of the file. "
            "`line=0` or `line=len(file_lines) + 1` can be used to append to the end. "
            "This parameter is crucial for precise insertion."
        ),
    )
    content: str = Field(
        ...,
        description=(
            "The multi-line string content to be inserted into the file. "
            "Newlines within this string will be preserved."
        ),
    )

# --- Python Tool Logic ---

def insert_content_function(path: str, line: int, content: str) -> str:
    """
    Inserts provided content into a specified file at a given line number.

    This tool is used to add new lines or blocks of code/text into an existing
    file or to create a new file and insert content into it.

    Args:
        path (str): The relative path to the file where the content will be inserted.
                    If the file does not exist, it will be created.
        line (int): The 1-based line number before which to insert the content.
                    - `line=1` means insert at the beginning of the file.
                    - To append to the end of the file, use a line number greater than
                      the current number of lines in the file (e.g., `len(lines) + 1`).
                      `line=0` will also be treated as inserting at the beginning.
        content (str): The multi-line string content to be inserted.

    Returns:
        str: A message indicating the success or failure of the operation.
             On success, it confirms the file update.
             On failure, it provides details about the error.
    """
    current_working_dir = os.getcwd()
    absolute_path = Path(current_working_dir) / path
    absolute_path = str(absolute_path.resolve()) # Resolve to an absolute path

    # All UI/interaction/context-specific logic removed.
    # No `cline.*` context objects (e.g., `cline.diffViewProvider`, `cline.ask`, `cline.say`,
    # `cline.consecutiveMistakeCount`, `cline.recordToolError`, `cline.rooIgnoreController`,
    # `cline.rooProtectedController`, `cline.fileContextTracker`).
    # No `block.partial` handling.
    # No `delay` calls.

    # Validate line number
    if line < 0:
        return "Error: Invalid line number. Line must be a non-negative integer (1-based for insertion)."

    file_exists = file_exists_at_path_mock(absolute_path)
    file_content: str = ""
    lines: List[str] = []

    if file_exists:
        try:
            with open(absolute_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            lines = file_content.split('\n') # Note: split() removes trailing empty string if content ends with '\n'
        except Exception as e:
            return f"Error: Could not read file '{path}' ({absolute_path}). Details: {e}"
    else:
        # If file doesn't exist, and trying to insert at a line other than 0 or 1 (effectively append/prepend)
        # This implies a new file, and insertion should be at the start.
        if line > 1:
            return f"Error: Cannot insert content at line {line} into a non-existent file. For new files, 'line' must be 1 (to insert at the beginning) or equivalent to append."
        # If file doesn't exist and line is 0 or 1, proceed (lines list is empty).

    # Adjust line number for 0-based indexing for `insert_groups_mock`
    # If line is 1, it means insert before first element (index 0).
    # If line is 0, it also means insert before first element (index 0).
    # If line is 2, means insert before second element (index 1).
    # If line is > len(lines), it means append to end.
    insert_index = max(0, line - 1) # 0-based index for insertion

    # Handle the case where the file exists and the user specifies a line number
    # beyond the current end of the file. This should append.
    if file_exists and insert_index > len(lines):
        insert_index = len(lines) # Insert at the very end

    updated_lines = insert_groups_mock(lines, [
        {
            "index": insert_index,
            "elements": content.split('\n'),
        },
    ])

    # Join lines back with newline characters (preserving original newline style if possible, but default to '\n')
    updated_content = '\n'.join(updated_lines)
    
    # Ensure a trailing newline if original had one and content doesn't break it
    if file_content.endswith('\n') and not updated_content.endswith('\n'):
        updated_content += '\n'
    elif not file_content.endswith('\n') and updated_content.endswith('\n'):
        pass # Fine, new content added a newline
    
    # If the original file did not end with a newline, but the updated_lines
    # result in a newline being appended (e.g., if the inserted content ends with one
    # and it was appended to a line that didn't have one), this logic needs care.
    # The `split('\n')` and `join('\n')` typically handle this consistently.
    
    # Compare before writing to avoid unnecessary file writes
    if file_exists and updated_content == file_content:
        return f"No changes needed for file '{path}'. Content already matches."

    try:
        # Ensure directory exists for new files
        Path(absolute_path).parent.mkdir(parents=True, exist_ok=True)
        with open(absolute_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
    except Exception as e:
        return f"Error: Could not write to file '{path}' ({absolute_path}). Details: {e}"

    return f"Content successfully inserted into file: '{path}'."


# --- FunctionTool Instantiation ---

insert_content_tool = FunctionTool.from_defaults(
    fn=insert_content_function,
    name="insert_content",
    description="""
## insert_content
Description: Use this tool specifically for adding new lines of content into a file without modifying existing content. Specify the line number to insert before, or use line 0 to append to the end. Ideal for adding imports, functions, configuration blocks, log entries, or any multi-line text block.

Parameters:
- path: (required) File path relative to workspace directory /Users/zhaoxuefeng/GitHub/test_obsidian_work1
- line: (required) Line number where content will be inserted (1-based)
	      Use 0 to append at end of file
	      Use any positive number to insert before that line
- content: (required) The content to insert at the specified line

Example for inserting imports at start of file:
<insert_content>
<path>src/utils.ts</path>
<line>1</line>
<content>
// Add imports at start of file
import { sum } from './math';
</content>
</insert_content>

Example for appending to the end of file:
<insert_content>
<path>src/utils.ts</path>
<line>0</line>
<content>
// This is the end of the file
</content>
</insert_content>

""",
    fn_schema=InsertContentToolParams,
)