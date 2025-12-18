"""
Quick script to check users in database
"""
from app.db.supabase_client import get_supabase

def check_users():
    supabase = get_supabase()
    
    # Search for users with similar email
    print("Searching for users with 'ginna' in email...")
    response = supabase.table("users_login").select("id, email, full_name").ilike("email", "%ginna%").execute()
    
    if response.data:
        print(f"\nFound {len(response.data)} user(s):")
        for user in response.data:
            print(f"  - ID: {user.get('id')}")
            print(f"    Email: {user.get('email')}")
            print(f"    Name: {user.get('full_name')}")
            print()
    else:
        print("No users found with 'ginna' in email")
    
    # Try exact match for the email from the log
    print("\nChecking exact email: ginnavaishanvi1214@gmail.com")
    response2 = supabase.table("users_login").select("id, email").eq("email", "ginnavaishanvi1214@gmail.com").execute()
    print(f"Result: {response2.data}")
    
    # Try the corrected spelling
    print("\nChecking corrected email: ginnavaishnavi1214@gmail.com")
    response3 = supabase.table("users_login").select("id, email").eq("email", "ginnavaishnavi1214@gmail.com").execute()
    print(f"Result: {response3.data}")

if __name__ == "__main__":
    check_users()
