# MCP Inspector Setup Guide

The MCP Inspector is an official tool for testing and debugging MCP servers.

## Installation

```bash
npm install -g @modelcontextprotocol/inspector
```
## Running the Inspector

### For STDIO Server

```bash
mcp-inspector python server/stdio_server.py
```

This will:
1. Start your MCP server
2. Open a web interface (usually at http://localhost:5173)
3. Allow you to inspect and test all primitives

## Using the Inspector

### Testing Resources

1. Click on "Resources" tab
2. You'll see:
   - `library://books/catalog` - The book catalog
   - `library://user/reading-stats` - Reading statistics
3. Click on any resource to view its content

### Testing Prompts

1. Click on "Prompts" tab
2. Select a prompt (e.g., `recommend_books`)
3. Fill in optional arguments:
   - genre: "Fantasy"
   - mood: "epic"
4. Click "Get Prompt" to see the rendered template

### Testing Tools

1. Click on "Tools" tab
2. Select a tool (e.g., `search_books`)
3. Fill in the arguments:
   ```json
   {
     "query": "tolkien",
     "min_rating": 4.5
   }
   ```
4. Click "Call Tool" to execute and see results

## Troubleshooting

### Server Won't Start
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that data files exist in `server/data/`

### Inspector Can't Connect
- Verify the server path is correct
- Try running the server directly first: `python server/stdio_server.py`

### Tool Execution Fails
- Check the JSON syntax in arguments
- Verify book IDs exist in the catalog
- Look at server logs for error messages

## Advanced Usage

### Testing HTTP Server

The Inspector works with STDIO by default. To test the HTTP server:

1. Start the HTTP server:
   ```bash
   python server/http_server.py
   ```

2. Use curl or Postman to send requests:
   ```bash
   curl -X POST http://localhost:8000/mcp \
     -H "Content-Type: application/json" \
     -d '{
       "jsonrpc": "2.0",
       "id": 1,
       "method": "tools/list",
       "params": {}
     }'
   ```

## Next Steps

After testing with the Inspector:
1. Try the Ollama host: `python host/run_ollama.py`
2. Experiment with the example client: `python client/example_usage.py`
3. Build your own MCP client or host!