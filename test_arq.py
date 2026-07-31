import asyncio
from app.worker.tasks import generate_and_email_report

async def main():
    ctx = {"job_try": 1}
    print("Testing generate_and_email_report...")
    res = await generate_and_email_report(ctx)
    print("Result:", res)

if __name__ == "__main__":
    import os
    # We set this to prevent actual emailing if the user has real SMTP creds,
    # OR we let it send an email to themselves.
    # The user wants to confirm the entry appears in Notion.
    asyncio.run(main())
