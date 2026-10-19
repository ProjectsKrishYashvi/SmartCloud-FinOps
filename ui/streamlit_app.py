import os
import pandas as pd
import streamlit as st
from pathlib import Path
import sys
import plotly.express as px
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
from lambdas.recommend.hybrid_recommender import generate_tenant_recommendations_from_billing, export_recommendations

st.set_page_config(
    page_title="SmartCloud FinOps", 
    layout="wide",
    page_icon="☁️",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-metric {
        border-left-color: #28a745;
    }
    .warning-metric {
        border-left-color: #ffc107;
    }
    .danger-metric {
        border-left-color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">☁️ SmartCloud FinOps Dashboard</h1>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Configuration")
    tenant = st.text_input("Tenant ID", value="tenantA")
    st.markdown("Upload a tenant billing CSV with columns: tenant_id,service,provider,usage_amount,unit,region,cost")
    uploaded = st.file_uploader("Upload Billing CSV", type=["csv"]) 
    run_btn = st.button("Run Recommendations")

placeholder = st.empty()

if run_btn and uploaded is not None:
    # Save uploaded file to inputs
    inputs_dir = ROOT / "inputs"
    inputs_dir.mkdir(exist_ok=True)
    csv_path = inputs_dir / f"billing_{tenant}.csv"
    csv_bytes = uploaded.getvalue()
    with open(csv_path, "wb") as f:
        f.write(csv_bytes)

    results = generate_tenant_recommendations_from_billing(tenant, csv_path)

    # Enhanced Summary with better styling
    st.subheader("📈 Summary")
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.metric("Services Analyzed", results["services_analyzed"], help="Total number of services analyzed")
    
    with c2:
        st.metric("With Savings", results["services_with_savings"], help="Services with potential savings")
    
    with c3:
        st.metric("Total Potential Savings", f"${results['total_savings']:.2f}", help="Total monthly savings potential")
    
    with c4:
        avg_savings = results['total_savings'] / max(results["services_analyzed"], 1)
        st.metric("Avg Savings per Service", f"${avg_savings:.2f}", help="Average savings per service")

    # Detailed recommendations with better formatting
    st.subheader("📋 Detailed Recommendations")
    df = pd.DataFrame([{
        "Service": r["service"],
        "Current Provider": r["current_provider"].upper(),
        "Current Cost": f"${r['current_cost']:.2f}",
        "Suggested Provider": r["suggested_provider"].upper(),
        "Suggested Cost": f"${r['suggested_cost']:.2f}",
        "Savings": f"${r['savings']:.2f}",
        "Savings %": f"{r['savings_percent']:.1f}%",
        "Strength": r["strength"],
        "Decision Source": r["decision_source"],
        "ML Confidence": f"{r['ml_confidence']:.3f}",
        "Rule Provider": r["rule_provider"].upper(),
        "ML Provider": r["ml_provider"].upper(),
        "Agreement": "✅" if r["rule_provider"] == r["ml_provider"] else "❌",
        "Rationale": r["recommendation"][:100] + "..." if len(r["recommendation"]) > 100 else r["recommendation"],
    } for r in results["recommendations"]])
    
    st.dataframe(df, use_container_width=True)
    
    # Visualizations
    st.subheader("📊 Visualizations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Savings by service
        savings_data = df.copy()
        savings_data['Savings_Numeric'] = savings_data['Savings'].str.replace('$', '').astype(float)
        
        fig_savings = px.bar(
            savings_data, 
            x='Service', 
            y='Savings_Numeric',
            title='Potential Savings by Service',
            color='Savings_Numeric',
            color_continuous_scale='Greens'
        )
        fig_savings.update_layout(yaxis_title="Savings ($)")
        st.plotly_chart(fig_savings, use_container_width=True)
    
    with col2:
        # Provider distribution
        provider_counts = df['Suggested Provider'].value_counts()
        fig_providers = px.pie(
            values=provider_counts.values,
            names=provider_counts.index,
            title='Recommended Provider Distribution'
        )
        st.plotly_chart(fig_providers, use_container_width=True)
    
    # ML vs Rule Agreement Analysis
    st.subheader("🤖 ML vs Rule Agreement Analysis")
    
    agreement_data = df[['Service', 'Rule Provider', 'ML Provider', 'ML Confidence', 'Agreement']].copy()
    agreement_data['ML Confidence Numeric'] = agreement_data['ML Confidence'].astype(float)
    
    # Agreement rate
    agreement_rate = (agreement_data['Agreement'] == '✅').mean() * 100
    st.metric("ML-Rule Agreement Rate", f"{agreement_rate:.1f}%", 
              help="Percentage of cases where ML and Rule-based decisions agree")
    
    # Confidence vs Agreement scatter
    fig_confidence = px.scatter(
        agreement_data,
        x='ML Confidence Numeric',
        y='Agreement',
        color='Service',
        title='ML Confidence vs Agreement with Rules',
        hover_data=['Service', 'Rule Provider', 'ML Provider']
    )
    st.plotly_chart(fig_confidence, use_container_width=True)

    st.subheader("Exports")
    out_dir = ROOT / "outputs" / "recommendations"
    text_file, json_file, csv_file = export_recommendations(tenant, results, out_dir, show_comparison=True)
    with open(text_file, "rb") as f:
        st.download_button("Download TXT", data=f, file_name=text_file.name)
    with open(json_file, "rb") as f:
        st.download_button("Download JSON", data=f, file_name=json_file.name)
    if csv_file and csv_file.exists():
        with open(csv_file, "rb") as f:
            st.download_button("Download CSV", data=f, file_name=csv_file.name)

else:
    st.info("Upload a billing CSV and click 'Run Recommendations'.")
