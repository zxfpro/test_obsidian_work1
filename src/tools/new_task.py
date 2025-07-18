import os
import re
from typing import Optional
from pydantic import BaseModel, Field
from llama_index.core.tools import FunctionTool

# Define a placeholder for external service/complex dependency
# In a real scenario, this would involve integrating with the actual mode management system.
class MockMode:
    def __init__(self, name: str, slug: str):
        self.name = name
        self.slug = slug

def get_mode_by_slug_stub(mode_slug: str, custom_modes: Optional[list] = None) -> Optional[MockMode]:
    """
    Stub for getModeBySlug.
    Simulates checking if a mode exists. In a real system, this would query
    an external mode management service.
    """
    # Example modes (extend as needed for testing or specific scenarios)
    available_modes = {
        "default": MockMode(name="Default Mode", slug="default"),
        "code_review": MockMode(name="Code Review", slug="code_review"),
        "bug_fix": MockMode(name="Bug Fix", slug="bug_fix"),
        "research": MockMode(name="Research Task", slug="research"),
    }
    if custom_modes:
        for cm in custom_modes:
            available_modes[cm.get("slug", "")] = MockMode(name=cm.get("name", ""), slug=cm.get("slug", ""))

    return available_modes.get(mode_slug)

# Pydantic BaseModel for the tool's input parameters
class NewTaskParams(BaseModel):
    mode: str = Field(..., description="The slug of the mode for the new task (e.g., 'code_review', 'bug_fix', 'research'). This mode must exist within the system.")
    message: str = Field(..., description="The detailed message or description for the new task. This will be the initial prompt for the spawned sub-task.")

# Python tool logic function
def new_task_tool_py(mode: str, message: str) -> str:
    """
    Creates a new sub-task with a given message in a specified mode.

    This tool is used to delegate a sub-problem or a new line of inquiry to a new,
    independent task. The agent calling this tool will pause its execution until
    the spawned sub-task is completed.

    Args:
        mode (str): The slug of the mode for the new task (e.g., 'code_review', 'bug_fix', 'research').
                    This mode must exist within the system.
        message (str): The detailed message or description for the new task. This will be the
                       initial prompt for the spawned sub-task.

    Returns:
        str: A message indicating the success or failure of the task creation.
             Returns a success message like "Successfully created new task in [Mode Name] mode with message: [message]"
             on success, or an error message if the mode is invalid or task creation fails.

    Example:
        To create a new task for code review:
        {"tool_code": "new_task_tool_py", "mode": "code_review", "message": "Review the newly added authentication module for security vulnerabilities."}
    """
    # Simulate un-escaping one level of backslashes for hierarchical subtasks.
    # In the original TS, this was `message.replace(/\\\\\\\\@/g, "\\\\@")`
    # Python equivalent for `\\\\@` (literal `\\@`) is `\\\\@` in a regex string,
    # and the replacement `\\@` (literal `@`) is `\\@`.
    unescaped_message = re.sub(r"\\\\@", r"\\@", message)

    # Simulate mode verification
    # In a real system, this would interact with the mode management.
    target_mode = get_mode_by_slug_stub(mode)
    if not target_mode:
        return f"Error: Invalid mode '{mode}'. Please provide a valid mode slug."

    # Simulate the creation of a new task and switching context.
    # In the actual system, this would involve complex state management and
    # potentially spawning a new process or thread for the sub-task.
    # For this FunctionTool, we only report the *intention* and *result*
    # as if the external system handled it.
    try:
        # Simulate approval and actual task spawning.
        # Here we assume approval is always granted for the purpose of the tool.
        # The actual task spawning logic is external to this tool.
        # The agent framework will handle the pausing/resuming.

        # Simulate delay for mode change/task initialization
        # await delay(500) # This is removed as FunctionTools are synchronous.

        # Simulate success
        return f"Successfully created new task in {target_mode.name} mode with message: {unescaped_message}"
    except Exception as e:
        # Simulate error handling
        return f"Error creating new task: {str(e)}"

# FunctionTool instantiation
new_task_function_tool = FunctionTool.from_defaults(
    fn=new_task_tool_py,
    name="newTask",
    description="""
## new_task
Description: This will let you create a new task instance in the chosen mode using your provided message.

Parameters:
- mode: (required) The slug of the mode to start the new task in (e.g., "code", "debug", "architect").
- message: (required) The initial user message or instructions for this new task.

Usage:
<new_task>
<mode>your-mode-slug-here</mode>
<message>Your initial instructions here</message>
</new_task>

Example:
<new_task>
<mode>code</mode>
<message>Implement a new feature for the application.</message>
</new_task>

""", 
    fn_schema=NewTaskParams,
)