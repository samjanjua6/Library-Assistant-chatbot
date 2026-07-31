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
            for t in tools.tools:
                if "post-page" in t.name.lower():
                    print(f"Tool: {t.name}")
                    print(f"Desc: {t.description}")
                    print("Schema:", json.dumps(t.input_schema, indent=2))
                    print("---")
                if "search" in t.name.lower():
                    print(f"Tool: {t.name}")
                    print(f"Desc: {t.description}")
                    print("Schema:", json.dumps(t.input_schema, indent=2))
                    print("---")

if __name__ == "__main__":
    asyncio.run(main())
