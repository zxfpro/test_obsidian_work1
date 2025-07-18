import os
import re
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Union
from pathlib import Path

from pydantic import BaseModel, Field
from llama_index.core.tools import FunctionTool

# 假设的辅助函数 (需要根据你的实际情况实现或找到替代库)
# --- START: 辅助函数存根 ---

# 假设的 is_binary_file 函数 (使用 python-magic 库更可靠，这里是简易版本)
def is_binary_file(filepath: Union[str, Path]) -> bool:
    """A simplified check for binary files based on common extensions."""
    filepath_str = str(filepath).lower()
    binary_extensions = ['.exe', '.dll', '.bin', '.obj', '.pyc', '.class', '.jar', '.zip',
                         '.tar', '.gz', '.bz2', '.rar', '.7z', '.iso', '.dmg',
                         '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
                         '.mp3', '.wav', '.ogg', '.flac', '.mp4', '.avi', '.mkv', '.mov',
                         '.pdf', '.docx', '.xlsx', '.pptx'] # PDF, DOCX等在Node.js中可能通过特定库处理
    return any(filepath_str.endswith(ext) for ext in binary_extensions)

# 假设的 get_readable_path (这里直接返回原路径)
def get_readable_path(cwd: str, file_path: str) -> str:
    """Simplistic version: returns the file_path itself."""
    # In a real scenario, this might convert absolute path to relative or shorten it.
    return file_path

# 假设的 extract_text_from_file
def extract_text_from_file(filepath: Union[str, Path]) -> str:
    """Reads content of a text file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Fallback for files that might not be strictly UTF-8
        with open(filepath, 'r', encoding='latin-1') as f:
            return f.read()
    except Exception as e:
        return f"ERROR_READING_FILE: {e}"

# 假设的 count_file_lines
def count_file_lines(filepath: Union[str, Path]) -> int:
    """Counts lines in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except Exception:
        return 0 # Or raise error

# 假设的 read_lines
def read_lines(filepath: Union[str, Path], end_idx: int, start_idx: int = 0) -> str:
    """Reads lines from start_idx (0-based) to end_idx (0-based)."""
    lines = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if start_idx <= i <= end_idx:
                    lines.append(line)
                elif i > end_idx:
                    break
    except Exception:
        pass # Handle errors as needed
    return "".join(lines)

# 假设的 add_line_numbers
def add_line_numbers(content: str, start_line: int = 1) -> str:
    """Adds line numbers to content."""
    lines = content.split('\n')
    numbered_lines = [f"{start_line + i}: {line}" for i, line in enumerate(lines)]
    return '\n'.join(numbered_lines)

# 假设的 parse_source_code_definitions_for_file (复杂，这里只返回一个存根)
def parse_source_code_definitions_for_file(filepath: Union[str, Path], roo_ignore_controller=None) -> Optional[str]:
    """
    Parses code definitions (e.g., function names, class names).
    Requires advanced parsing libraries like tree-sitter or AST parsers.
    For this example, it's a placeholder.
    """
    if str(filepath).endswith(".py"):
        return "<definition><name>example_function</name><type>function</type></definition>"
    return None

# 假设的 get_supported_binary_formats (对应Node.js端的配置)
def get_supported_binary_formats() -> List[str]:
    """List of binary formats that can be text-extracted."""
    return ['.pdf', '.docx', '.xlsx', '.pptx', '.ipynb'] # Example formats

# --- END: 辅助函数存根 ---

# --- 1. 定义工具输入模式 (Schema) ---
class ReadFileParams(BaseModel):
    """Parameters for the read_file tool."""
    # 'args' 优先级高于 'path'，用于多文件和行范围读取。
    # LLM 应该优先生成 XML 格式的 'args'
    args: Optional[str] = Field(
        None,
        description=(
            "An XML string containing one or more <file> elements, each with a <path> and optional <line_range>s. "
            "Example: <files><file><path>src/main.py</path><line_range>1-10</line_range></file><file><path>test/test.py</path></file></files>. "
            "Use <line_range> for specific line excerpts. Multiple files or specific line ranges are more efficient than multiple single-file calls."
        )
    )
    # 'path' and 'start_line', 'end_line' are for legacy single-file usage
    # LLM 应该避免使用这些，优先使用 'args'
    path: Optional[str] = Field(
        None,
        description="DEPRECATED: Use 'args' for file path. The path to the file to read (relative or absolute)."
    )
    start_line: Optional[int] = Field(
        None,
        description="DEPRECATED: Use <line_range> in 'args'. Starting line number (1-based) to read. Requires 'path'."
    )
    end_line: Optional[int] = Field(
        None,
        description="DEPRECATED: Use <line_range> in 'args'. Ending line number (1-based) to read. Requires 'path'."
    )


