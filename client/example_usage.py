"""
Example Client demonstrating all MCP primitives
Shows how to use resources, prompts, and tools programmatically
"""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pathlib import Path


async def demonstrate_mcp_primitives():
    """
    Educational example showing how to use each MCP primitive.
    """
    print("=" * 60)
    print("MCP Library - Client Example")
    print("=" * 60)
    print()

    # Connect to server
    server_path = Path("server/stdio_server.py")
    server_params = StdioServerParameters(
        command="python",
        args=[str(server_path)],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("✓ Connected to MCP server\n")

            # ===== DEMONSTRATE RESOURCES =====
            print("1. RESOURCES - Reading structured data")
            print("-" * 60)

            # List available resources
            resources = await session.list_resources()
            print(f"Available resources: {len(resources.resources)}")
            for resource in resources.resources:
                print(f"  - {resource.uri}: {resource.description}")
            print()

            # Read a specific resource
            catalog = await session.read_resource("library://books/catalog")
            print("Book catalog content (first 200 chars):")
            print(catalog.contents[0].text[:200] + "...\n")

            # ===== DEMONSTRATE PROMPTS =====
            print("2. PROMPTS - Using templates with injected data")
            print("-" * 60)

            # List available prompts
            prompts = await session.list_prompts()
            print(f"Available prompts: {len(prompts.prompts)}")
            for prompt in prompts.prompts:
                print(f"  - {prompt.name}: {prompt.description}")
            print()

            # Get a prompt with arguments
            recommend_prompt = await session.get_prompt(
                "recommend_books",
                arguments={"genre": "Science Fiction", "mood": "adventurous"}
            )
            print("Recommendation prompt (first 300 chars):")
            print(recommend_prompt.messages[0].content.text[:300] + "...\n")

            # ===== DEMONSTRATE TOOLS =====
            print("3. TOOLS - Executing actions")
            print("-" * 60)

            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {len(tools.tools)}")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            print()

            # Search for books
            print("Searching for 'science fiction' books...")
            search_result = await session.call_tool(
                "search_books",
                arguments={"query": "science fiction", "min_rating": 4.0}
            )
            print(f"Search result:\n{search_result.content[0].text}\n")

            # Add a book to reading list
            print("Adding 'dune' to reading list...")
            add_result = await session.call_tool(
                "add_to_reading_list",
                arguments={"book_id": "hobbit"}
            )
            print(f"Result:\n{add_result.content[0].text}\n")

            print("=" * 60)
            print("Demo complete!")
            print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demonstrate_mcp_primitives())