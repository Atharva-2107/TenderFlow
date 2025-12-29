import streamlit as st

import streamlit as st

def auth_and_onboarding_guard(supabase):
    user = st.session_state.get("user")

    if not user:
        st.switch_page("pages/loginPage.py")
        st.stop()

    user_id = user.id

    res = (
        supabase
        .table("profiles")
        .select("onboarding_step, onboarding_complete")
        .eq("id", user_id)
        .execute()   # ❌ NO .single()
    )

    # 🚨 NO PROFILE ROW YET → start onboarding
    if not res.data or len(res.data) == 0:
        st.session_state["onboarding_step"] = 1
        st.session_state["onboarding_complete"] = False
        st.switch_page("pages/informationCollection.py")
        st.stop()

    profile = res.data[0]

    onboarding_complete = bool(profile.get("onboarding_complete"))
    step = int(profile.get("onboarding_step") or 1)

    st.session_state["onboarding_step"] = step
    st.session_state["onboarding_complete"] = onboarding_complete

    if onboarding_complete:
        st.switch_page("pages/dashboard.py")
        st.stop()

    routes = {
        1: "pages/informationCollection.py",
        2: "pages/informationCollection_2.py",
        3: "pages/informationCollection_3.py",
        4: "pages/informationCollection_4.py",
    }

    st.switch_page(routes.get(step, "pages/informationCollection.py"))
    st.stop()
