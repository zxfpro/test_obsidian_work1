import os
from pathlib import Path
import re
from typing import Optional, Tuple, Dict, Any

from pydantic import BaseModel, Field
from llama_index.core.tools import FunctionTool

# --- Helper Stubs and Mocks (as per protocol) ---

# Mock for `unescapeHtmlEntities`: Re-using previous mock.
def unescape_html_entities_mock(text: str) -> str:
    """
    Mocks unescapeHtmlEntities, performing basic HTML entity unescaping.
    """
    return text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&quot;", "\"").replace("&#39;", "'")

# Mock for `formatResponse.toolError` and `formatResponse.rooIgnoreError`: Re-using previous mock.
def format_tool_error_mock(message: str) -> str:
    """Mocks formatResponse.toolError."""
    return f"Error: {message}"

def format_roo_ignore_error_mock(path: str) -> str:
    """Mocks formatResponse.rooIgnoreError."""
    return f"Access to path '{path}' is blocked by .rooignore rules."

# Mock for `Terminal.compressTerminalOutput`: Simple truncation.
def compress_terminal_output_mock(output: str, limit: int) -> str:
    """
    STUB: Mocks Terminal.compressTerminalOutput.
    Simply truncates the output to the given line limit.
    """
    lines = output.splitlines()
    if len(lines) > limit:
        return "\\n".join(lines[:limit]) + f"\\n... (output truncated to {limit} lines)"
    return output

# Mock for `fs.access`: Python's `pathlib` provides `exists()`.
def access_path_mock(path_str: str) -> bool:
    """Mocks fs.access to check if a path exists and is accessible."""
    return Path(path_str).exists()

# STUB for `executeCommand`:
# This is a **CRITICAL STUB** as the original `executeCommand`
# interacts directly with a VS Code terminal, handles shell integration,
# real-time output streaming, user interaction for approval and backgrounding,
# and complex error handling.
#
# The Llama-Index `FunctionTool` must be atomic and non-interactive in its execution.
# Therefore, this stub will:
# 1. Simulate command execution by running the command directly in a subprocess.
# 2. Capture stdout/stderr.
# 3. **NOT** interact with a real terminal or ask for user approval during execution.
#    User approval is handled by the Agent *before* calling the tool.
# 4. **NOT** handle `cline.consecutiveMistakeCount`, `TelemetryService`, `cline.rooIgnoreController`,
#    `cline.providerRef`, `cline.terminalProcess`, `cline.ask`, `cline.say` etc., as these are
#    host-environment specific.
#
# IMPORTANT: This stub runs the command synchronously (or awaits its completion).
# It does not simulate "running in background" or real-time output streams.
# The `terminalOutputLineLimit` will be applied to the final captured output.
#
# TODO: For a more advanced setup, consider using `subprocess.run` with `text=True`,
# `capture_output=True`, and handling `check=False` to get exit codes.
import subprocess

def execute_command_stub(
    command: str,
    custom_cwd: Optional[str] = None,
    terminal_output_line_limit: int = 500
) -> Tuple[bool, str]:
    """
    STUB: Mocks the core logic of `executeCommand` by running a subprocess.
    This does NOT simulate a real interactive terminal, shell integration,
    or real-time output streaming. It runs the command to completion.

    Args:
        command (str): The command string to execute.
        custom_cwd (Optional[str]): The directory to execute the command in.
                                    If None, uses the current working directory of the Python script.
        terminal_output_line_limit (int): Max lines of output to return.

    Returns:
        Tuple[bool, str]: A tuple where the boolean indicates if the command was
                          "rejected" (always False for this stub as no user interaction),
                          and the string is the formatted output or error message.
    """
    working_dir = Path(custom_cwd) if custom_cwd else Path(os.getcwd())

    if not working_dir.exists() or not working_dir.is_dir():
        return False, f"Error: Working directory '{working_dir}' does not exist or is not a directory."

    try:
        # Using subprocess.run to execute the command
        # shell=True is generally discouraged due to security, but often needed for complex commands
        # or commands with pipes/redirections as seen in typical shell usage.
        # For a more secure approach, parse command and arguments manually.
        # For this stub, matching the original JS behavior often implies shell execution.
        result = subprocess.run(
            command,
            cwd=working_dir,
            shell=True,
            capture_output=True,
            text=True, # Capture output as text (decoded using default encoding)
            check=False # Do not raise an exception for non-zero exit codes
        )

        output = result.stdout + result.stderr
        compressed_output = compress_terminal_output_mock(output, terminal_output_line_limit)

        exit_status_message = f"Exit code: {result.returncode}"
        if result.returncode != 0:
            exit_status_message = f"Command execution was not successful, inspect the cause and adjust as needed. {exit_status_message}"

        # Simulate the success message format from the original tool
        return False, f"Command executed within working directory '{working_dir}'. {exit_status_message}\\nOutput:\\n{compressed_output}"

    except FileNotFoundError:
        return False, f"Error: Command '{command.split()[0]}' not found. Ensure it's in your system's PATH."
    except Exception as e:
        return False, f"Error executing command: {e}\\nCommand: '{command}'"


