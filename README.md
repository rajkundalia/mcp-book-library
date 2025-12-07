# MCP Book Library Manager

An educational Model Context Protocol (MCP) server demonstrating **Resources**, **Prompts**, and **Tools** with dual transport support (STDIO + HTTP) and Ollama integration.

## What You'll Learn

This project demonstrates:

- ✅ **Resources**: Structured data access (book catalog, reading statistics)
- ✅ **Prompts**: Template-based LLM guidance with data injection
- ✅ **Tools**: Executable functions (search, modify reading list)
- ✅ **STDIO Transport**: Traditional stdin/stdout communication
- ✅ **HTTP Transport**: RESTful JSON-RPC endpoint
- ✅ **True LLM Routing**: Ollama-based host where the AI decides which tools/prompts to use

## Prerequisites

- Python 3.10 or higher
- [Ollama](https://ollama.ai/) installed and running
- Node.js (for MCP Inspector, optional)

## Quick Start

### 1. Installation

```bash
# Clone or create the project directory
cd mcp-library

# Install dependencies
pip install -r requirements.txt

# Install Ollama (if not already installed)
# Visit: https://ollama.ai/download

# Pull the Llama3 model
ollama pull llama3
```

### 2. Start Ollama Service

```bash
# In a separate terminal
ollama serve
```

### 3. Run the Interactive Assistant

```bash
python host/run_ollama.py
```

Example interaction:
```
You: Find me some science fiction books
Assistant: [Uses search_books tool internally]
I found several great science fiction books:
1. Dune by Frank Herbert (Rating: 4.5)
2. Brave New World by Aldous Huxley (Rating: 4.3)
...

You: Recommend me a book based on my reading history
Assistant: [Uses recommend_books prompt with your stats]
Based on your favorite genres (Science Fiction, Fantasy, Mystery)...
```

## Testing with MCP Inspector

The MCP Inspector lets you test primitives without writing code:

```bash
# Install Inspector
npm install -g @modelcontextprotocol/inspector

# Run Inspector with your server
mcp-inspector python server/stdio_server.py
```

Opens a web UI where you can:
- Browse and read **Resources**
- Test **Prompts** with different arguments
- Execute **Tools** with custom inputs

See [client/inspector_guide.md](client/inspector_guide.md) for detailed instructions.

## Understanding MCP Primitives

### Resources (Read-Only Data)

Resources provide structured data that LLMs can access:

```python
# List resources
GET library://books/catalog        # All books with metadata
GET library://user/reading-stats   # User's reading history
```

**Use case**: When the LLM needs to know what books are available or understand user preferences.

### Prompts (Templates + Data)

Prompts are instruction templates with injected data:

```python
# Get recommendation prompt
get_prompt("recommend_books", {
    "genre": "Fantasy",
    "mood": "adventurous"
})
```

Returns a complete prompt with:
- Your reading statistics
- Full book catalog
- Structured instructions for the LLM

**Use case**: Guide the LLM to perform specific tasks using current data.

### Tools (Executable Functions)

Tools perform actions and return results:

```python
# Search for books
call_tool("search_books", {
    "query": "tolkien",
    "min_rating": 4.5
})

# Add to reading list
call_tool("add_to_reading_list", {
    "book_id": "fellowship-ring"
})
```

**Use case**: When the LLM needs to DO something (search, modify data, call APIs).

## 🔧 Architecture

```
┌─────────────────┐
│  Ollama Host    │  ← True LLM routing (no hardcoded logic)
│  (run_ollama.py)│
└────────┬────────┘
         │
    JSON-RPC over STDIO/HTTP
         │
┌────────▼────────┐
│  MCP Server     │
│  ┌───────────┐  │
│  │ Resources │  │  ← Read data
│  │ Prompts   │  │  ← Templates
│  │ Tools     │  │  ← Execute actions
│  └───────────┘  │
└────────┬────────┘
         │
┌────────▼────────┐
│  Data Files     │
│  - books.json   │
│  - reading_list.│
└─────────────────┘
```

## How the LLM Routing Works

Unlike traditional chatbots with `if/else` logic, this host uses **true AI routing**:

1. **System Context**: The host fetches all available tools/prompts and sends their descriptions to Ollama
2. **LLM Decision**: Llama3 reads the user's query and decides which tool/prompt to use
3. **Execution**: The host executes the LLM's choice via MCP
4. **Iteration**: Results flow back to the LLM, which can chain multiple tools

Example:
```
User: "Find fantasy books and add the best one to my list"

Llama3 thinks:
  → Use search_books(query="fantasy") first
  → Analyze results
  → Use add_to_reading_list(book_id="fellowship-ring")
  → Respond to user
```

## Running Different Components

### STDIO Server (for Inspector/Clients)
```bash
python server/stdio_server.py
```

### HTTP Server (for REST clients)
```bash
python server/http_server.py
# Server runs on http://localhost:8000

# read more about testing this on inspector_guide.md file
```

### Example Client (Demonstrates all primitives)
```bash
python client/example_usage.py
```

### Run Tests
```bash
pytest tests/ -v
```

## Project Structure

```
mcp-library/
├── server/
│   ├── stdio_server.py        # STDIO transport
│   ├── http_server.py         # HTTP transport
│   ├── registry.py            # Central primitive registry
│   ├── resources/             # Data access layer
│   ├── prompts/               # Template generators
│   ├── tools/                 # Executable functions
│   └── data/                  # JSON storage
├── host/
│   ├── run_ollama.py          # Ollama-based AI host
│   └── config.yaml            # Configuration
├── client/
│   ├── example_usage.py       # Demo client
│   └── inspector_guide.md     # Inspector tutorial
├── tests/                     # Pytest test suite
└── diagrams/                  # Architecture diagrams
```

## Troubleshooting

### Ollama Connection Error
```
Error: Cannot connect to Ollama
```
**Solution**: Ensure Ollama is running:
```bash
ollama serve
ollama pull llama3
```

### Module Not Found
```
ModuleNotFoundError: No module named 'mcp'
```
**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Tool Execution Fails
**Solution**: Verify data files exist:
```bash
ls server/data/books.json
ls server/data/reading_list.json
```

## Learn More

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Ollama Documentation](https://ollama.ai/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## License

MIT License - Feel free to use this for learning and building!

---

**Happy Learning!**