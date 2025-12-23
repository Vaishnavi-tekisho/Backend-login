# Authentication Logic Documentation

## 1. Signup Flow (`/auth/signup`)
1.  **Check Existence**: Queries `users_login` to see if the email is already registered.
2.  **Hash Password**: Hashes the provided password using `bcrypt`.
3.  **Create Login Record**: Inserts a new row into `users_login` with email and hashed password.
4.  **Create Profile Record**: Inserts a corresponding row into `users_profile_login` with the `user_id`, location, and default stats.
5.  **Trigger Verification**: Uses the `VerificationService` to send a verification email.
6.  **Response**: Returns an access token and the combined user data.

## 2. Login Flow (`/auth/login`)
1.  **User Lookup**: Queries `users_login` to find a user with the provided email.
    *   **Current Issue**: This query uses the *public* Supabase client. If Row Level Security (RLS) is enabled (which it is), this query fails to find the user because unauthenticated users are not allowed to read the `users_login` table.
2.  **Password Verification**: If a user is found, it verifies the provided password against the stored hash.
3.  **Update Stats**: Updates `users_profile_login` with the new login time and IP address.
4.  **Token Generation**: Generates a JWT access token.
5.  **Response**: Returns the token and user profile.

## 3. Google OAuth Flow
1.  **Initiate (`/auth/google`)**: Redirects the user to Google's OAuth consent screen.
2.  **Callback (`/auth/callback`)**:
    *   Receives an authorization `code` from Google.
    *   Exchanges the code for an ID Token and Access Token.
    *   Verifies the Google ID Token to extract the user's email.
3.  **User Handling**:
    *   **Existing User**: Updates their login stats in `users_profile_login`.
    *   **New User**: Creates a new account in `users_login` (without a password) and `users_profile_login`.
4.  **Redirect**: Redirects the user back to the frontend with the access token in the URL params.
