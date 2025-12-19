import streamlit as st
import pandas as pd
import plotly.express as px # New tool for charts!

# 1. Page Configuration
st.set_page_config(
    page_title="TenderFlow | Hackathon Edition",
    page_icon="🌊",
    layout="wide"
)

# 2. Sidebar Navigation
st.sidebar.title("🌊 TenderFlow")
st.sidebar.markdown("---")
page = st.sidebar.radio("Go to", ["Dashboard", "Submit a Bid", "Analytics", "Settings"])

# Mock Data (In a real app, this would come from a database)
if 'tender_data' not in st.session_state:
    st.session_state.tender_data = pd.DataFrame({
        "ID": ["T-101", "T-102", "T-103"],
        "Project Name": ["Smart City Lighting", "Highway Expansion", "School WiFi Setup"],
        "Budget ($)": [50000, 1200000, 15000],
        "Bids Received": [5, 12, 3],
        "Status": ["Open", "Under Review", "Open"]
    })

# 3. Main Logic
if page == "Dashboard":
    st.title("📊 Tender Management Dashboard")
    st.write("Real-time overview of active procurement flows.")
    
    # Key Metrics at the top
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Tenders", len(st.session_state.tender_data))
    col2.metric("Total Value", f"${st.session_state.tender_data['Budget ($)'].sum():,}")
    col3.metric("Avg. Bids/Project", round(st.session_state.tender_data['Bids Received'].mean(), 1))

    st.markdown("---")
    st.subheader("Current Tenders")
    st.dataframe(st.session_state.tender_data, use_container_width=True)

elif page == "Submit a Bid":
    st.title("📝 Bid Submission Portal")
    st.info("Ensure all financial disclosures are attached before submitting.")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("Company Name", placeholder="e.g. Acme Corp")
            tender_id = st.selectbox("Select Target Tender", st.session_state.tender_data["ID"])
        with col2:
            bid_amount = st.number_input("Your Bid Amount ($)", min_value=0, step=1000)
            contact_email = st.text_input("Representative Email")

        message = st.text_area("Value Proposition (Why choose you?)")
        uploaded_file = st.file_uploader("Upload Technical Proposal (PDF)")

        if st.button("Submit Official Bid", type="primary"):
            if company_name and bid_amount > 0 and contact_email:
                st.success(f"Success! Bid for {company_name} has been logged in the flow.")
                st.balloons()
            else:
                st.warning("Please fill out the required fields.")

elif page == "Analytics":
    st.title("📈 Tender Analytics")
    st.write("Comparison of budget allocation across projects.")
    
    # Create a simple bar chart using Plotly
    fig = px.bar(
        st.session_state.tender_data, 
        x="Project Name", 
        y="Budget ($)", 
        color="Status",
        title="Budget Distribution by Project",
        template="seaborn"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    st.subheader("Bidding Competition")
    st.bar_chart(st.session_state.tender_data.set_index("Project Name")["Bids Received"])

elif page == "Settings":
    st.title("⚙️ System Settings")
    st.checkbox("Enable Email Notifications")
    st.checkbox("Dark Mode Interface")
    if st.button("Export Audit Log"):
        st.write("Log exported to CSV...")