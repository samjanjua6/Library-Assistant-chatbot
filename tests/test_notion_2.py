import asyncio
import os
import sys
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(level=logging.DEBUG)

async def main():
    print("Testing MCP client directly...")
    try:
        env = os.environ.copy()
        base_dir = os.getcwd()
        bin_path = os.path.join(base_dir, "node_modules", "@notionhq", "notion-mcp-server", "bin", "cli.mjs")
        server_params = StdioServerParameters(command="node", args=[bin_path], env=env)
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                search_tool = next((t for t in tools.tools if "search" in t.name.lower()), None)
                print("Found tool:", search_tool.name)
                
                result = await session.call_tool(search_tool.name, arguments={"query": "test"})
                print("Result:", result)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
