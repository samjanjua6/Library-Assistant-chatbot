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
            
            # 1. Search for the page
            search_tool = next(t for t in tools.tools if "post-search" in t.name.lower())
            res = await session.call_tool(search_tool.name, arguments={
                "query": "Daily Library Reports"
            })
            
            if res.is_error:
                print("Error searching:", res.content)
                return
                
            text = [c.text for c in res.content if c.type == "text"][0]
            data = json.loads(text)
            results = data.get("results", [])
            if not results:
                print("Not found")
                return
                
            parent_obj = results[0]
            parent_id = parent_obj["id"]
            parent_type = "database_id" if parent_obj["object"] == "database" else "page_id"
            
            print(f"Found parent: {parent_type} {parent_id}")
            
            # 2. Create the page
            post_page = next(t for t in tools.tools if "post-page" in t.name.lower())
            args = {
                "parent": {
                    "type": parent_type,
                    parent_type: parent_id
                },
                "properties": {
                    "title": {
                        "title": [
                            {"type": "text", "text": {"content": "Test Summary - 2026-07-30"}}
                        ]
                    }
                },
                "children": [
                    {
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {"type": "text", "text": {"content": "Books Borrowed: 5"}}
                            ]
                        }
                    }
                ]
            }
            
            create_res = await session.call_tool(post_page.name, arguments=args)
            if create_res.is_error:
                print("Error creating:", create_res.content)
            else:
                create_text = [c.text for c in create_res.content if c.type == "text"][0]
                print("Created:", create_text)

if __name__ == "__main__":
    asyncio.run(main())
