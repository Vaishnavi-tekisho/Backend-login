import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: SUPABASE_URL or SUPABASE_KEY not set in .env")
    exit(1)

async def check_column():
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("1. Testing 'acc_updated_at' (Correct spelling)...")
    try:
        supabase.table("users_login").select("acc_updated_at").limit(1).execute()
        print("   -> FOUND!")
    except Exception as e:
        print(f"   -> NOT FOUND. Error: {str(e)[:100]}")

    print("\n2. Testing 'acc_upadted_at' (User typo in chat)...")
    try:
        supabase.table("users_login").select("acc_upadted_at").limit(1).execute()
        print("   -> FOUND! The column is misspelled in the DB.")
    except Exception as e:
        print(f"   -> NOT FOUND.")

    print("\n3. Testing 'updated_at' (Common mapping)...")
    try:
        supabase.table("users_login").select("updated_at").limit(1).execute()
        print("   -> FOUND! Maybe it's named 'updated_at'?")
    except Exception as e:
        print(f"   -> NOT FOUND.")

if __name__ == "__main__":
    asyncio.run(check_column())
