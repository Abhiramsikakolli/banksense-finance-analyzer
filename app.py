import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from analyzer import load_data, get_summary, category_breakdown, monthly_trend, detect_anomalies, top_expenses, saving_tips
from report_generator import generate_pdf_report

st.set_page_config(page_title="BankSense", page_icon="💳", layout="wide")

# basic styling
st.markdown("""
<style>
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
</style>
""", unsafe_allow_html=True)

# sidebar
with st.sidebar:
    st.title("💳 BankSense")
    st.caption("Personal Finance Analyzer")
    st.divider()

    f = st.file_uploader("Upload bank statement (CSV)", type=["csv"])

    st.divider()
    if st.button("Use sample data", use_container_width=True):
        st.session_state['sample'] = True

    st.divider()
    st.markdown("**Expected CSV format:**")
    st.code("Date,Description,Amount,Type\n2024-01-01,Salary,50000,Credit\n2024-01-02,Swiggy,-450,Debit")

# load the data
df = None
if f:
    df = load_data(f)
    if df is None:
        st.error("Could not read CSV. Please check the format.")
elif st.session_state.get('sample'):
    df = load_data("sample_data.csv")

# landing page if no data
if df is None:
    st.markdown("## Welcome to BankSense")
    st.markdown("Upload your bank statement to get started")
    st.divider()

    c1, c2, c3, c4 = st.columns(4)
    c1.info("📊 Auto-categorizes transactions")
    c2.info("🔍 Detects unusual spending")
    c3.info("📈 Monthly trend charts")
    c4.info("📄 PDF report download")

    st.divider()
    st.markdown("👈 Upload a CSV or use sample data from the sidebar")

else:
    s = get_summary(df)
    cat_df = category_breakdown(df)
    mon_df = monthly_trend(df)
    anom_df = detect_anomalies(df)
    top_ex = top_expenses(df)
    tips = saving_tips(cat_df)

    # header
    st.markdown("## 💳 BankSense Dashboard")
    dr = f"{df['Date'].min().strftime('%d %b %Y')} to {df['Date'].max().strftime('%d %b %Y')}"
    st.caption(f"{dr} | {s['total_transactions']} transactions")
    st.divider()

    # summary numbers
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Income", f"₹{s['total_income']:,.0f}")
    c2.metric("Total Expenses", f"₹{s['total_expense']:,.0f}")
    c3.metric("Net Savings", f"₹{s['net_savings']:,.0f}")
    c4.metric("Savings Rate", f"{s['savings_rate']:.1f}%")

    st.divider()

    # monthly chart + pie chart
    c1, c2 = st.columns([3, 2])

    with c1:
        st.markdown("#### Monthly Income vs Expense")
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Income', x=mon_df['Month'], y=mon_df['Income'], marker_color='#22c55e', opacity=0.85))
        fig.add_trace(go.Bar(name='Expense', x=mon_df['Month'], y=mon_df['Expense'], marker_color='#ef4444', opacity=0.85))
        fig.add_trace(go.Scatter(name='Savings', x=mon_df['Month'], y=mon_df['Savings'],
                                 mode='lines+markers', line=dict(color='#3b82f6', width=2)))
        fig.update_layout(barmode='group', height=300, margin=dict(l=0,r=0,t=10,b=0),
                          legend=dict(orientation='h', y=1.1), plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("#### Spending by Category")
        fig2 = px.pie(cat_df, values='Amount', names='Category',
                      color_discrete_sequence=px.colors.qualitative.Set3, hole=0.4)
        fig2.update_layout(height=300, margin=dict(l=0,r=0,t=10,b=0))
        fig2.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig2, use_container_width=True)

    # anomalies + tips
    c1, c2 = st.columns([2, 3])

    with c1:
        st.markdown("#### Anomaly Detection")
        if len(anom_df) == 0:
            st.success("No anomalies found!")
        else:
            st.warning(f"{len(anom_df)} unusual transaction(s) found")
            for _, row in anom_df.head(4).iterrows():
                st.markdown(f"""<div class="anomaly-box">
                    <b>{row['Description']}</b><br>
                    ₹{row['Amount']:,.0f} | {row['Category']} | Z: {row['ZScore']:.1f}
                </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown("#### Saving Tips")
        for tip in tips:
            st.markdown(f'<div class="tip-box">{tip}</div>', unsafe_allow_html=True)

    # top expenses
    st.divider()
    st.markdown("#### Top 10 Expenses")
    td = top_ex.copy()
    td['Date'] = td['Date'].dt.strftime('%d %b %Y')
    td['Amount'] = td['Amount'].apply(lambda x: f"₹{x:,.0f}")
    st.dataframe(td, use_container_width=True, hide_index=True)

    # category bar chart
    st.divider()
    st.markdown("#### Category Breakdown")
    fig3 = px.bar(cat_df.sort_values('Amount'), x='Amount', y='Category',
                  orientation='h', color='Amount',
                  color_continuous_scale=['#bfdbfe', '#3b82f6', '#1d4ed8'],
                  text='Amount')
    fig3.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
    fig3.update_layout(height=350, margin=dict(l=0,r=60,t=10,b=0),
                       showlegend=False, plot_bgcolor='white', coloraxis_showscale=False)
    st.plotly_chart(fig3, use_container_width=True)

    # pdf export
    st.divider()
    _, c2, _ = st.columns(3)
    with c2:
        pdf = generate_pdf_report(s, cat_df, mon_df, anom_df, tips)
        st.download_button(
            "📄 Download PDF Report",
            data=pdf,
            file_name=f"banksense_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
