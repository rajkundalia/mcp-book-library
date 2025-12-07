"""
Ollama Host with True LLM Routing
NO hardcoded if/else logic - the LLM decides which tool/prompt to use
"""
import asyncio
import json
import sys
import re
import yaml
import logging
from pathlib import Path
from typing import Optional, Any, Dict
import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ollama-host")


class OllamaHost:
    """
    Ollama-based host that uses true LLM routing.
    The LLM decides which tools/prompts to use based on their descriptions.
    """

    def __init__(self, config_path: str = "host/config.yaml"):
        self.config = self._load_config(config_path)
        self.conversation_history = []
        self.mcp_session = None
        self.stdio_context = None
        self.session_context = None
        self.available_tools = []

    def _load_config(self, path: str) -> dict:
        """Load configuration from YAML file."""
        config_file = Path(path)
        if not config_file.exists():
            logger.warning(f"Config file {path} not found, using defaults")
            # Default configuration
            return {
                "ollama": {
                    "host": "http://localhost:11434",
                    "model": "llama3",
                    "timeout": 120,
                    "temperature": 0.7
                },
                "server": {
                    "transport": "stdio",
                    "path": "server/stdio_server.py"
                },
                "agent": {
                    "max_iterations": 50
                }
            }

        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {path}")
            return config

    async def connect_to_server(self):
        """Connect to the MCP server via STDIO."""
        server_path = Path(self.config["server"]["path"])

        if not server_path.exists():
            print(f"Error: Server file not found at {server_path}")
            print("Please ensure the server is set up correctly.")
            sys.exit(1)

        print("Starting MCP server...")

        server_params = StdioServerParameters(
            command="python",
            args=[str(server_path)],
            env=None
        )

        try:
            # Store context managers to keep them alive
            self.stdio_context = stdio_client(server_params)
            self.read_stream, self.write_stream = await self.stdio_context.__aenter__()

            print("Initializing session...")
            self.session_context = ClientSession(self.read_stream, self.write_stream)
            self.mcp_session = await self.session_context.__aenter__()

            # Initialize the session
            await self.mcp_session.initialize()
            print("✓ Connected to MCP server")

            # Discover available tools
            tools_result = await self.mcp_session.list_tools()
            self.available_tools = tools_result.tools
            logger.info(f"✓ Discovered {len(self.available_tools)} tools")

        except Exception as e:
            print(f"Error connecting to server: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    async def disconnect_from_server(self):
        """Disconnect from the MCP server."""
        try:
            if self.session_context:
                await self.session_context.__aexit__(None, None, None)
            if self.stdio_context:
                await self.stdio_context.__aexit__(None, None, None)
            logger.info("✓ Cleaned up resources")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

    async def get_system_context(self) -> str:
        """
        Build system context with tool/prompt descriptions.
        This is how the LLM learns what capabilities are available.
        """
        if not self.mcp_session:
            raise RuntimeError("MCP session not initialized")

        # Get available tools
        tools_response = await self.mcp_session.list_tools()
        tools = tools_response.tools if hasattr(tools_response, 'tools') else []

        # Get available prompts
        prompts_response = await self.mcp_session.list_prompts()
        prompts = prompts_response.prompts if hasattr(prompts_response, 'prompts') else []

        # Get available resources
        resources_response = await self.mcp_session.list_resources()
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
            args_desc = ", ".join([
                f"{arg.name}{'(required)' if arg.required else '(optional)'}"
                for arg in prompt.arguments
            ]) if prompt.arguments else "none"
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
            logger.info(f"Calling MCP tool: {tool_name}")
            logger.debug(f"Arguments: {arguments}")

            result = await self.mcp_session.call_tool(tool_name, arguments=arguments)

            # Extract text content
            if hasattr(result, 'content') and result.content:
                result_text = result.content[0].text if result.content else str(result)
                logger.info(f"✓ Tool {tool_name} executed successfully")
                return result_text
            return str(result)

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return f"Error executing tool: {str(e)}"

    async def execute_prompt(self, prompt_name: str, arguments: dict) -> str:
        """Execute a prompt via MCP."""
        try:
            logger.info(f"Getting prompt: {prompt_name}")
            logger.debug(f"Arguments: {arguments}")

            result = await self.mcp_session.get_prompt(prompt_name, arguments=arguments)

            # Extract prompt text
            if hasattr(result, 'messages') and result.messages:
                prompt_text = result.messages[0].content.text
                logger.info(f"✓ Prompt {prompt_name} retrieved successfully")
                return prompt_text
            return str(result)

        except Exception as e:
            logger.error(f"Error executing prompt {prompt_name}: {e}")
            return f"Error executing prompt: {str(e)}"

    async def chat(self, user_message: str) -> str:
        """
        Main chat loop with LLM routing.
        The LLM decides what to do based on system context.
        """
        logger.info(f"User: {user_message}")

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
                    messages=messages,
                    options={
                        'temperature': self.config["ollama"].get("temperature", 0.7)
                    }
                )

                assistant_message = response['message']['content']
                logger.info(f"Ollama response: {assistant_message[:100]}...")

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
                            "content": f"Tool result: {tool_result}\n\nNow provide a natural language response to the user based on this result."
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
                            "content": f"Prompt template: {prompt_result}\n\nNow use this template to help the user."
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
                logger.error(f"Error in chat loop: {e}")
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
            print(f"✓ Ollama is running")
            print(f"✓ Model: {self.config['ollama']['model']}")
        except Exception as e:
            print("⚠️  Ollama is not running!")
            print()
            print("Please start Ollama:")
            print("  1. Install from: https://ollama.ai/download")
            print("  2. Run: ollama serve")
            print("  3. Pull model: ollama pull llama3")
            print()
            sys.exit(1)

        try:
            # Connect to MCP server
            await self.connect_to_server()

            print(f"✓ Tools: {len(self.available_tools)} available")
            print("\nType 'exit', 'quit', 'bye', or 'stop' to end the conversation.")
            print("Type 'tools' to list available tools")
            print("Type 'clear' to clear conversation history")
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

                    # List tools command
                    if user_input.lower() == 'tools':
                        print("\nAvailable Tools:")
                        for tool in self.available_tools:
                            print(f"  - {tool.name}: {tool.description}")
                        print()
                        continue

                    # Clear history command
                    if user_input.lower() == 'clear':
                        self.conversation_history = []
                        print("\n✓ Conversation history cleared\n")
                        continue

                    # Get response
                    response = await self.chat(user_input)
                    print(f"\nAssistant: {response}\n")

                except KeyboardInterrupt:
                    print("\n\nGoodbye! Happy reading! 📚")
                    break
                except Exception as e:
                    print(f"\nError: {str(e)}\n")
                    logger.error(f"Error in main loop: {e}", exc_info=True)

        finally:
            # Always cleanup connection
            await self.disconnect_from_server()


async def main():
    """Entry point for the Ollama host."""
    host = OllamaHost()
    await host.run()


if __name__ == "__main__":
    asyncio.run(main())