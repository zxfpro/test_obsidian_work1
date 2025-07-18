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
    # In a real scenario, this might format content and image links for LLM consumption.
    # For now, just return content and note if images are present.
    if images:
        return f"Result: {content}\n(Note: {len(images)} images were also retrieved, but not directly rendered in this text output.)"
    return f"Result: {content}"


# STUB for `cline.providerRef.deref()?.getMcpHub()?.readResource`
# This is a **CRITICAL STUB** because `McpHub` is an internal component
# of the original TypeScript application, likely managing communication
# with external "micro-credentialing providers" (MCPs) and their resources.
#
# A Llama-Index `FunctionTool` cannot directly interact with such external
# or proprietary systems without a dedicated Python client/SDK for that system.
#
# This stub will simulate reading a resource based on `server_name` and `uri`.
#
# TODO: For a real-world scenario, this would need to be replaced with actual
# Python client code for the MCP system, or an API call that interacts with it.
def read_mcp_resource_stub(server_name: str, uri: str) -> Optional[Dict[str, Any]]:
    """
    STUB: Mocks reading a resource from an external MCP server.
    Simulates a response based on `server_name` and `uri`.
    """
    print(f"STUB: Simulating MCP resource access: server=\'{server_name}\', uri=\'{uri}\'")

    if server_name == "GitHub_MCP":
        if uri == "/repos/my_repo/README.md":
            return {
                "contents": [{"text": "# My Repository\n\nThis is a sample README file."}],
                "isError": False
            }
        elif uri == "/users/octocat/avatar.png":
            # Simulate a base64 encoded image
            dummy_base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
            return {
                "contents": [{"mimeType": "image/png", "blob": dummy_base64_image}],
                "isError": False
            }
        else:
            return {
                "contents": [{"text": f"Resource not found for GitHub_MCP at URI: {uri}"}],
                "isError": True
            }
    elif server_name == "Jira_MCP":
        if uri == "/issues/PROJ-123/description":
            return {
                "contents": [{"text": "Description for PROJ-123: Implement feature X and fix bug Y."}],
                "isError": False
            }
        else:
            return {
                "contents": [{"text": f"Resource not found for Jira_MCP at URI: {uri}"}],
                "isError": True
            }
    else:
        return {
            "contents": [{"text": f"Unknown MCP server: {server_name}"}],
            "isError": True
        }


# --- Pydantic BaseModel for Tool Parameters ---

class AccessMcpResourceToolParams(BaseModel):
    """Parameters for the access_mcp_resource tool."""
    server_name: str = Field(
        ...,
        description=(
            "The name of the MCP (Micro-Credentialing Provider) server from which "
            "to access a resource. This identifies the specific external service or platform."
        ),
    )
    uri: str = Field(
        ...,
        description=(
            "The URI (Uniform Resource Identifier) of the specific resource to access "
            "on the MCP server. This is typically a path or endpoint that points to "
            "data, files, or other assets (e.g., `/repos/my_project/README.md`, `/users/avatar.png`)."
        ),
    )

# --- Python Tool Logic ---

def access_mcp_resource_function(server_name: str, uri: str) -> str:
    """
    Accesses and retrieves a specific resource (e.g., file content, image) from a designated MCP server.

    This tool enables the agent to fetch data or assets from external services that are
    exposed as resources via an MCP. This is crucial for retrieving information needed
    for tasks like reading documentation, viewing images, or fetching configuration data
    from connected platforms.

    Args:
        server_name (str): The name of the MCP server to connect to (e.g., "GitHub_MCP", "Jira_MCP").
        uri (str): The URI of the resource to access (e.g., `/repos/my_project/README.md`, `/images/logo.png`).

    Returns:
        str: A formatted string containing the content of the accessed resource,
             or an error message if the access failed (e.g., resource not found,
             permission issues, server error). If the resource is an image, a note
             will indicate its presence as the image itself cannot be directly rendered.
    """
    # All UI/interaction/context-specific logic removed.
    # No `cline.*` context objects (`cline.consecutiveMistakeCount`, `cline.recordToolError`,
    # `cline.ask`, `cline.say`, `cline.providerRef`, `formatResponse.toolResult`).
    # No `block.partial` handling.

    # Simulate the MCP resource access using the stub
    resource_result = read_mcp_resource_stub(server_name, uri)

    if not resource_result:
        return format_tool_error_mock("No response from MCP server or resource access failed internally.")
    
    # Process contents, extracting text and noting images
    extracted_texts = []
    extracted_images: List[str] = []

    if resource_result.get("contents") and isinstance(resource_result["contents"], list):
        for item in resource_result["contents"]:
            if isinstance(item, dict):
                if item.get("type") == "text" and "text" in item:
                    extracted_texts.append(item["text"])
                elif item.get("mimeType", "").startswith("image") and "blob" in item:
                    # For images, we just collect the base64 string or data URI
                    if item["blob"].startswith("data:"):
                        extracted_images.append(item["blob"])
                    else:
                        extracted_images.append(f"data:{item['mimeType']};base64," + item["blob"])
    
    resource_result_pretty = "\n\n".join(filter(None, extracted_texts)) or "(Empty response)"

    if resource_result.get("isError", False):
        return f"Error: Failed to access MCP resource \'{uri}\' on server \'{server_name}\'.\nDetails:\n{resource_result_pretty or 'No specific error details provided.'}"
    else:
        return format_tool_result_mock(resource_result_pretty, extracted_images)


# --- FunctionTool Instantiation ---

access_mcp_resource_tool = FunctionTool.from_defaults(
    fn=access_mcp_resource_function,
    name="access_mcp_resource",
    description="""
## access_mcp_resource
Description: Request to access a resource provided by a connected MCP server. Resources represent data sources that can be used as context, such as files, API responses, or system information.
Parameters:
- server_name: (required) The name of the MCP server providing the resource
- uri: (required) The URI identifying the specific resource to access
Usage:
<access_mcp_resource>
<server_name>server name here</server_name>
<uri>resource URI here</uri>
</access_mcp_resource>

Example: Requesting to access an MCP resource

<access_mcp_resource>
<server_name>weather-server</server_name>
<uri>weather://san-francisco/current</uri>
</access_mcp_resource>
""",
    fn_schema=AccessMcpResourceToolParams,
)