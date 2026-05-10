import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from typing import List

# Import tools from the app
from app.agents.tools import get_tools

server = Server("market-research-mcp")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """
    List available tools from the app.
    """
    tools = get_tools()
    mcp_tools = []
    for t in tools:
        mcp_tools.append(Tool(
            name=t.name,
            description=t.description,
            inputSchema=t.args_schema.schema() if t.args_schema else {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        ))
    return mcp_tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """
    Handle tool execution requests.
    """
    tools = {t.name: t for t in get_tools()}
    
    if name not in tools:
        raise ValueError(f"Unknown tool: {name}")
        
    tool = tools[name]
    # Tool invocation
    # Langchain tools can be invoked directly
    result = tool.invoke(arguments)
    
    return [TextContent(type="text", text=str(result))]

async def main():
    """Run the MCP server via stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
