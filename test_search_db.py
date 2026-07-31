import asyncio
import os
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    env = os.environ.copy()
    base_dir = os.getcwd()
    bin_path = os.path.join(base_dir, "node_modules", "@notionhq", "notion-mcp-server", "bin", "cli.mjs")
    server_params = StdioServerParameters(command="node", args=[bin_path], env=env)
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            search_tool = next(t for t in tools.tools if "post-search" in t.name.lower())
            
            res = await session.call_tool(search_tool.name, arguments={
                "query": "Daily Library Reports"
            })
            if not res.is_error:
                text_content = [c.text for c in res.content if c.type == "text"]
                print(json.dumps(json.loads(text_content[0]), indent=2))
            else:
                print("Error:", res.content)

if __name__ == "__main__":
    asyncio.run(main())
