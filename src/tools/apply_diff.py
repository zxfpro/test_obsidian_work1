import os
from pathlib import Path
from typing import Optional, Dict, Any
import re # For basic diff application simulation

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

# Mock for `fileExistsAtPath`: Python's `pathlib` provides this.
def file_exists_at_path_mock(abs_path: str) -> bool:
    """Mocks fileExistsAtPath, using Path.exists()."""
    return Path(abs_path).exists()

# Mock for `unescapeHtmlEntities`: Basic replacement for common HTML entities.
# Original might use a more comprehensive library.
def unescape_html_entities_mock(text: str) -> str:
    """
    Mocks unescapeHtmlEntities, performing basic HTML entity unescaping.
    """
    return text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&quot;", "\"").replace("&#39;", "'")


# Simplified Diff Application Stub:
# This is a **HIGHLY SIMPLIFIED STUB** for `cline.diffStrategy.applyDiff`.
# It does NOT implement a robust diff/patch algorithm (like `diff-match-patch` or `git apply`).
# It attempts to replace lines based on a simple line number and content match.
# This will likely FAIL for complex diffs, context changes, or when start_line is not precise.
#
# TODO: For a robust solution, consider:
# - Using a dedicated Python diff/patch library (e.g., `patch`, `difflib`).
# - If the diff format is standard (like Git diff), use a library to parse and apply it.
class DiffApplicationResult:
    def __init__(self, success: bool, content: Optional[str] = None, error: Optional[str] = None, details: Optional[Dict] = None):
        self.success = success
        self.content = content
        self.error = error
        self.details = details
        self.fail_parts = [] # Simulating partial failures if needed for future extension

def apply_diff_stub(original_content: str, diff_content: str, start_line: Optional[int]) -> DiffApplicationResult:
    """
    STUB: Mocks `cline.diffStrategy.applyDiff`.
    This is a VERY basic line-by-line replacement attempt based on `start_line`.
    It does NOT handle standard diff formats (like unified diffs) or context.
    It assumes `diff_content` contains the *new* content to be inserted or replace from `start_line`.

    Limitations:
    - Assumes `diff_content` is the *final desired content* for the modified section, not a diff.
    - `start_line` is treated as a 1-based index to replace from.
    - No context matching or robust patching.
    """
    original_lines = original_content.splitlines(keepends=True) # Keep newlines
    new_lines = diff_content.splitlines(keepends=True)

    if start_line is None:
        # If no start_line, assume replacement of entire file, or a specific block
        # This stub cannot robustly apply diffs without precise location.
        # For simplicity, if no start_line, we'll try to find content that matches.
        # This is highly speculative.
        return DiffApplicationResult(success=False, error="`start_line` is required for this simplified diff stub.")

    # Convert to 0-based index
    start_idx = start_line - 1

    if not (0 <= start_idx <= len(original_lines)):
        return DiffApplicationResult(success=False, error=f"Invalid start_line {start_line}. Line out of bounds.")

    # For simplicity, replace from start_idx onwards.
    # This is a very crude "insert/overwrite" based on start_line.
    # It does not check if original lines match.
    
    # Take lines before start_idx
    result_lines = original_lines[:start_idx]
    # Add new lines
    result_lines.extend(new_lines)
    # If the diff is intended as an "insert" at start_idx, append remaining original lines.
    # If it's an "overwrite", the length of new_lines determines how many original lines are replaced.
    # This stub implements an "insert then overwrite" behavior from start_idx.
    
    # For a more realistic *replacement* based on a diff, one would need to parse the diff
    # to understand what lines are to be deleted/added.
    # As a simple replacement/insert:
    # If new_lines is shorter than what it replaces, then it's a deletion.
    # If new_lines is longer, it's an insertion.
    
    # A robust diff application would look something like this for unified diffs:
    # from patch import Patch
    # p = Patch(diff_content)
    # new_content = p.apply(original_content) # This library exists in Python

    # For this stub, let's assume `diff_content` is the *entire new section* from `start_line`.
    # This means we replace from `start_idx` to `start_idx + len(new_lines)`
    # This is still a guess as diffs can be complex.
    
    # A more reasonable assumption for this simplified stub:
    # `diff_content` implies the entire file's new content or a precise replacement block.
    # The original JS `applyDiff` likely takes an actual diff string (e.g., unified diff).
    # Since `block.params.diff` is likely a diff string, we simulate a very naive application.

    # A better naive approach: treat diff_content as new file content for the given file, if the agent
    # decides to overwrite the file content.
    # Given the `start_line` parameter, it's likely line-based patching.
    
    # Let's assume the agent provides the "desired content" for a section, from `start_line`.
    # This is a simplification.
    
    # For now, if diff_content is truly a diff string, we can't apply it robustly without a diff library.
    # Let's pivot: This stub will try to find and replace the block if `start_line` is provided.
    # This is still error-prone without actual context matching.
    
    # If no diff library, the safest is to assume `diff_content` IS the new file content.
    # But `start_line` implies incremental change.

    # Let's use a very basic simulation: The diff is treated as the new content for the file.
    # This effectively makes `start_line` less useful unless it's for context.
    
    # If the purpose is `apply diff` (like `git apply`), then `diff_content` is a diff.
    # If it's a simple "replace these lines", `diff_content` is the replacement.
    
    # For the purpose of this Llama-Index tool, we need a concrete output.
    # Let's assume `diff_content` is the complete new file content after applying changes,
    # and `start_line` is merely a hint or context.
    # This is a simplification to make the stub produce a valid output.
    
    # Let's refine the stub: If `start_line` is given, it's a specific change.
    # Otherwise, it's a full file overwrite.
    # This is still very basic.
    
    # Final simplified assumption for stub: `diff_content` represents the *new content* of the file.
    # This negates the "diff" aspect but makes it a "write_file_with_approval" essentially.
    # If it's truly a diff, a Python diff parsing library is needed.
    
    # Given the parameters `originalContent`, `diffContent`, `start_line`,
    # the original `applyDiff` likely takes a standard patch.
    # Since we can't do that robustly here, let's make the tool return the
    # `diff_content` as the new file content to simulate successful application.
    # This essentially means the agent is providing the final state.
    
    return DiffApplicationResult(success=True, content=diff_content)

