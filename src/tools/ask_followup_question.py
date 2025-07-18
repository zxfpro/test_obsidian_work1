import json
from typing import Optional, Any, Dict, List, Union, Tuple
from pydantic import BaseModel, Field
from llama_index.core.tools import FunctionTool

# --- Helper Stubs and Mocks (as per protocol) ---

# Mock for `formatResponse.toolError` and `formatResponse.toolResult`
# Re-using previous simple mocks.
def format_tool_error_mock(message: str) -> str:
    """Mocks formatResponse.toolError."""
    return f"Error: {message}"

def format_tool_result_mock(content: str, images: Optional[List[str]] = None) -> str:
    """Mocks formatResponse.toolResult."""
    if images:
        return f"Result: {content}\\n(Note: {len(images)} images were also retrieved, but not directly rendered in this text output.)"
    return f"Result: {content}"

# Mock for `parseXml`: This is a **CRITICAL STUB/SIMPLIFICATION**.
# The original `parseXml` likely uses a robust XML parser.
# This mock will use Python\'s `xml.etree.ElementTree` for basic XML parsing.
# It simulates the expected structure for `suggest` elements.
import xml.etree.ElementTree as ET

def parse_xml_stub(xml_string: str, tags_to_parse: List[str]) -> Dict[str, Any]:
    """
    STUB: Mocks parseXml from TypeScript.
    Parses a simple XML string and extracts content based on tags_to_parse.
    Specifically designed to handle the \'suggest\' XML structure for this tool.
    """
    try:
        root = ET.fromstring(xml_string)
        result: Dict[str, Any] = {}

        for tag in tags_to_parse:
            elements = root.findall(f".//{tag}")
            if elements:
                parsed_items = []
                for elem in elements:
                    text_content = elem.text.strip() if elem.text else ""
                    # Check for attributes that start with \'@_\' as per original
                    attributes = {f"@{k}": v for k, v in elem.attrib.items()}
                    
                    if attributes:
                        # If attributes exist, return as a dict with \'#text\' and attributes
                        item_dict = {"#text": text_content}
                        item_dict.update(attributes)
                        parsed_items.append(item_dict)
                    else:
                        # Otherwise, return as a simple string
                        parsed_items.append(text_content)
                result[tag] = parsed_items if len(parsed_items) > 1 else parsed_items[0]
            else:
                result[tag] = None # Or an empty list/dict based on expected behavior

        return result
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse XML: {e}")
    except Exception as e:
        raise ValueError(f"An unexpected error occurred during XML parsing: {e}")

# --- Pydantic BaseModel for Tool Parameters ---

class AskFollowupQuestionToolParams(BaseModel):
    """Parameters for the ask_followup_question tool."""
    question: str = Field(
        ...,
        description=(
            "The main question or prompt to ask the user for clarification or further input. "
            "This should be a clear, concise question that guides the user\'s response."
        ),
    )
    follow_up: Optional[str] = Field(
        None,
        description=(
            "Optional. An XML string containing suggested answers or modes for the user. "
            "This helps constrain or guide the user\'s response. "
            "Format: `<suggest><answer>Option 1</answer><answer mode=\\'code\\'>Option 2</answer></suggest>`. " # Corrected here
            "Each `<answer>` tag contains a suggestion. The `mode` attribute is optional and can "
            "indicate how the suggestion should be interpreted (e.g., \'code\', \'text\', \'file\')."
        ),
    )

# --- Python Tool Logic ---

