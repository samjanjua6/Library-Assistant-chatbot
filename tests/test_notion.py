import asyncio
import os
import sys
import logging

logging.basicConfig(level=logging.DEBUG)

from app.library.notion_mcp import search_notion_policy

async def main():
    print("Testing...")
    try:
        res = await search_notion_policy("test")
        print("Result:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
