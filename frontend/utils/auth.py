import streamlit as st

ROLE_PERMISSIONS = {
    "Bid Manager": {
        "tender_generation": True,
        "tender_analysis": True,
        "bid_generation": True,
        "risk_analysis": True
    },
    "Risk Reviewer": {
        "tender_generation": False,
        "tender_analysis": True,
        "bid_generation": False,
        "risk_analysis": True
    },
    "Executive": {
        "tender_generation": True,
        "tender_analysis": True,
        "bid_generation": True,
        "risk_analysis": True
    },
    "Procurement Officer": {
        "tender_generation": False,
        "tender_analysis": False,
        "bid_generation": False,
        "risk_analysis": False
    }
}

def can_access(feature: str) -> bool:
    role = st.session_state.get("user_role")
    return ROLE_PERMISSIONS.get(role, {}).get(feature, False)
