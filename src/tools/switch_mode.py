import json
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field
from llama_index.core.tools import FunctionTool

# --- Helper Stubs and Mocks (as per protocol) ---

# Mock for `formatResponse.toolError`: Re-using previous simple mock.
def format_tool_error_mock(message: str) -> str:
    """Mocks formatResponse.toolError."""
    return f"Error: {message}"

# Mock for `cline.sayAndCreateMissingParamError`: Replaces specific error messages.
def say_and_create_missing_param_error_stub(tool_name: str, param_name: str) -> str:
    """STUB: Mocks cline.sayAndCreateMissingParamError."""
    return f"Error: Missing required parameter '{param_name}' for tool '{tool_name}'."

# Mock for `getModeBySlug` and `defaultModeSlug`:
# This is a **CRITICAL STUB** because the original `getModeBySlug` and `defaultModeSlug`
# are tightly coupled to the application's internal mode management system.
# A Llama-Index FunctionTool cannot directly query or change the application's global state.
#
# This stub will simulate a set of predefined modes.
# In a real scenario, if mode switching is a critical agent capability,
# the modes would need to be defined within the agent's accessible context or
# via another external service it can query.

DEFAULT_MODE_SLUG_STUB = "default"

# Simplified mode definitions for the stub
MODES_STUB = {
    "default": {"name": "Default", "slug": "default"},
    "code_editing": {"name": "Code Editing", "slug": "code_editing"},
    "documentation": {"name": "Documentation", "slug": "documentation"},
    "debugging": {"name": "Debugging", "slug": "debugging"},
    "planning": {"name": "Planning", "slug": "planning"},
}

def get_mode_by_slug_stub(mode_slug: str) -> Optional[Dict[str, str]]:
    """
    STUB: Mocks getModeBySlug.
    Returns a predefined mode definition based on its slug.
    """
    return MODES_STUB.get(mode_slug)

# STUB for `cline.providerRef.deref()?.handleModeSwitch`:
# This is a **CRITICAL STUB**. The original `handleModeSwitch` changes the application's
# operational mode, which is a global state change that a Llama-Index FunctionTool
# cannot directly perform.
#
# This stub will only simulate the action. The actual mode change would need to be
# handled by the external application orchestrating the agent, based on the agent's tool call.
#
# We will use a simple global variable to simulate the current mode for this stub's context.
_current_simulated_mode = DEFAULT_MODE_SLUG_STUB

def handle_mode_switch_stub(mode_slug: str) -> None:
    """
    STUB: Mocks cline.providerRef.deref()?.handleModeSwitch.
    Simulates changing the application's mode.
    """
    global _current_simulated_mode
    if mode_slug in MODES_STUB:
        print(f"STUB: Simulating mode switch to: {mode_slug}")
        _current_simulated_mode = mode_slug
    else:
        print(f"STUB: Attempted to switch to unknown mode: {mode_slug}")

def get_current_simulated_mode_stub() -> str:
    """Helper to get the current simulated mode."""
    return _current_simulated_mode


# --- Pydantic BaseModel for Tool Parameters ---

class SwitchModeToolParams(BaseModel):
    """Parameters for the switch_mode tool."""
    mode_slug: str = Field(
        ...,
        description=(
            "The unique identifier (slug) of the mode to switch to. "
            "Examples: `code_editing`, `documentation`, `debugging`, `planning`."
        ),
    )
    reason: Optional[str] = Field(
        None,
        description=(
            "An optional, brief explanation of why the mode switch is necessary or beneficial. "
            "This helps the user understand the agent's intent. "
            "Example: `reason=\\\"Need to focus on writing new code.\\\"`"
        ),
    )

# --- Python Tool Logic ---

def switch_mode_function(mode_slug: str, reason: Optional[str] = None) -> str:
    """
    Switches the operational mode of the development environment or agent.

    This tool allows the agent to adjust the environment's focus or configuration
    to better suit the current task (e.g., switching to a 'code_editing' mode
    when writing code, or 'documentation' mode when reading docs).

    Args:
        mode_slug (str): The unique identifier (slug) of the mode to switch to.
                         E.g., `code_editing`, `documentation`, `debugging`.
        reason (str, optional): A brief explanation for the mode switch.

    Returns:
        str: A message indicating whether the mode switch was successful,
             if the mode is invalid, or if already in the requested mode.
    """
    # All UI/interaction/context-specific logic removed.
    # No `cline.*` context objects (`cline.consecutiveMistakeCount`, `cline.recordToolError`,\
    # `cline.ask`, `cline.say`, `cline.providerRef`).
    # No `block.partial` handling.
    # No `delay` calls.

    # 1. Verify the mode exists
    target_mode = get_mode_by_slug_stub(mode_slug)
    if not target_mode:
        return format_tool_error_mock(f"Invalid mode: '{mode_slug}'. Available modes are: {', '.join(MODES_STUB.keys())}.")

    # 2. Check if already in requested mode (simulated)
    current_mode_slug = get_current_simulated_mode_stub()
    if current_mode_slug == mode_slug:
        return f"Already in '{target_mode['name']}' mode. No switch needed."

    # 3. Simulate user approval (handled by agent before tool call)
    # The agent orchestrator should handle user approval before invoking this tool.
    # The tool assumes approval if called.

    # 4. Switch the mode using the simulated handler
    handle_mode_switch_stub(mode_slug)

    # 5. Provide success message
    current_mode_name = MODES_STUB.get(current_mode_slug, {}).get("name", current_mode_slug)
    reason_message = f" because: {reason}" if reason else ""
    return (
        f"Successfully switched from '{current_mode_name}' mode to '{target_mode['name']}' mode"
        f"{reason_message}."
    )

# --- FunctionTool Instantiation ---

switch_mode_tool = FunctionTool.from_defaults(
    fn=switch_mode_function,
    name="switch_mode",
    description="""
## switch_mode
Description: Request to switch to a different mode. This tool allows modes to request switching to another mode when needed, such as switching to Code mode to make code changes. The user must approve the mode switch.
Parameters:
- mode_slug: (required) The slug of the mode to switch to (e.g., "code", "ask", "architect")
- reason: (optional) The reason for switching modes
Usage:
<switch_mode>
<mode_slug>Mode slug here</mode_slug>
<reason>Reason for switching here</reason>
</switch_mode>

Example: Requesting to switch to code mode
<switch_mode>
<mode_slug>code</mode_slug>
<reason>Need to make code changes</reason>
</switch_mode>
""",
    fn_schema=SwitchModeToolParams,
)