import streamlit as st
from supabase import create_client
import os

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)


@st.cache_data(ttl=15)
def get_tenders():
    response = (
        supabase
        .table("tender_documents")
        .select("*")
        .execute()
    )
    return response.data or []


@st.cache_data(ttl=15)
def get_bids():
    response = (
        supabase
        .table("bid_history")
        .select("*")
        .execute()
    )
    return response.data or []


@st.cache_data(ttl=15)
def get_generated_tenders():
    response = (
        supabase
        .table("generated_tenders")
        .select("*")
        .execute()
    )
    return response.data or []


def get_pending_tenders():
    """Fetch only pending tenders with minimal data - NOT cached for real-time updates"""
    response = (
        supabase
        .table("generated_tenders")
        .select("id, project_name, status")
        .eq("status", "pending")
        .execute()
    )
    return response.data or []


def get_pending_bids():
    """Fetch pending bids (won is null) - NOT cached for real-time updates"""
    response = (
        supabase
        .table("bid_history_v2")
        .select("id, project_name, category, won")
        .execute()
    )
    # Filter for NULL won values - Supabase returns None for SQL NULL
    data = response.data or []
    return [bid for bid in data if bid.get("won") is None]