# --- 2. 实现工具的实际逻辑 ---
def read_file_tool_func(
    args: Optional[str] = None,
    path: Optional[str] = None, # legacy path
    start_line: Optional[int] = None, # legacy start_line
    end_line: Optional[int] = None, # legacy end_line
) -> str:
    """
    Reads content from one or more specified files, optionally within line ranges.
    Prioritizes the 'args' XML parameter for multi-file and range reading.
    Returns file contents in an XML format.
    """
    file_results: List[Dict[str, Any]] = [] # To store individual file results
    file_entries: List[Dict[str, Any]] = [] # Parsed file requests

    # --- Parse file entries ---
    if args:
        try:
            root = ET.fromstring(args)
            for file_elem in root.findall('file'):
                file_path_elem = file_elem.find('path')
                if file_path_elem is None or not file_path_elem.text:
                    continue # Skip if no path
                
                entry_path = file_path_elem.text.strip()
                line_ranges: List[Dict[str, int]] = []
                for lr_elem in file_elem.findall('line_range'):
                    range_str = lr_elem.text.strip() if lr_elem.text else ''
                    match = re.match(r'(\d+)-(\d+)', range_str)
                    if match:
                        start, end = int(match.group(1)), int(match.group(2))
                        if start > 0 and end > 0 and start <= end:
                            line_ranges.append({'start': start, 'end': end})
                        else:
                             file_results.append({
                                'path': entry_path,
                                'error': f"Invalid line range: {range_str}. Start/end must be positive and start <= end."
                             })
                             continue # Skip to next range/file if invalid range
                
                file_entries.append({'path': entry_path, 'line_ranges': line_ranges})

        except ET.ParseError as e:
            return f"<files><error>Failed to parse 'args' XML: {e}</error></files>"
        except Exception as e:
            return f"<files><error>Unexpected error parsing 'args': {e}</error></files>"
    elif path: # Legacy single file fallback
        print("[read_file_tool] Warning: Received legacy 'path' parameter. Consider using 'args' XML structure for better functionality.")
        entry_line_ranges: List[Dict[str, int]] = []
        if start_line is not None and end_line is not None:
            if start_line > 0 and end_line > 0 and start_line <= end_line:
                entry_line_ranges.append({'start': start_line, 'end': end_line})
            else:
                file_results.append({
                    'path': path,
                    'error': f"Invalid legacy line range: start={start_line}, end={end_line}. Must be positive and start <= end."
                })
        file_entries.append({'path': path, 'line_ranges': entry_line_ranges})

    if not file_entries:
        return "<files><error>No valid file paths provided. Use 'args' with <file><path>...</path> or 'path' for legacy.</error></files>"

    # --- Process each file entry ---
    for entry in file_entries:
        rel_path = entry['path']
        line_ranges = entry['line_ranges']
        full_path = Path(rel_path).resolve() # Convert to absolute path

        current_file_result: Dict[str, Any] = {'path': rel_path}

        try:
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {full_path}")

            # Simplified binary file check
            if is_binary_file(full_path):
                # Check if it's a supported binary format for text extraction
                file_extension = full_path.suffix.lower()
                if file_extension not in get_supported_binary_formats():
                    current_file_result['notice'] = "Binary file. Content not extracted."
                    # No content for unsupported binary files
                else:
                    # Attempt text extraction for supported binary formats (needs a real implementation)
                    extracted_content = extract_text_from_file(full_path)
                    current_file_result['content'] = extracted_content
                    current_file_result['lines'] = f"1-{len(extracted_content.splitlines())}"
                    current_file_result['notice'] = f"Content extracted from binary file ({file_extension})."
            else:
                # Handle text files
                total_lines = count_file_lines(full_path)
                
                # If specific line ranges are requested
                if line_ranges:
                    line_contents = []
                    for r in line_ranges:
                        content_slice = read_lines(full_path, r['end'] - 1, r['start'] - 1)
                        # Add line numbers if requested (simulating Node.js behavior)
                        line_contents.append(f"<content lines=\"{r['start']}-{r['end']}\">\n{add_line_numbers(content_slice, r['start'])}\n</content>")
                    current_file_result['content_elements'] = line_contents # Store as list of XML content strings

                # If no specific line ranges, apply default limits (simulating maxReadFileLine)
                else:
                    # Simulate maxReadFileLine = 0 (definitions only) - needs actual parsing
                    # if max_read_file_line == 0: # This would come from a global config / LLM prompt, not tool params directly
                    #     definitions = parse_source_code_definitions_for_file(full_path)
                    #     if definitions:
                    #         current_file_result['definitions'] = definitions
                    #         current_file_result['notice'] = "Only code definitions provided."
                    #     else:
                    #         current_file_result['notice'] = "No code definitions found or language not supported."
                    # else: # Default read or limited lines
                    #     read_limit = 500 # Example limit, usually from a global setting
                    #     if total_lines > read_limit:
                    #         content = read_lines(full_path, read_limit - 1, 0)
                    #         current_file_result['notice'] = f"Showing only {read_limit} of {total_lines} total lines. Use line_range if you need to read more."
                    #         current_file_result['lines'] = f"1-{read_limit}"
                    #     else:
                    #         content = extract_text_from_file(full_path)
                    #         current_file_result['lines'] = f"1-{total_lines}"
                    #     current_file_result['content'] = add_line_numbers(content) # Assuming always line numbers for full content

                    # Simplified: just read full content (or within line ranges if specified)
                    if not line_ranges: # Only read full if no line ranges were requested
                        content = extract_text_from_file(full_path)
                        current_file_result['content'] = add_line_numbers(content, 1)
                        current_file_result['lines'] = f"1-{total_lines}"
                        if total_lines == 0:
                            current_file_result['notice'] = "File is empty."

        except FileNotFoundError as e:
            current_file_result['error'] = str(e)
        except Exception as e:
            current_file_result['error'] = f"Error processing file: {e}"

        file_results.append(current_file_result)

    # --- Generate final XML output ---
    xml_output_elements: List[str] = []
    for res in file_results:
        file_elem_parts: List[str] = []
        file_elem_parts.append(f"<path>{res['path']}</path>")

        if 'error' in res:
            file_elem_parts.append(f"<error>{res['error']}</error>")
        elif 'notice' in res:
            file_elem_parts.append(f"<notice>{res['notice']}</notice>")
        
        if 'content_elements' in res: # For multiple line range contents
            file_elem_parts.extend(res['content_elements'])
        elif 'content' in res: # For single content block
            lines_attr = f' lines="{res["lines"]}"' if 'lines' in res else ''
            file_elem_parts.append(f"<content{lines_attr}>\n{res['content']}\n</content>")
        elif 'definitions' in res: # For definitions only mode
            file_elem_parts.append(f"<list_code_definition_names>{res['definitions']}</list_code_definition_names>")

        xml_output_elements.append(f"<file>\n{''.join(file_elem_parts)}\n</file>")
    
    return f"<files>\n{''.join(xml_output_elements)}\n</files>"