def ask_followup_question_function(question: str, follow_up: Optional[str] = None) -> str:
    """
    Asks the user a follow-up question, optionally providing suggested answers.

    This tool is used when the agent requires additional information, clarification,
    or a decision from the user to proceed with a task. It allows the agent to
    guide the user\'s response by offering predefined options.

    Args:
        question (str): The main question or prompt to ask the user.
        follow_up (str, optional): An XML string containing suggested answers or modes.
                                   Format: `<suggest><answer>Option 1</answer><answer mode=\'code\'>Option 2</answer></suggest>`.

    Returns:
        str: A formatted string containing the user\'s feedback (answer) to the question.
             The format will be `<answer>\\n[user\'s response]\\n</answer>`.
             If an error occurs (e.g., invalid XML), an error message is returned.
    """
    # All UI/interaction/context-specific logic removed.
    # No `cline.*` context objects (`cline.consecutiveMistakeCount`, `cline.recordToolError`,
    # `cline.ask`, `cline.say`, `formatResponse.toolResult`, `formatResponse.toolError`).
    # No `block.partial` handling.

    follow_up_json: Dict[str, Any] = {
        "question": question,
        "suggest": [],
    }

    if follow_up:
        try:
            # The parse_xml_stub is designed to handle the XML structure correctly
            # It expects the raw XML string, not a JSON string containing XML
            parsed_suggest_xml = parse_xml_stub(follow_up, ["suggest", "answer"])
            
            raw_suggestions = parsed_suggest_xml.get("answer")
            if raw_suggestions is None:
                # If \'answer\' tag is not found within \'suggest\', check if \'suggest\' itself contains text
                # This handles `<suggest>Some text</suggest>`
                suggest_root_content = parsed_suggest_xml.get("suggest")
                if isinstance(suggest_root_content, str) and suggest_root_content.strip():
                    raw_suggestions = [suggest_root_content.strip()]
                elif isinstance(suggest_root_content, list):
                    # In case parse_xml_stub returns list directly for \'suggest\'
                    raw_suggestions = suggest_root_content
                else:
                    raw_suggestions = [] # No suggestions found
            elif not isinstance(raw_suggestions, list):
                raw_suggestions = [raw_suggestions] # Ensure it\'s a list for iteration

            normalized_suggest: List[Dict[str, str]] = []
            for sug in raw_suggestions:
                if isinstance(sug, str):
                    normalized_suggest.append({"answer": sug})
                elif isinstance(sug, dict) and "#text" in sug:
                    result_sug: Dict[str, str] = {"answer": sug["#text"]}
                    # Check for attributes like \'@_mode\'
                    for key, value in sug.items():
                        if key.startswith("@_"):
                            result_sug[key[2:]] = value # Remove \'@_\' prefix
                    normalized_suggest.append(result_sug)
            
            follow_up_json["suggest"] = normalized_suggest

        except ValueError as e:
            # Catch XML parsing errors
            return format_tool_error_mock(f"Invalid XML format for \'follow_up\': {e}")
        except Exception as e:
            # Catch any other unexpected errors during parsing
            return format_tool_error_mock(f"An unexpected error occurred while processing \'follow_up\' XML: {e}")

    # Simulate user interaction and response.
    # In a real Llama-Index Agent setup, the agent itself would handle the interaction
    # with the user based on the tool\'s description and parameters.
    # The tool\'s job is just to define the capability and its inputs/outputs.
    # We will return a placeholder for the user\'s response.
    # The LLM is expected to provide the actual user response later.

    # The original tool calls `cline.ask` and then `cline.say("user_feedback")`
    # and then `pushToolResult(formatResponse.toolResult(...))`.\n
    # For a Llama-Index FunctionTool, the return value is the "tool result".
    # We simulate a generic user response here.
    
    # Simulate a generic user response. In a real LlamaIndex agent, the LLM
    # would generate this based on its interaction with the user.
    # For the purpose of this tool, we assume the user provides a direct answer.
    simulated_user_response = "The user has provided an answer." # This would be filled by the LLM
    
    # If the `follow_up` provided suggestions, the LLM might choose one of them.\n
    if follow_up_json["suggest"]:
        simulated_user_response += " (Based on provided suggestions)"
        # You could even pick one of the suggestions for a more concrete stub behavior
        # if you want to test the parsing of suggestions.
        # e.g., simulated_user_response = f"User chose: {follow_up_json[\'suggest\'][0][\'answer\']}"


    # The original tool returns a formatted string like `<answer>\\n${text}\\n</answer>`
    # We will maintain that format.
    return format_tool_result_mock(f"<answer>\\n{simulated_user_response}\\n</answer>")

# --- FunctionTool Instantiation ---

ask_followup_question_tool = FunctionTool.from_defaults(
    fn=ask_followup_question_function,
    name="ask_followup_question",
    description="""
## ask_followup_question
Description: Ask the user a question to gather additional information needed to complete the task. This tool should be used when you encounter ambiguities, need clarification, or require more details to proceed effectively. It allows for interactive problem-solving by enabling direct communication with the user. Use this tool judiciously to maintain a balance between gathering necessary information and avoiding excessive back-and-forth.
Parameters:
- question: (required) The question to ask the user. This should be a clear, specific question that addresses the information you need.
- follow_up: (required) A list of 2-4 suggested answers that logically follow from the question, ordered by priority or logical sequence. Each suggestion must:
  1. Be provided in its own <suggest> tag
  2. Be specific, actionable, and directly related to the completed task
  3. Be a complete answer to the question - the user should not need to provide additional information or fill in any missing details. DO NOT include placeholders with brackets or parentheses.
  4. Optionally include a mode attribute to switch to a specific mode when the suggestion is selected: <suggest mode="mode-slug">suggestion text</suggest>
     - When using the mode attribute, focus the suggestion text on the action to be taken rather than mentioning the mode switch, as the mode change is handled automatically and indicated by a visual badge
Usage:
<ask_followup_question>
<question>Your question here</question>
<follow_up>
<suggest>
Your suggested answer here
</suggest>
<suggest mode="code">
Implement the solution
</suggest>
</follow_up>
</ask_followup_question>

Example: Requesting to ask the user for the path to the frontend-config.json file
<ask_followup_question>
<question>What is the path to the frontend-config.json file?</question>
<follow_up>
<suggest>./src/frontend-config.json</suggest>
<suggest>./config/frontend-config.json</suggest>
<suggest>./frontend-config.json</suggest>
</follow_up>
</ask_followup_question>

Example: Asking a question with mode switching options
<ask_followup_question>
<question>How would you like to proceed with this task?</question>
<follow_up>
<suggest mode="code">Start implementing the solution</suggest>
<suggest mode="architect">Plan the architecture first</suggest>
<suggest>Continue with more details</suggest>
</follow_up>
</ask_followup_question>
""",
    fn_schema=AskFollowupQuestionToolParams,
)