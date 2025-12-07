"""
Ollama Host with True LLM Routing
NO hardcoded if/else logic - the LLM decides which tool/prompt to use
"""
import asyncio
import json
import re
import sys
from pathlib import Path
from typing import Optional

import ollama
import yaml
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class OllamaHost:
    """
    Ollama-based host that uses true LLM routing.
    The LLM decides which tools/prompts to use based on their descriptions.
    """

    def __init__(self, config_path: str = "host/config.yaml"):
        self.config = self._load_config(config_path)
        self.conversation_history = []
        self.session: Optional[ClientSession] = None

    def _load_config(self, path: str) -> dict:
        """Load configuration from YAML file."""
        config_file = Path(path)
        if not config_file.exists():
            # Default configuration
            return {
                "ollama": {
                    "host": "http://localhost:11434",
                    "model": "llama3",
                    "timeout": 120
                },
                "server": {
                    "type": "stdio",
                    "path": "server/stdio_server.py"
                },
                "agent": {
                    "max_iterations": 50
                }
            }

        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    async def connect_to_server(self):
        """Connect to the MCP server via STDIO."""
        server_path = Path(self.config["server"]["path"])

        if not server_path.exists():
            print(f"Error: Server file not found at {server_path}")
            print("Please ensure the server is set up correctly.")
            sys.exit(1)

        server_params = StdioServerParameters(
            command="python",
            args=[str(server_path)],
            env=None
        )

        # Connect to server
        stdio_transport = await stdio_client(server_params)
        self.stdio, self.write = stdio_transport
        self.session = ClientSession(self.stdio, self.write)

        await self.session.initialize()

        print("✓ Connected to MCP server")

    async def get_system_context(self) -> str:
        """
        Build system context with tool/prompt descriptions.
        This is how the LLM learns what capabilities are available.
        """
        # Get available tools
        tools_response = await self.session.list_tools()
        tools = tools_response.tools if hasattr(tools_response, 'tools') else []

        # Get available prompts
        prompts_response = await self.session.list_prompts()
        prompts = prompts_response.prompts if hasattr(prompts_response, 'prompts') else []

        # Get available resources
        resources_response = await self.session.list_resources()
        resources = resources_response.resources if hasattr(resources_response, 'resources') else []

        # Build system prompt
        context = """You are a helpful library assistant. You have access to the following capabilities:

TOOLS (use these to perform actions):
"""

        for tool in tools:
            context += f"\n- {tool.name}: {tool.description}\n"
            context += f"  Input: {json.dumps(tool.inputSchema, indent=4)}\n"

        context += "\nPROMPTS (use these for specialized templates):\n"
        for prompt in prompts:
            args_desc = ", ".join([f"{arg['name']}{'(required)' if arg.get('required') else '(optional)'}"
                                   for arg in prompt.arguments]) if prompt.arguments else "none"
            context += f"\n- {prompt.name}: {prompt.description}\n"
            context += f"  Arguments: {args_desc}\n"

        context += "\nRESOURCES (available data):\n"
        for resource in resources:
            context += f"\n- {resource.uri}: {resource.description}\n"

        context += """

IMPORTANT: When you need to use a tool, respond with JSON in this exact format:
{
  "action": "tool",
  "tool_name": "search_books",
  "arguments": {"query": "science fiction"}
}

When you need to use a prompt, respond with:
{
  "action": "prompt",
  "prompt_name": "recommend_books",
  "arguments": {"genre": "Fantasy"}
}

When you have a final answer, just respond normally without JSON.
"""

        return context

    def parse_llm_response(self, response: str) -> Optional[dict]:
        """
        Parse LLM response to detect tool/prompt calls.
        This is the key routing mechanism - NO hardcoded logic!
        """
        # Try to find JSON in the response
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response)

        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                if parsed.get("action") in ["tool", "prompt"]:
                    return parsed
            except json.JSONDecodeError:
                pass

        return None

    async def execute_tool(self, tool_name: str, arguments: dict) -> str:
        """Execute a tool via MCP."""
        try:
            result = await self.session.call_tool(tool_name, arguments)

            # Extract text content
            if hasattr(result, 'content') and result.content:
                return result.content[0].text if result.content else str(result)
            return str(result)

        except Exception as e:
            return f"Error executing tool: {str(e)}"

    async def execute_prompt(self, prompt_name: str, arguments: dict) -> str:
        """Execute a prompt via MCP."""
        try:
            result = await self.session.get_prompt(prompt_name, arguments)

            # Extract prompt text
            if hasattr(result, 'messages') and result.messages:
                return result.messages[0].content.text
            return str(result)

        except Exception as e:
            return f"Error executing prompt: {str(e)}"

    async def chat(self, user_message: str) -> str:
        """
        Main chat loop with LLM routing.
        The LLM decides what to do based on system context.
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Get system context
        system_context = await self.get_system_context()

        # Prepare messages for Ollama
        messages = [
            {"role": "system", "content": system_context},
            *self.conversation_history
        ]

        # Agent loop - allow LLM to use multiple tools if needed
        iteration = 0
        max_iterations = self.config["agent"]["max_iterations"]

        while iteration < max_iterations:
            iteration += 1

            # Get LLM response
            try:
                response = ollama.chat(
                    model=self.config["ollama"]["model"],
                    messages=messages
                )

                assistant_message = response['message']['content']

                # Check if LLM wants to use a tool or prompt
                action = self.parse_llm_response(assistant_message)

                if action:
                    # LLM decided to use a tool or prompt
                    if action["action"] == "tool":
                        tool_name = action["tool_name"]
                        arguments = action.get("arguments", {})

                        print(f"\n[Using tool: {tool_name}]")

                        # Execute the tool
                        tool_result = await self.execute_tool(tool_name, arguments)

                        # Add tool result to conversation
                        messages.append({
                            "role": "assistant",
                            "content": assistant_message
                        })
                        messages.append({
                            "role": "user",
                            "content": f"Tool result: {tool_result}"
                        })

                        # Continue loop to let LLM process the result
                        continue

                    elif action["action"] == "prompt":
                        prompt_name = action["prompt_name"]
                        arguments = action.get("arguments", {})

                        print(f"\n[Using prompt: {prompt_name}]")

                        # Execute the prompt
                        prompt_result = await self.execute_prompt(prompt_name, arguments)

                        # Add prompt result to conversation
                        messages.append({
                            "role": "assistant",
                            "content": assistant_message
                        })
                        messages.append({
                            "role": "user",
                            "content": f"Prompt template: {prompt_result}"
                        })

                        # Continue loop to let LLM use the prompt
                        continue

                else:
                    # No action detected - this is the final answer
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": assistant_message
                    })
                    return assistant_message

            except Exception as e:
                if "ollama" in str(e).lower() or "connection" in str(e).lower():
                    return (
                        "Error: Cannot connect to Ollama.\n\n"
                        "Please ensure Ollama is installed and running:\n"
                        "1. Install: https://ollama.ai/download\n"
                        "2. Run: ollama serve\n"
                        "3. Pull model: ollama pull llama3"
                    )
                return f"Error: {str(e)}"

        return "Reached maximum iterations. Please try rephrasing your request."

    async def run(self):
        """Main run loop for the host."""
        print("=" * 60)
        print("MCP Library Assistant (Ollama)")
        print("=" * 60)
        print()

        # Check Ollama
        try:
            ollama.list()
        except Exception:
            print("⚠️  Ollama is not running!")
            print()
            print("Please start Ollama:")
            print("  1. Install from: https://ollama.ai/download")
            print("  2. Run: ollama serve")
            print("  3. Pull model: ollama pull llama3")
            print()
            sys.exit(1)

        # Connect to MCP server
        await self.connect_to_server()

        print("\nType 'exit', 'quit', 'bye', or 'stop' to end the conversation.")
        print()

        # Main conversation loop
        while True:
            try:
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                # Check for exit commands
                if user_input.lower() in ['exit', 'quit', 'bye', 'stop']:
                    print("\nGoodbye! Happy reading! 📚")
                    break

                # Get response
                response = await self.chat(user_input)
                print(f"\nAssistant: {response}\n")

            except KeyboardInterrupt:
                print("\n\nGoodbye! Happy reading! 📚")
                break
            except Exception as e:
                print(f"\nError: {str(e)}\n")


async def main():
    """Entry point for the Ollama host."""
    host = OllamaHost()
    await host.run()


if __name__ == "__main__":
    asyncio.run(main())
