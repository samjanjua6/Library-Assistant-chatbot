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
            tools_response = await session.list_tools()
            
            search_tool = next((t for t in tools_response.tools if "post-search" in t.name.lower()), None)
            result = await session.call_tool(search_tool.name, arguments={"query": "test"})
            
            if not result.is_error:
                text_content = []
                for content in result.content:
                    if content.type == "text":
                        text_content.append(content.text)
                extracted = "\n".join(text_content).strip()
                
                print("Search returned:", extracted[:100], "...")
                
                try:
                    data = json.loads(extracted)
                    results = data.get("results", [])
                    if results:
                        page_id = results[0].get("id")
                        print("Found page ID:", page_id)
                        
                        md_tool = next((t for t in tools_response.tools if "retrieve-page-markdown" in t.name.lower()), None)
                        md_result = await session.call_tool(md_tool.name, arguments={"page_id": page_id})
                        if not md_result.is_error:
                            print("Success fetching Markdown!")
                            md_text = [c.text for c in md_result.content if c.type == "text"]
                            print("\n".join(md_text)[:100], "...")
                        else:
                            print("Error fetching markdown:", md_result.content)
                    else:
                        print("No pages found")
                except Exception as e:
                    print("JSON parse error:", e)

if __name__ == "__main__":
    asyncio.run(main())
