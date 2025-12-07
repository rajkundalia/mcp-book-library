"""
STDIO Transport Server
Demonstrates MCP server using stdin/stdout communication
"""
import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Prompt, Tool, TextContent, GetPromptResult, PromptMessage
from registry import MCPRegistry

# Create MCP server instance
app = Server("mcp-library")
registry = MCPRegistry()


@app.list_resources()
async def handle_list_resources() -> list[Resource]:
    """
    Handler for listing available resources.
    Resources provide structured data to LLMs.
    """
    resources_meta = registry.list_resources()
    return [
        Resource(
            uri=r["uri"],
            name=r["name"],
            description=r["description"],
            mimeType=r["mimeType"]
        )
        for r in resources_meta
    ]


@app.read_resource()
async def handle_read_resource(uri: str) -> str:
    """
    Handler for reading a specific resource.
    Returns the actual content of the resource.
    """
    resource_data = registry.read_resource(uri)
    return resource_data["text"]


@app.list_prompts()
async def handle_list_prompts() -> list[Prompt]:
    """
    Handler for listing available prompts.
    Prompts are templates that guide LLM behavior with injected data.
    """
    prompts_meta = registry.list_prompts()
    return [
        Prompt(
            name=p["name"],
            description=p["description"],
            arguments=p.get("arguments", [])
        )
        for p in prompts_meta
    ]


@app.get_prompt()
async def handle_get_prompt(name: str, arguments: dict = None) -> GetPromptResult:
    """
    Handler for getting a specific prompt.
    Returns the fully rendered template with data.
    """
    prompt_data = registry.get_prompt(name, arguments)

    return GetPromptResult(
        description=prompt_data.get("description", ""),
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=prompt_data["prompt"]
                )
            )
        ]
    )

@app.list_resource_templates()
async def handle_list_resource_templates() -> list[Resource]:
    """
    Handler for listing resource templates.
    Templates are parameterized resources.
    """
    # For now, return empty list since we don't have templates
    return []


@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    Handler for listing available tools.
    Tools are executable functions that perform actions.
    """
    tools_meta = registry.list_tools()
    return [
        Tool(
            name=t["name"],
            description=t["description"],
            inputSchema=t["inputSchema"]
        )
        for t in tools_meta
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Handler for executing a tool.
    Runs the tool function and returns results.
    """
    result = registry.call_tool(name, arguments)
    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


async def main():
    """Run the STDIO server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