# --- Pydantic BaseModel for Tool Parameters ---

class ExecuteCommandToolParams(BaseModel):
    """Parameters for the execute_command tool."""
    command: str = Field(
        ...,
        description=(
            "The shell command string to execute. This can be any valid command "
            "executable in the operating system's shell (e.g., `ls -l`, `git status`, "
            "`npm install`). The command will be executed as if typed into a terminal."
        ),
    )
    cwd: Optional[str] = Field(
        None,
        description=(
            "Optional. The relative path to the directory where the command should be executed. "
            "If not provided, the command will be executed in the agent's current working directory. "
            "Example: `cwd=\'./backend\'` to run a command in the `backend` subdirectory."
        ),
    )

# --- Python Tool Logic ---

def execute_command_function(command: str, cwd: Optional[str] = None) -> str:
    """
    Executes a shell command in the operating system's terminal.

    This tool allows the agent to interact with the underlying file system,
    run build tools, inspect environment, or perform any operation that
    can be done via a shell command. The output of the command is returned.

    Args:
        command (str): The shell command string to execute (e.g., `ls -l`, `git status`).
        cwd (str, optional): The relative path to the directory where the command
                             should be executed. If omitted, the agent's current
                             working directory will be used.

    Returns:
        str: The output from the executed command, including exit status and
             any error messages. The output may be truncated if it's too long.
    """
    # All UI/interaction/context-specific logic removed.
    # No `cline.*` context objects (e.g., `cline.consecutiveMistakeCount`, `cline.recordToolError`,
    # `cline.ask`, `cline.say`, `cline.rooIgnoreController`, `TelemetryService`, etc.).
    # No `block.partial` handling.
    # No `delay` calls.

    # Unescape HTML entities in the command string, as per original logic.
    processed_command = unescape_html_entities_mock(command)

    # Resolve custom_cwd if provided, relative to the agent's current working directory.
    # Assuming agent's CWD is os.getcwd() for simplicity and isolation.
    resolved_cwd: Optional[str] = None
    if cwd:
        # path.isAbsolute check and path.resolve handling (Python equivalent)
        if Path(cwd).is_absolute():
            resolved_cwd = str(Path(cwd).resolve())
        else:
            resolved_cwd = str((Path(os.getcwd()) / cwd).resolve())
    
    # Execute the command using the stub
    # The `rejected` boolean from the stub is ignored as this tool does not support rejection mid-execution.
    _, result_message = execute_command_stub(
        command=processed_command,
        custom_cwd=resolved_cwd,
        terminal_output_line_limit=500 # Hardcoding the limit for the tool, as `clineProviderState` is removed.
    )

    return result_message

# --- FunctionTool Instantiation ---

execute_command_tool = FunctionTool.from_defaults(
    fn=execute_command_function,
    name="execute_command",
    description="""
## execute_command
Description: Request to execute a CLI command on the system. Use this when you need to perform system operations or run specific commands to accomplish any step in the user's task. You must tailor your command to the user's system and provide a clear explanation of what the command does. For command chaining, use the appropriate chaining syntax for the user's shell. Prefer to execute complex CLI commands over creating executable scripts, as they are more flexible and easier to run. Prefer relative commands and paths that avoid location sensitivity for terminal consistency, e.g: `touch ./testdata/example.file`, `dir ./examples/model1/data/yaml`, or `go test ./cmd/front --config ./cmd/front/config.yml`. If directed by the user, you may open a terminal in a different directory by using the `cwd` parameter.
Parameters:
- command: (required) The CLI command to execute. This should be valid for the current operating system. Ensure the command is properly formatted and does not contain any harmful instructions.
- cwd: (optional) The working directory to execute the command in (default: /Users/zhaoxuefeng/GitHub/test_obsidian_work1)
Usage:
<execute_command>
<command>Your command here</command>
<cwd>Working directory path (optional)</cwd>
</execute_command>

Example: Requesting to execute npm run dev
<execute_command>
<command>npm run dev</command>
</execute_command>

Example: Requesting to execute ls in a specific directory if directed
<execute_command>
<command>ls -la</command>
<cwd>/home/user/projects</cwd>
</execute_command>
""",
    fn_schema=ExecuteCommandToolParams,
)