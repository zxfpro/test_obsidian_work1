from typing import Optional

from pydantic import BaseModel, Field
from llama_index.core.tools import FunctionTool

# --- 模拟 fetchInstructions 函数 ---
# 这是一个存根，你在实际应用中需要实现或集成你的指令获取逻辑
def _mock_fetch_instructions(task_name: str) -> Optional[str]:
    """
    Simulates fetching instructions based on a task name.
    In a real application, this would fetch from a database, API,
    or pre-defined knowledge base.
    """
    instructions_db = {
        "create_file": "To create a file, use the 'write_to_file' tool. Specify the 'path' and 'content'.",
        "read_file_example": "To read a file, use the 'read_file' tool with the 'args' parameter. Example: <files><file><path>myfile.txt</path></file></files>.",
        "debug_issue": "If you encounter an issue, first check logs, then try to isolate the problem. Use 'read_file' to examine relevant code.",
        "default": "No specific instructions found for this task. Please provide a more precise task description."
    }
    return instructions_db.get(task_name.lower(), instructions_db["default"])

# --- 1. 定义工具输入模式 (Schema) ---
class FetchInstructionsParams(BaseModel):
    """Parameters for the fetch_instructions tool."""
    task: str = Field(
        ...,
        description=(
            "The specific task name or query for which to fetch instructions. "
            "Examples: 'create_file', 'read_file_example', 'debug_issue'."
        )
    )

# --- 2. 实现工具的实际逻辑 ---
def fetch_instructions_tool_func(task: str) -> str:
    """
    Fetches detailed instructions or guidance for a given task.

    Args:
        task (str): The specific task name or query for which to fetch instructions.
    Returns:
        str: The fetched instructions, or an error message if the task is not found.
    """
    try:
        # In the original TS, this would be `fetchInstructions(task, { mcpHub, diffStrategy, context })`
        # Here we use our simplified mock function.
        content = _mock_fetch_instructions(task)

        if not content or content == _mock_fetch_instructions("default"): # Check if content is default or empty
            # If the original TS returned formatResponse.toolError for invalid requests, we can do similar
            return f"Error: No specific instructions found for task '{task}'. Please try a different task query."
        
        # The original TS just returns `content` as result.
        return content

    except Exception as e:
        # Simulate handleError
        return f"Error fetching instructions for task '{task}': {e}"

# --- 3. 包装成 Llama-Index FunctionTool ---
fetch_instructions_tool = FunctionTool.from_defaults(
    fn=fetch_instructions_tool_func,
    name="fetch_instructions",
    description="""
## fetch_instructions
Description: Request to fetch instructions to perform a task
Parameters:
- task: (required) The task to get instructions for.  This can take the following values:
  create_mcp_server
  create_mode

Example: Requesting instructions to create an MCP Server

<fetch_instructions>
<task>create_mcp_server</task>
</fetch_instructions>
""",
    fn_schema=FetchInstructionsParams,
)