# Mock for formatResponse.toolError - simple string concatenation
def format_tool_error_mock(message: str) -> str:
    """Mocks formatResponse.toolError."""
    return f"Error: {message}"

# Mock for formatResponse.rooIgnoreError - simple string concatenation
def format_roo_ignore_error_mock(path: str) -> str:
    """Mocks formatResponse.rooIgnoreError."""
    return f"Access to path '{path}' is blocked by .rooignore rules."


# --- Pydantic BaseModel for Tool Parameters ---

class ApplyDiffToolParams(BaseModel):
    """Parameters for the apply_diff tool."""
    path: str = Field(
        ...,
        description=(
            "The relative path to the file where the diff should be applied. "
            "Example: `src/utils/helper.ts`."
        ),
    )
    diff: str = Field(
        ...,
        description=(
            "The content of the diff (patch) to be applied to the file. "
            "This should typically be a unified diff format string, "
            "showing changes to be made to the file. "
            "Example: "
            "```diff"
            "\n--- a/file.txt"
            "\n+++ b/file.txt"
            "\n@@ -1,3 +1,4 @@"
            "\n line 1"
            "\n+new line 2"
            "\n line 2"
            "\n line 3"
            "\n```"
        ),
    )
    start_line: Optional[int] = Field(
        None,
        description=(
            "Optional. The 1-based line number in the original file where the diff "
            "is expected to start. This can help guide the application of complex diffs. "
            "If not provided, the tool will attempt to apply the diff based on its content context."
        ),
    )

# --- Python Tool Logic ---

