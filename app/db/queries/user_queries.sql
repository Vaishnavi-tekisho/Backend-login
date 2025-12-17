-- User Queries for Supabase
-- These are reference queries; actual queries are done via Supabase REST API

-- Get user by email
-- supabase.table("users").select("*").eq("email", email).execute()

-- Get user by ID
-- supabase.table("users").select("*").eq("id", user_id).execute()

-- Create user
-- supabase.table("users").insert({...}).execute()

-- Update user
-- supabase.table("users").update({...}).eq("id", user_id).execute()

-- Update last login
-- supabase.table("users").update({"last_login": timestamp}).eq("id", user_id).execute()

-- Store password reset OTP
-- supabase.table("users").update({"reset_otp": hashed_otp, "reset_otp_expiry": expiry}).eq("email", email).execute()

-- Get stored OTP
-- supabase.table("users").select("reset_otp, reset_otp_expiry").eq("email", email).execute()

-- Invalidate OTP
-- supabase.table("users").update({"reset_otp": None, "reset_otp_expiry": None}).eq("email", email).execute()

-- Update password
-- supabase.table("users").update({"password": hashed_password}).eq("email", email).execute()
