from fastapi import FastAPI
from supabase import create_client, Client

app = FastAPI()

# 1. Go to Supabase > Settings > API to find these:
URL = "https://jaleiquogmqgvwqmdnqa.supabase.co"
KEY = "sb_publishable_y-hBU82kEJcHz8wRszfhjw_YKF23_tj"

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