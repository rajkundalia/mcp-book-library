"""
Streamable HTTP Transport Server
Demonstrates MCP server using HTTP POST endpoint (not SSE)
"""
import json

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from registry import MCPRegistry

app = FastAPI(title="MCP Library HTTP Server")
registry = MCPRegistry()


@app.post("/mcp")
async def handle_mcp_request(request: Request):
    """
    Single HTTP POST endpoint for all MCP JSON-RPC requests.
    Routes requests to appropriate handlers based on method.
    """
    try:
        body = await request.json()

        # JSON-RPC 2.0 structure
        jsonrpc = body.get("jsonrpc")
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        if jsonrpc != "2.0":
            raise HTTPException(status_code=400, detail="Invalid JSON-RPC version")

        # Route based on method
        result = None

        if method == "resources/list":
            result = registry.list_resources()

        elif method == "resources/read":
            uri = params.get("uri")
            if not uri:
                raise HTTPException(status_code=400, detail="Missing uri parameter")
            resource_data = registry.read_resource(uri)
            result = {
                "contents": [{
                    "uri": resource_data["uri"],
                    "mimeType": resource_data["mimeType"],
                    "text": resource_data["text"]
                }]
            }

        elif method == "prompts/list":
            result = {"prompts": registry.list_prompts()}

        elif method == "prompts/get":
            name = params.get("name")
            arguments = params.get("arguments", {})
            if not name:
                raise HTTPException(status_code=400, detail="Missing name parameter")
            prompt_data = registry.get_prompt(name, arguments)
            result = {
                "messages": [{
                    "role": "user",
                    "content": {"type": "text", "text": prompt_data["prompt"]}
                }]
            }

        elif method == "tools/list":
            result = {"tools": registry.list_tools()}

        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {})
            if not name:
                raise HTTPException(status_code=400, detail="Missing name parameter")
            tool_result = registry.call_tool(name, arguments)
            result = {
                "content": [{
                    "type": "text",
                    "text": json.dumps(tool_result, indent=2)
                }]
            }

        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")

        # Return JSON-RPC response
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        })

    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id if 'request_id' in locals() else None,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }, status_code=500)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "mcp-library"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
