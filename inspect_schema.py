from src.core.database import get_supabase
import json

def check_schema():
    output = []
    try:
        supabase = get_supabase()
        
        # Test users_login
        output.append("\n--- Columns in users_login ---")
        res = supabase.table("users_login").select("*").limit(1).execute()
        if res.data:
            for key in sorted(res.data[0].keys()):
                output.append(f"  - {key}")
        else:
            output.append("No data in users_login.")
        
        # Test users_profile_login
        output.append("\n--- Columns in users_profile_login ---")
        res = supabase.table("users_profile_login").select("*").limit(1).execute()
        if res.data:
            for key in sorted(res.data[0].keys()):
                output.append(f"  - {key}")
        else:
            output.append("No data in users_profile_login.")

    except Exception as e:
        output.append(f"Diagnostic failed: {e}")

    with open("schema_results.txt", "w") as f:
        f.write("\n".join(output))

if __name__ == "__main__":
    check_schema()
