import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_core.tools import tool
import sys
import os

class MCPToolManager:
    def __init__(self):
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=[os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts", "mcp_server.py")]
        )
        self.session = None
        self._exit_stack = None

    async def _invoke_mcp(self, name: str, arguments: dict) -> str:
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments)
                if result and len(result.content) > 0:
                    return result.content[0].text
                return "No result from MCP tool."

mcp_manager = MCPToolManager()

@tool
def mcp_vector_search(query: str) -> str:
    """Search internal market research documents via MCP."""
    return asyncio.run(mcp_manager._invoke_mcp("vector_search", {"query": query}))

@tool
def mcp_web_search(query: str) -> str:
    """Web search for market research via MCP."""
    return asyncio.run(mcp_manager._invoke_mcp("mock_web_search", {"query": query}))

def get_mcp_tools():
    """Return the available tools via MCP."""
    return [mcp_vector_search, mcp_web_search]
