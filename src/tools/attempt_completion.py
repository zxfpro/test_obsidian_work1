import json
from typing import Optional, Any, Dict, List, Tuple
from pydantic import BaseModel, Field
from llama_index.core.tools import FunctionTool

# --- Helper Stubs and Mocks (as per protocol) ---

# Mock for `formatResponse.toolResult` and `formatResponse.toolError`
# Re-using previous simple mocks.
def format_tool_error_mock(message: str) -> str:
    """Mocks formatResponse.toolError."""
    return f"Error: {message}"

def format_tool_result_mock(content: str, images: Optional[List[str]] = None) -> str:
    """Mocks formatResponse.toolResult."""
    if images:
        return f"Result: {content}\\n(Note: {len(images)} images were also retrieved, but not directly rendered in this text output.)"
    return f"Result: {content}"

# Mock for `formatResponse.imageBlocks`: Returns empty list as images are not directly handled by FunctionTool
def format_image_blocks_mock(images: Optional[List[str]]) -> List[Dict[str, Any]]:
    """
    STUB: Mocks formatResponse.imageBlocks.
    Since Llama-Index FunctionTool typically returns text, image blocks are not directly supported.
    """
    return []

# STUB for `TelemetryService.instance.captureTaskCompleted`:
# Telemetry is host-specific and should be stripped.
def capture_task_completed_stub(task_id: str):
    """STUB: Mocks TelemetryService.instance.captureTaskCompleted."""
    print(f"STUB: Telemetry captured task {task_id} as completed.")

# STUB for `cline.sayAndCreateMissingParamError`:
# Replaces specific error messages with generic ones.
def say_and_create_missing_param_error_stub(tool_name: str, param_name: str) -> str:
    """STUB: Mocks cline.sayAndCreateMissingParamError."""
    return f"Error: Missing required parameter '{param_name}' for tool '{tool_name}'."


# --- Pydantic BaseModel for Tool Parameters ---

class AttemptCompletionToolParams(BaseModel):
    """Parameters for the attempt_completion tool."""
    result: str = Field(
        ...,
        description=(
            "The final result or summary of the task that the agent has completed. "
            "This should be a comprehensive description of the work done, findings, "
            "or changes made. Example: `result=\\\"Successfully refactored module X. "
            "All tests pass.\\\"`"
        ),
    )
    command: Optional[str] = Field(
        None,
        description=(
            "Optional. A command string that the user is expected to execute after the completion. "
            "This is typically a suggestion for the next step outside the agent's direct control, "
            "e.g., `git push`, `npm run deploy`. If provided, the agent will suggest this to the user."
        ),
    )

# --- Python Tool Logic ---

def attempt_completion_function(result: str, command: Optional[str] = None) -> str:
    """
    Signals that the agent believes it has completed the current task and provides a final result or summary.

    This tool is used to present the outcome of the agent's work to the user.
    It can also suggest a follow-up command for the user to execute manually.

    Args:
        result (str): A detailed summary of the task's outcome, changes made,
                      or information gathered. This is the primary output of the tool.
        command (str, optional): An optional shell command that the agent suggests
                                 the user run as a next step. This command is presented
                                 to the user for manual execution, not executed by the agent.

    Returns:
        str: A formatted string indicating the completion of the task, including
             the result summary and any suggested command.
             If the `result` parameter is missing, an error message is returned.
    """
    # All UI/interaction/context-specific logic removed.
    # No `cline.*` context objects (`cline.consecutiveMistakeCount`, `cline.recordToolError`,
    # `cline.ask`, `cline.say`, `cline.parentTask`, `cline.providerRef`, `cline.lastMessageTs`,
    # `cline.emit`, `cline.getTokenUsage`, `cline.toolUsage`, `cline.userMessageContent`,
    # `askFinishSubTaskApproval`, `toolDescription`).
    # No `block.partial` handling.
    # No `TelemetryService` calls.

    if not result:
        # This check is technically redundant due to Pydantic Field(..., description=...)
        # but kept for explicit clarity matching original logic.
        return say_and_create_missing_param_error_stub("attempt_completion", "result")

    # Simulate task completion actions stripped from host environment
    capture_task_completed_stub("simulated_task_id") # Using a dummy task_id

    response_message = f"Task completed successfully.\\nResult: {result}"
    if command:
        response_message += f"\\nSuggested next command for user: `{command}`"

    # The original tool had complex logic for user approval and feedback loops.
    # For a Llama-Index FunctionTool, the return value is the "tool result".
    # We consolidate the final output into a single string.
    # The agent is responsible for handling the "approval" flow before calling this tool,
    # and for interpreting the final result.

    return format_tool_result_mock(response_message)

# --- FunctionTool Instantiation ---

attempt_completion_tool = FunctionTool.from_defaults(
    fn=attempt_completion_function,
    name="attempt_completion",
    description="""
## attempt_completion
Description: After each tool use, the user will respond with the result of that tool use, i.e. if it succeeded or failed, along with any reasons for failure. Once you've received the results of tool uses and can confirm that the task is complete, use this tool to present the result of your work to the user. The user may respond with feedback if they are not satisfied with the result, which you can use to make improvements and try again.
IMPORTANT NOTE: This tool CANNOT be used until you've confirmed from the user that any previous tool uses were successful. Failure to do so will result in code corruption and system failure. Before using this tool, you must ask yourself in <thinking></thinking> tags if you've confirmed from the user that any previous tool uses were successful. If not, then DO NOT use this tool.
Parameters:
- result: (required) The result of the task. Formulate this result in a way that is final and does not require further input from the user. Don't end your result with questions or offers for further assistance.
Usage:
<attempt_completion>
<result>
Your final result description here
</result>
</attempt_completion>

Example: Requesting to attempt completion with a result
<attempt_completion>
<result>
I've updated the CSS
</result>
</attempt_completion>
""",
    fn_schema=AttemptCompletionToolParams,
)