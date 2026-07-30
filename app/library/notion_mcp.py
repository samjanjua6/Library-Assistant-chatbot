import os
import json
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from ..core.config import settings

logger = logging.getLogger(__name__)

async def search_notion_policy(query: str) -> str | None:
    """
    Connect to the Notion MCP server via stdio, search for the query, and return the result.
    If no result is found or if the token is missing, returns None.
    """
    if not settings.NOTION_API_TOKEN:
        logger.warning("NOTION_API_TOKEN is not set. Skipping Notion MCP search.")
        return None

    env = os.environ.copy()
    env["NOTION_API_TOKEN"] = settings.NOTION_API_TOKEN
    env["NOTION_TOKEN"] = settings.NOTION_API_TOKEN
    env["NOTION_API_KEY"] = settings.NOTION_API_TOKEN

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    bin_path = os.path.join(base_dir, "node_modules", "@notionhq", "notion-mcp-server", "bin", "cli.mjs")
    
    server_params = StdioServerParameters(
        command="node",
        args=[bin_path],
        env=env
    )

    try:
        combined_text = None
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                tools_response = await session.list_tools()
                
                # Find a search tool
                search_tool = None
                for t in tools_response.tools:
                    if "search" in t.name.lower():
                        search_tool = t
                        break

                if not search_tool:
                    logger.error("No search tool found in Notion MCP server.")
                    return None

                # Execute the tool
                result = await session.call_tool(
                    search_tool.name,
                    arguments={"query": query}
                )

                if result.is_error:
                    logger.error(f"Notion MCP error: {result.content}")
                else:
                    text_content = []
                    for content in result.content:
                        if content.type == "text":
                            text_content.append(content.text)

                    extracted = "\n".join(text_content).strip()

                    if extracted and extracted != "[]" and "No results" not in extracted:
                        try:
                            # The search tool returns a JSON list of pages.
                            data = json.loads(extracted)
                            if "status" in data and data["status"] >= 400:
                                # It's an error response (e.g. 401 Unauthorized)
                                logger.error(f"Notion API error: {extracted}")
                            else:
                                results = data.get("results", [])
                                if results:
                                    # Fetch the first page's markdown
                                    page_id = results[0].get("id")
                                    if page_id:
                                        md_tool = next((t for t in tools_response.tools if "retrieve-page-markdown" in t.name.lower()), None)
                                        if md_tool:
                                            md_result = await session.call_tool(md_tool.name, arguments={"page_id": page_id})
                                            if not md_result.is_error:
                                                md_text_content = [c.text for c in md_result.content if c.type == "text"]
                                                combined_text = "\n".join(md_text_content).strip()
                                            else:
                                                logger.error(f"Error fetching markdown: {md_result.content}")
                        except Exception as parse_e:
                            logger.error(f"Error parsing Notion search result: {parse_e}")
                            combined_text = extracted
                        
        return combined_text
        
    except Exception as e:
        logger.error(f"Failed to communicate with Notion MCP: {e}")
        import traceback
        traceback.print_exc()
        if hasattr(e, 'exceptions'):
            for sub_e in e.exceptions:
                logger.error(f"Sub-exception: {sub_e}")
        return None

async def write_daily_report_to_notion(date_str: str, new_borrows: int, returns: int, overdue: int) -> bool:
    """
    Connect to Notion MCP, find 'Daily Library Reports' database/page, and append a daily summary.
    Returns True if successful, False otherwise.
    """
    if not settings.NOTION_API_TOKEN:
        logger.warning("NOTION_API_TOKEN is not set. Skipping Notion daily report write.")
        return False

    env = os.environ.copy()
    env["NOTION_API_TOKEN"] = settings.NOTION_API_TOKEN
    env["NOTION_TOKEN"] = settings.NOTION_API_TOKEN
    env["NOTION_API_KEY"] = settings.NOTION_API_TOKEN

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    bin_path = os.path.join(base_dir, "node_modules", "@notionhq", "notion-mcp-server", "bin", "cli.mjs")
    
    server_params = StdioServerParameters(
        command="node",
        args=[bin_path],
        env=env
    )

    try:
        success = False
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_response = await session.list_tools()
                
                # Search for the parent page/database
                search_tool = next((t for t in tools_response.tools if "post-search" in t.name.lower()), None)
                if not search_tool:
                    logger.error("No search tool found in Notion MCP server.")
                    return False

                search_res = await session.call_tool(search_tool.name, arguments={"query": "Daily Library Reports"})
                
                if search_res.is_error:
                    logger.error(f"Notion MCP search error: {search_res.content}")
                else:
                    text_content = [c.text for c in search_res.content if c.type == "text"]
                    extracted = "\n".join(text_content).strip()
                    
                    data = json.loads(extracted)
                    results = data.get("results", [])
                    if not results:
                        logger.warning("Could not find 'Daily Library Reports' in Notion. Please create it and share it with your integration.")
                    else:
                        parent_obj = results[0]
                        parent_id = parent_obj.get("id")
                        parent_type = "database_id" if parent_obj.get("object") == "database" else "page_id"

                        # Create the page
                        post_page_tool = next((t for t in tools_response.tools if "post-page" in t.name.lower()), None)
                        if not post_page_tool:
                            logger.error("No post-page tool found.")
                        else:
                            args = {
                                "parent": {
                                    "type": parent_type,
                                    parent_type: parent_id
                                },
                                "properties": {
                                    "title": {
                                        "title": [
                                            {"type": "text", "text": {"content": f"Daily Summary - {date_str}"}}
                                        ]
                                    }
                                },
                                "children": [
                                    {
                                        "type": "paragraph",
                                        "paragraph": {
                                            "rich_text": [{"type": "text", "text": {"content": f"📚 Books Borrowed: {new_borrows}"}}]
                                        }
                                    },
                                    {
                                        "type": "paragraph",
                                        "paragraph": {
                                            "rich_text": [{"type": "text", "text": {"content": f"📥 Books Returned: {returns}"}}]
                                        }
                                    },
                                    {
                                        "type": "paragraph",
                                        "paragraph": {
                                            "rich_text": [{"type": "text", "text": {"content": f"⚠️ Overdue Today: {overdue}"}}]
                                        }
                                    }
                                ]
                            }
                            
                            create_res = await session.call_tool(post_page_tool.name, arguments=args)
                            if create_res.is_error:
                                logger.error(f"Error creating Notion page: {create_res.content}")
                            else:
                                logger.info(f"Successfully wrote daily report to Notion for {date_str}.")
                                success = True
        return success
    except Exception as e:
        logger.error(f"Failed to communicate with Notion MCP while writing report: {e}")
        import traceback
        traceback.print_exc()
        return False

