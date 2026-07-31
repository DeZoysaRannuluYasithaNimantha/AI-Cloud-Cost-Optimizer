import os
import pandas as pd
import plotly.express as px
import streamlit as st
from openai import OpenAI

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI Cloud Cost Optimizer",
    page_icon="☁️",
    layout="wide"
)

# ---------------------------------------------------------
# API Key Initialization (Streamlit Secrets / Local Fallback)
# ---------------------------------------------------------
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

# Sidebar - Settings & API Status
st.sidebar.title("⚙️ Settings")
if api_key:
    st.sidebar.success("OpenAI API Key Detected", icon="✅")
    client = OpenAI(api_key=api_key)
else:
    st.sidebar.warning("No OpenAI API Key found. Add `OPENAI_API_KEY` to Secrets or environment.", icon="⚠️")
    client = None

# ---------------------------------------------------------
# Header Section
# ---------------------------------------------------------
st.title("☁️ AI Cloud Cost Optimizer")
st.markdown(
    "Upload your multi-cloud billing export (CSV) to analyze expenditure patterns "
    "and generate automated AI optimization recommendations."
)

# ---------------------------------------------------------
# File Upload / Sample Loader
# ---------------------------------------------------------
uploaded_file = st.file_uploader("Upload Cloud Bill (CSV)", type=["csv"])

df = None
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
elif os.path.exists("sample_cloud_bill.csv"):
    st.info("💡 Showing sample bill data (`sample_cloud_bill.csv`). Upload a custom CSV above to override.")
    df = pd.read_csv("sample_cloud_bill.csv")

if df is not None:
    # Validate expected columns
    required_cols = {"Service", "CloudProvider", "MonthlyCost"}
    if not required_cols.issubset(set(df.columns)):
        st.error(f"Missing required columns in CSV. Required: {required_cols}")
        st.stop()

    # Clean numeric data
    df["MonthlyCost"] = pd.to_numeric(df["MonthlyCost"], errors="coerce").fillna(0)

    # ---------------------------------------------------------
    # Key Performance Indicators (KPIs)
    # ---------------------------------------------------------
    st.markdown("### 📊 Spend Overview")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    total_spend = df["MonthlyCost"].sum()
    top_provider = df.groupby("CloudProvider")["MonthlyCost"].sum().idxmax()
    top_service = df.groupby("Service")["MonthlyCost"].sum().idxmax()
    resource_count = len(df)

    kpi1.metric("Total Monthly Spend", f"${total_spend:,.2f}")
    kpi2.metric("Primary Cloud Provider", top_provider)
    kpi3.metric("Highest Cost Service", top_service)
    kpi4.metric("Active Resources", resource_count)

    st.divider()

    # ---------------------------------------------------------
    # Visual Analytics (Plotly Charts)
    # ---------------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Cost by Cloud Provider")
        fig_provider = px.pie(
            df,
            values="MonthlyCost",
            names="CloudProvider",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_provider, use_container_width=True)

    with col2:
        st.subheader("Top Services by Expenditure")
        fig_service = px.bar(
            df.groupby("Service", as_index=False)["MonthlyCost"].sum().sort_values(by="MonthlyCost", ascending=False),
            x="Service",
            y="MonthlyCost",
            color="Service",
            text_auto=".2s"
        )
        fig_service.update_layout(showlegend=False)
        st.plotly_chart(fig_service, use_container_width=True)

    st.divider()

    # ---------------------------------------------------------
    # AI Optimization Recommendation Engine
    # ---------------------------------------------------------
    st.subheader("🤖 AI Cost Optimization Insights")

    if st.button("Generate AI Optimization Report", type="primary"):
        if not client:
            st.error("Cannot run analysis without an OpenAI API Key. Add it to Streamlit Secrets.")
        else:
            with st.spinner("Analyzing cloud resource utilization and billing patterns..."):
                summary_str = df.to_csv(index=False)

                prompt = f"""
                You are a Cloud FinOps Expert. Analyze the following cloud billing breakdown:

                {summary_str}

                Provide a structured report with:
                1. Executive Summary: Immediate observation of spending waste.
                2. Quick Wins (1-3 days): Direct actions like rightsizing, terminating idle resources, or turning off unused IPs.
                3. Strategic Savings (30+ days): Reserved Instances/Savings Plans, architectural changes.
                4. Estimated Monthly Savings ($ and %).
                """

                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a Cloud Cost Optimization assistant."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                    )

                    report = response.choices[0].message.content
                    st.markdown(report)

                    # Export Option
                    st.download_button(
                        label="📄 Download AI Report (.txt)",
                        data=report,
                        file_name="cloud_cost_optimization_report.txt",
                        mime="text/plain"
                    )

                except Exception as e:
                    st.error(f"API Error: {str(e)}")

    # Raw Data View
    with st.expander("🔍 View Raw CSV Data"):
        st.dataframe(df, use_container_width=True)

else:
    st.warning("Please upload a CSV file or add `sample_cloud_bill.csv` to the root folder to continue.")