import os
from pathlib import Path
import re
from typing import Optional, List

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

# Mock for `formatResponse.createPrettyPatch`: Simplifies to just returning new content indication.
# Original generates a diff string for display.
def create_pretty_patch_mock(rel_path: str, original_content: str, new_content: str) -> Optional[str]:
    """
    STUB: Mocks formatResponse.createPrettyPatch.
    In a real scenario, this would generate a unified diff.
    For this stub, it returns `new_content` if there's a change, else None.
    """
    if original_content != new_content:
        # In a real tool, this would be a unified diff string.
        # For simplicity, we just return a non-None value to indicate change.
        return "Changes detected (diff content omitted in this stub)."
    return None

# Mock for `escapeRegExp`: Re-implementing the utility function.
def escape_reg_exp_mock(input_string: str) -> str:
    """
    Escapes special regex characters in a string.
    Mocks the escapeRegExp function from TypeScript.
    """
    return re.sub(r'[.*+?^${}()|[\]\\]', r'\\\g<0>', input_string)

# --- Pydantic BaseModel for Tool Parameters ---

class SearchAndReplaceToolParams(BaseModel):
    """Parameters for the search_and_replace tool."""
    path: str = Field(
        ...,
        description=(
            "The relative path to the file on which to perform the search and replace operation. "
            "Example: `src/utils/string_helpers.py`."
        ),
    )
    search: str = Field(
        ...,
        description=(
            "The string or regex pattern to search for within the file content. "
            "If `use_regex` is true, this is treated as a regex pattern; otherwise, it's a literal string."
        ),
    )
    replace: str = Field(
        ...,
        description=(
            "The string to replace the matched `search` pattern with. "
            "Supports backreferences (`\\1`, `\\2`, etc.) if `use_regex` is true."
        ),
    )
    use_regex: Optional[bool] = Field(
        False,
        description=(
            "Boolean flag indicating whether the `search` parameter should be treated as a regular expression. "
            "Defaults to `false` (literal string search)."
        ),
    )
    ignore_case: Optional[bool] = Field(
        False,
        description=(
            "Boolean flag indicating whether the search should be case-insensitive. "
            "Defaults to `false` (case-sensitive)."
        ),
    )
    start_line: Optional[int] = Field(
        None,
        description=(
            "Optional. The 1-based starting line number for the search and replace operation. "
            "If provided, the operation will only apply to lines from this number onwards. "
            "Useful for restricting changes to a specific section of the file."
        ),
    )
    end_line: Optional[int] = Field(
        None,
        description=(
            "Optional. The 1-based ending line number for the search and replace operation. "
            "If provided, the operation will only apply to lines up to this number (inclusive). "
            "Useful for restricting changes to a specific section of the file."
        ),
    )

# --- Python Tool Logic ---

