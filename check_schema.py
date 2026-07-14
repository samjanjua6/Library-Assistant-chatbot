import asyncio
from sqlalchemy import text
from app.core.database import engine

def check_schema():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT column_name, is_nullable, data_type FROM information_schema.columns WHERE table_name = 'chat_sessions'"))
            for row in result:
                print(row)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