# --- 3. 包装成 Llama-Index FunctionTool ---
read_file_tool = FunctionTool.from_defaults(
    fn=read_file_tool_func,
    name="read_file",
    description="""
## read_file
Description: Request to read the contents of one or more files. The tool outputs line-numbered content (e.g. "1 | const x = 1") for easy reference when creating diffs or discussing code. Use line ranges to efficiently read specific portions of large files. Supports text extraction from PDF and DOCX files, but may not handle other binary files properly.

**IMPORTANT: You can read a maximum of 5 files in a single request.** If you need to read more files, use multiple sequential read_file requests.

By specifying line ranges, you can efficiently read specific portions of large files without loading the entire file into memory.
Parameters:
- args: Contains one or more file elements, where each file contains:
  - path: (required) File path (relative to workspace directory /Users/zhaoxuefeng/GitHub/test_obsidian_work1)
  - line_range: (optional) One or more line range elements in format "start-end" (1-based, inclusive)

Usage:
<read_file>
<args>
  <file>
    <path>path/to/file</path>
    <line_range>start-end</line_range>
  </file>
</args>
</read_file>

Examples:

1. Reading a single file:
<read_file>
<args>
  <file>
    <path>src/app.ts</path>
    <line_range>1-1000</line_range>
  </file>
</args>
</read_file>

2. Reading multiple files (within the 5-file limit):
<read_file>
<args>
  <file>
    <path>src/app.ts</path>
    <line_range>1-50</line_range>
    <line_range>100-150</line_range>
  </file>
  <file>
    <path>src/utils.ts</path>
    <line_range>10-20</line_range>
  </file>
</args>
</read_file>

3. Reading an entire file:
<read_file>
<args>
  <file>
    <path>config.json</path>
  </file>
</args>
</read_file>

IMPORTANT: You MUST use this Efficient Reading Strategy:
- You MUST read all related files and implementations together in a single operation (up to 5 files at once)
- You MUST obtain all necessary context before proceeding with changes
- You MUST use line ranges to read specific portions of large files, rather than reading entire files when not needed
- You MUST combine adjacent line ranges (<10 lines apart)
- You MUST use multiple ranges for content separated by >10 lines
- You MUST include sufficient line context for planned modifications while keeping ranges minimal

- When you need to read more than 5 files, prioritize the most critical files first, then use subsequent read_file requests for additional files
""",
    fn_schema=ReadFileParams,
)

# 注意：`read_file_tool` 的实际行为将取决于你实现的辅助函数
# (如 `is_binary_file`, `extract_text_from_file`, `parse_source_code_definitions_for_file` 等)。
# 上面的辅助函数都是简化或存根，你需要根据你的需求来实现它们。