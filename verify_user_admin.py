from app.db.supabase_client import get_supabase_admin

def check_user_admin():
    print("Checking users loosely with admin client...")
    supabase = get_supabase_admin()
    
    # List first 10 users
    print("\n--- First 10 Users ---")
    res = supabase.table("users_login").select("id, email").limit(10).execute()
    for u in res.data:
        print(f"User: {u['email']}")
        
    # Search for 'ginna'
    print("\n--- Searching for 'ginna' ---")
    response = supabase.table("users_login").select("*").ilike("email", "%ginna%").execute()
    
    if response.data:
        for user in response.data:
            print(f"FOUND: {user['email']} (ID: {user['id']})")
    else:
        print("NO USERS FOUND WITH 'ginna'")

if __name__ == "__main__":
    check_user_admin()
