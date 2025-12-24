from fastapi import Header, HTTPException, Depends
from supabase import create_client, Client
import os
from dotenv import load_dotenv
# 1. Load the secrets from the .env file into your computer's memory
load_dotenv()
# 2. Assign them to variables
# The names inside the quotes MUST match exactly what you wrote in your .env file
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
LLAMA_KEY = os.getenv("LLAMAPARSE_CLOUD_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_current_user(authorization: str = Header(None)):
    """
    This function intercepts the 'Authorization' header 
    to check if the user is actually logged in.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header found")
    
    # The header usually looks like "Bearer [token]"
    token = authorization.split(" ")[1] if " " in authorization else authorization
    
    try:
        # Ask Supabase: "Is this token valid?"
        user = supabase.auth.get_user(token)
        return user.user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")