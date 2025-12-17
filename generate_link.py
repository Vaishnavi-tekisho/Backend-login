from app.database import supabase
from app.config import settings
import asyncio

async def main():
    email = "resettest@example.com"
    print(f"Generating reset link for {email}...")
    
    # Needs service role key to work
    if not settings.SUPABASE_SECRET_KEY:
        print("ERROR: SUPABASE_SECRET_KEY not set. Cannot generate link.")
        return

    try:
        # Check if user exists first roughly (optional, or just try to generate link and catch error)
        # But to be robust, let's create random user if needed. 
        # Actually admin.create_user is better.
        
        try:
            print("Ensuring user exists...")
            supabase.auth.admin.create_user({
                "email": email,
                "password": "TemporaryPassword123!",
                "email_confirm": True
            })
            print("Created user.")
        except Exception as e:
            print(f"User creation info (might already exist): {e}")

        res = supabase.auth.admin.generate_link({
            "type": "recovery",
            "email": email,
            "options": {
                "redirect_to": "http://localhost:5173/reset-password"
            }
        })
        
        print("\n--- GENERATED LINK ---")
        print(res.properties.action_link)
        print("----------------------\n")
        
        with open("link_output.txt", "w") as f:
            f.write(res.properties.action_link)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
