import streamlit as st


def auth_and_onboarding_guard(
    *,
    require_auth: bool = True,
    require_onboarding_complete: bool = False,
    redirect_login: str = "pages/loginPage.py",
    redirect_onboarding: str = "pages/informationCollection.py",
):
    """
    Centralized auth + onboarding guard for Streamlit pages.
    Uses ONLY st.session_state (no Supabase calls).

    Parameters:
    - require_auth: block unauthenticated users
    - require_onboarding_complete: block users who haven't finished onboarding
    """

    # 1️⃣ Auth check
    if require_auth and not st.session_state.get("authenticated"):
        st.switch_page(redirect_login)
        st.stop()

    # 2️⃣ User object check
    user = st.session_state.get("user")
    if require_auth and not user:
        st.switch_page(redirect_login)
        st.stop()

    # 3️⃣ Onboarding check (optional)
    if require_onboarding_complete:
        if not st.session_state.get("onboarding_complete", False):
            st.switch_page(redirect_onboarding)
            st.stop()

    # ✅ Passed all checks
    return True
