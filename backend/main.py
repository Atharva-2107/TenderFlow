from fastapi import FastAPI
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

app = FastAPI()

# 2. Connect to the database
supabase: Client = create_client(URL, KEY)

@app.get("/")
def home():
    return {"message": "TenderFlow Backend is Running!"}

@app.get("/tenders")
def get_tenders():
    # This pulls data from your Supabase 'tenders' table
    response = supabase.table("tenders").select("*").execute()
    return response.data

if __name__ == "__main__":
    import uvicorn
    # This starts the server on port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)