def search_and_replace_function(
    path: str,
    search: str,
    replace: str,
    use_regex: Optional[bool] = False,
    ignore_case: Optional[bool] = False,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
) -> str:
    """
    Performs search and replace operations on a specified file.

    This tool allows for programmatic modification of file content, supporting
    both literal string and regular expression searches, with optional case-insensitivity
    and line-range restrictions.

    Args:
        path (str): The relative path to the file to modify.
        search (str): The string or regex pattern to search for.
        replace (str): The string to replace matches with.
        use_regex (bool, optional): If `True`, `search` is treated as a regex. Defaults to `False`.
        ignore_case (bool, optional): If `True`, the search is case-insensitive. Defaults to `False`.
        start_line (int, optional): 1-based starting line number for the operation.
        end_line (int, optional): 1-based ending line number for the operation.

    Returns:
        str: A message indicating the success or failure of the operation,
             including details if an error occurred or no changes were made.
    """
    current_working_dir = os.getcwd()
    absolute_path = Path(current_working_dir) / path
    absolute_path = str(absolute_path.resolve()) # Resolve to an absolute path

    # All UI/interaction/context-specific logic removed.
    # No `cline.*` context objects (e.g., `cline.diffViewProvider`, `cline.ask`, `cline.say`,\
    # `cline.consecutiveMistakeCount`, `cline.recordToolError`, `cline.rooIgnoreController`,\
    # `cline.rooProtectedController`, `cline.fileContextTracker`, `TelemetryService`).
    # No `block.partial` handling.
    # No `delay` calls.

    # 1. Check if file exists
    if not file_exists_at_path_mock(absolute_path):
        return f"Error: File does not exist at path: \'{path}\' ({absolute_path}). Please verify the file path and try again."

    # 2. Read file content
    try:
        with open(absolute_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
    except Exception as e:
        return f"Error: Failed to read file \'{path}\' ({absolute_path}). Details: {e}"

    # 3. Prepare search pattern
    flags = re.IGNORECASE if ignore_case else 0
    if not use_regex:
        # Escape special regex characters if not using regex mode
        search_pattern = re.compile(escape_reg_exp_mock(search), flags)
    else:
        try:
            search_pattern = re.compile(search, flags)
        except re.error as e:
            return f"Error: Invalid regex pattern provided: \'{search}\'. Details: {e}"

    new_content: str

    if start_line is not None or end_line is not None:
        # Handle line-specific replacement
        lines = file_content.splitlines(keepends=True) # Keep newlines for accurate reconstruction

        # Adjust 1-based line numbers to 0-based indices
        # If start_line is 1, it means index 0. If None, start from beginning.
        start_idx = (start_line - 1) if start_line is not None else 0
        # If end_line is 1, it means index 0. If None, go to end.
        end_idx = (end_line - 1) if end_line is not None else (len(lines) - 1)

        # Ensure indices are within valid bounds
        start_idx = max(0, min(start_idx, len(lines)))
        end_idx = max(-1, min(end_idx, len(lines) - 1)) # -1 if lines is empty, or for slice logic

        if start_idx > end_idx and start_line is not None and end_line is not None:
             return f"Error: Invalid line range provided. start_line ({start_line}) is greater than end_line ({end_line})."

        # Extract content of the target section
        # slice(start, end+1) for inclusive end_idx
        target_lines = lines[start_idx : end_idx + 1]
        target_content = "".join(target_lines)

        # Perform replacement on the target section
        modified_content_in_section = search_pattern.sub(replace, target_content)

        # Reconstruct the full content
        # Lines before the target section
        before_lines = lines[0:start_idx]
        # Lines after the target section
        after_lines = lines[end_idx + 1:]

        new_content = "".join(before_lines) + modified_content_in_section + "".join(after_lines)

    else:
        # Global replacement
        new_content = search_pattern.sub(replace, file_content)

    # 4. Compare and write if changed
    if new_content == file_content:
        return f"No changes needed for \'{path}\'. Content already matches after search and replace."

    try:
        with open(absolute_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    except Exception as e:
        return f"Error: Failed to write changes to file \'{path}\' ({absolute_path}) after search and replace. Details: {e}"

    # Simulate success message
    # The original tool had `pushToolWriteResult` which provided a formatted message.
    # We will simulate a simple success message here.
    return f"Successfully performed search and replace on file: \'{path}\'."

# --- FunctionTool Instantiation ---

search_and_replace_tool = FunctionTool.from_defaults(
    fn=search_and_replace_function,
    name="search_and_replace",
    description="""
## search_and_replace
Description: Use this tool to find and replace specific text strings or patterns (using regex) within a file. It's suitable for targeted replacements across multiple locations within the file. Supports literal text and regex patterns, case sensitivity options, and optional line ranges. Shows a diff preview before applying changes.

Required Parameters:
- path: The path of the file to modify (relative to the current workspace directory /Users/zhaoxuefeng/GitHub/test_obsidian_work1)
- search: The text or pattern to search for
- replace: The text to replace matches with

Optional Parameters:
- start_line: Starting line number for restricted replacement (1-based)
- end_line: Ending line number for restricted replacement (1-based)
- use_regex: Set to "true" to treat search as a regex pattern (default: false)
- ignore_case: Set to "true" to ignore case when matching (default: false)

Notes:
- When use_regex is true, the search parameter is treated as a regular expression pattern
- When ignore_case is true, the search is case-insensitive regardless of regex mode

Examples:

1. Simple text replacement:
<search_and_replace>
<path>example.ts</path>
<search>oldText</search>
<replace>newText</replace>
</search_and_replace>

2. Case-insensitive regex pattern:
<search_and_replace>
<path>example.ts</path>
<search>oldw+</search>
<replace>new$&</replace>
<use_regex>true</use_regex>
<ignore_case>true</ignore_case>
</search_and_replace>
""",
    fn_schema=SearchAndReplaceToolParams,
)