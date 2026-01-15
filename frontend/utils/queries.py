from supabase import create_client
import os

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


def get_tenders():
    response = (
        supabase
        .table("tender_documents")
        .select("*")
        .execute()
    )
    return response.data or []


def get_bids():
    response = (
        supabase
        .table("bid_history")
        .select("*")
        .execute()
    )
    return response.data or []