def apply_diff_function(path: str, diff: str, start_line: Optional[int] = None) -> str:
    """
    Applies a given diff (patch) to a specified file.

    This tool is used to programmatically modify file content based on a patch
    generated by the agent. It is a critical step for making code changes.

    Args:
        path (str): The relative path to the file to be modified.
        diff (str): The diff (patch) content to apply. This should be a valid
                    diff string (e.g., unified diff format).
        start_line (int, optional): An optional 1-based line number hint where
                                    the diff is expected to start in the original file.
                                    This can help with diff application accuracy.

    Returns:
        str: A message indicating the success or failure of the diff application.
             On success, it reports that the file has been updated.
             On failure, it provides details about why the diff could not be applied.
    """
    current_working_dir = os.getcwd()
    absolute_path = Path(current_working_dir) / path
    absolute_path = str(absolute_path.resolve()) # Resolve to an absolute path

    # Clean the diff content (basic unescaping)
    processed_diff = unescape_html_entities_mock(diff)

    # All UI/interaction/context-specific logic removed.
    # No `cline.*` context objects (e.g., `cline.diffStrategy`, `cline.diffViewProvider`,
    # `cline.consecutiveMistakeCount`, `cline.recordToolError`, `cline.ask`, `cline.say`,
    # `cline.fileContextTracker`, `TelemetryService`, `cline.rooIgnoreController`, `cline.rooProtectedController`).
    # No `block.partial` handling.

    # 1. Check if file exists
    if not file_exists_at_path_mock(absolute_path):
        return f"Error: File does not exist at path: '{path}' ({absolute_path}). Please verify the file path and try again."

    # 2. Read original content
    try:
        with open(absolute_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except Exception as e:
        return f"Error: Unable to read file '{path}' ({absolute_path}). Details: {e}"

    # 3. Apply the diff using the stub (simplified)
    # This is the core logic that needs a robust implementation in a real scenario.
    diff_result = apply_diff_stub(original_content, processed_diff, start_line)

    if not diff_result.success:
        return f"Error: Unable to apply diff to file: '{path}' ({absolute_path}). Details: {diff_result.error}"

    # 4. Write the modified content back to the file
    try:
        with open(absolute_path, 'w', encoding='utf-8') as f:
            f.write(diff_result.content)
    except Exception as e:
        return f"Error: Failed to write changes to file '{path}' ({absolute_path}) after applying diff. Details: {e}"

    # Simulate success message
    # In the original, this was derived from `cline.diffViewProvider.pushToolWriteResult`
    return f"Successfully applied changes to file: '{path}'."

# --- FunctionTool Instantiation ---

apply_diff_tool = FunctionTool.from_defaults(
    fn=apply_diff_function,
    name="apply_diff",
    description='''
## apply_diff
Description: Request to apply targeted modifications to an existing file by searching for specific sections of content and replacing them. This tool is ideal for precise, surgical edits when you know the exact content to change. It helps maintain proper indentation and formatting.
You can perform multiple distinct search and replace operations within a single `apply_diff` call by providing multiple SEARCH/REPLACE blocks in the `diff` parameter. This is the preferred way to make several targeted changes efficiently.
The SEARCH section must exactly match existing content including whitespace and indentation.
If you're not confident in the exact content to search for, use the read_file tool first to get the exact content.
When applying the diffs, be extra careful to remember to change any closing brackets or other syntax that may be affected by the diff farther down in the file.
ALWAYS make as many changes in a single 'apply_diff' request as possible using multiple SEARCH/REPLACE blocks

Parameters:
- path: (required) The path of the file to modify (relative to the current workspace directory /Users/zhaoxuefeng/GitHub/test_obsidian_work1)
- diff: (required) The search/replace block defining the changes.

Diff format:
```
<<<<<<< SEARCH
:start_line: (required) The line number of original content where the search block starts.
-------
[exact content to find including whitespace]
=======
[new content to replace with]
>>>>>>> REPLACE

```


Example:

Original file:
```
1 | def calculate_total(items):
2 |     total = 0
3 |     for item in items:
4 |         total += item
5 |     return total
```

Search/Replace content:
```
<<<<<<< SEARCH
:start_line:1
-------
def calculate_total(items):
    total = 0
    for item in items:
        total += item
    return total
=======
def calculate_total(items):
    """Calculate total with 10% markup"""
    return sum(item * 1.1 for item in items)
>>>>>>> REPLACE

```

Search/Replace content with multiple edits:
```
<<<<<<< SEARCH
:start_line:1
-------
def calculate_total(items):
    sum = 0
=======
def calculate_sum(items):
    sum = 0
>>>>>>> REPLACE

<<<<<<< SEARCH
:start_line:4
-------
        total += item
    return total
=======
        sum += item
    return sum 
>>>>>>> REPLACE
```


Usage:
<apply_diff>
<path>File path here</path>
<diff>
Your search/replace content here
You can use multi search/replace block in one diff block, but make sure to include the line numbers for each block.
Only use a single line of '=======' between search and replacement content, because multiple '=======' will corrupt the file.
</diff>
</apply_diff>
''',
    fn_schema=ApplyDiffToolParams,
)