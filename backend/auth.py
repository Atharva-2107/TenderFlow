from fastapi import Header, HTTPException, Depends
from supabase import create_client, Client

# Supabase Setup (Usually you'd use Environment Variables here!)
URL = "https://jaleiquogmqgvwqmdnqa.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImphbGVpcXVvZ21xZ3Z3cW1kbnFhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYxNDcxMDIsImV4cCI6MjA4MTcyMzEwMn0.ClymJSijiioTMDVlOX1sc_lsxaMVYO62Hpd7nLCi0kU"
supabase: Client = create_client(URL, KEY)

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