import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from analyzer import load_and_process, get_summary, get_category_breakdown, get_monthly_trend, detect_anomalies, get_top_expenses, get_saving_tips
from report_generator import generate_pdf_report

st.set_page_config(
    page_title="BankSense - Finance Analyzer",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    .metric-card {
        background: white;
        padding: 1rem 1.2rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    .metric-label { font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { font-size: 24px; font-weight: 700; color: #1e293b; margin-top: 4px; }
    .metric-delta { font-size: 12px; margin-top: 4px; }
    .anomaly-box {
        background: #fff5f5;
        border-left: 4px solid #e53e3e;
        padding: 0.6rem 1rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 8px;
        font-size: 13px;
    }
    .tip-box {
        background: #f0fdf4;
        border-left: 4px solid #22c55e;
        padding: 0.6rem 1rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 8px;
        font-size: 13px;
    }
    .section-header {
        font-size: 16px;
        font-weight: 600;
        color: #1e293b;
        margin: 1.2rem 0 0.6rem 0;
        padding-bottom: 6px;
        border-bottom: 2px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/bank-building.png", width=60)
    st.title("BankSense")
    st.caption("Personal Finance Analyzer")
    st.divider()

    uploaded_file = st.file_uploader(
        "Upload Bank Statement (CSV)",
        type=["csv"],
        help="CSV with columns: Date, Description, Amount, Type"
    )

    st.divider()
    if st.button("📄 Use Sample Data", use_container_width=True):
        st.session_state['use_sample'] = True

    st.divider()
    st.markdown("**CSV Format Required:**")
    st.code("Date,Description,Amount,Type\n2024-01-01,Salary,50000,Credit\n2024-01-02,Swiggy,-450,Debit", language="text")

# Load data
df = None
if uploaded_file:
    df = load_and_process(uploaded_file)
    if df is None:
        st.error("❌ Could not parse your CSV. Please check the format.")
elif st.session_state.get('use_sample'):
    df = load_and_process("sample_data.csv")

# Main content
if df is None:
    st.markdown("## 💳 Welcome to BankSense")
    st.markdown("##### AI-powered personal finance analyzer for smarter money decisions")
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info("📊 **Auto-categorize** transactions into 10 categories")
    with col2:
        st.info("🔍 **Detect anomalies** using Z-score statistical analysis")
    with col3:
        st.info("📈 **Visualize trends** with interactive charts")
    with col4:
        st.info("📄 **Export PDF** reports with saving recommendations")
    st.divider()
    st.markdown("👈 **Upload your bank statement CSV or click 'Use Sample Data' to get started**")

else:
    summary = get_summary(df)
    category_df = get_category_breakdown(df)
    monthly_df = get_monthly_trend(df)
    anomalies_df = detect_anomalies(df)
    top_expenses = get_top_expenses(df)
    tips = get_saving_tips(category_df)

    # Header
    st.markdown("## 💳 BankSense Dashboard")
    date_range = f"{df['Date'].min().strftime('%d %b %Y')} — {df['Date'].max().strftime('%d %b %Y')}"
    st.caption(f"Analysis Period: {date_range} | {summary['total_transactions']} transactions")
    st.divider()

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Total Income", f"₹{summary['total_income']:,.0f}")
    with col2:
        st.metric("💸 Total Expenses", f"₹{summary['total_expense']:,.0f}")
    with col3:
        delta_color = "normal" if summary['net_savings'] >= 0 else "inverse"
        st.metric("🏦 Net Savings", f"₹{summary['net_savings']:,.0f}")
    with col4:
        st.metric("📊 Savings Rate", f"{summary['savings_rate']:.1f}%")

    st.divider()

    # Charts Row 1
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<div class="section-header">📈 Monthly Income vs Expense</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Income', x=monthly_df['Month'], y=monthly_df['Income'],
                             marker_color='#22c55e', opacity=0.85))
        fig.add_trace(go.Bar(name='Expense', x=monthly_df['Month'], y=monthly_df['Expense'],
                             marker_color='#ef4444', opacity=0.85))
        fig.add_trace(go.Scatter(name='Savings', x=monthly_df['Month'], y=monthly_df['Savings'],
                                 mode='lines+markers', line=dict(color='#3b82f6', width=2.5),
                                 marker=dict(size=7)))
        fig.update_layout(
            barmode='group', height=300, margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation='h', y=1.1), plot_bgcolor='white',
            yaxis=dict(gridcolor='#f1f5f9'), xaxis=dict(gridcolor='#f1f5f9')
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">🗂️ Spending by Category</div>', unsafe_allow_html=True)
        fig2 = px.pie(category_df, values='Amount', names='Category',
                      color_discrete_sequence=px.colors.qualitative.Set3,
                      hole=0.45)
        fig2.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0),
                           legend=dict(font=dict(size=10)))
        fig2.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig2, use_container_width=True)

    # Charts Row 2
    col1, col2 = st.columns([2, 3])

    with col1:
        st.markdown('<div class="section-header">🔍 Anomaly Detection</div>', unsafe_allow_html=True)
        if len(anomalies_df) == 0:
            st.success("✅ No anomalies detected! Your spending looks normal.")
        else:
            st.warning(f"⚠️ {len(anomalies_df)} unusual transaction(s) detected")
            for _, row in anomalies_df.head(4).iterrows():
                st.markdown(f"""<div class="anomaly-box">
                    <b>{row['Description']}</b><br>
                    ₹{row['Amount']:,.0f} | {row['Category']} | Z-Score: {row['ZScore']:.1f}
                </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-header">💡 Smart Saving Tips</div>', unsafe_allow_html=True)
        for tip in tips:
            st.markdown(f'<div class="tip-box">{tip}</div>', unsafe_allow_html=True)

    # Top Expenses Table
    st.divider()
    st.markdown('<div class="section-header">🔝 Top 10 Highest Expenses</div>', unsafe_allow_html=True)
    top_display = top_expenses.copy()
    top_display['Date'] = top_display['Date'].dt.strftime('%d %b %Y')
    top_display['Amount'] = top_display['Amount'].apply(lambda x: f"₹{x:,.0f}")
    st.dataframe(top_display, use_container_width=True, hide_index=True)

    # Category Bar Chart
    st.divider()
    st.markdown('<div class="section-header">📊 Category-wise Spending Breakdown</div>', unsafe_allow_html=True)
    fig3 = px.bar(category_df.sort_values('Amount'), x='Amount', y='Category',
                  orientation='h', color='Amount',
                  color_continuous_scale=['#bfdbfe', '#3b82f6', '#1d4ed8'],
                  text='Amount')
    fig3.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
    fig3.update_layout(height=350, margin=dict(l=0, r=60, t=10, b=0),
                       showlegend=False, plot_bgcolor='white',
                       coloraxis_showscale=False,
                       xaxis=dict(gridcolor='#f1f5f9'))
    st.plotly_chart(fig3, use_container_width=True)

    # PDF Download
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        pdf_bytes = generate_pdf_report(summary, category_df, monthly_df, anomalies_df, tips)
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_bytes,
            file_name=f"banksense_report_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
