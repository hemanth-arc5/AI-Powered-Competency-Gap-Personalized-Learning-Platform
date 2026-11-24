
import html
import streamlit as st
def apply_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
    html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
    .stApp{background:#f5f8fc;color:#16243a}
    [data-testid="stSidebar"]{background:#10243b}
    [data-testid="stSidebar"] *{color:#edf6ff!important}
    h1,h2,h3{font-family:'Manrope',sans-serif;color:#14263d}
    .hero-sub{color:#62738a;font-size:1.02rem;margin-top:-8px}
    .metric-card,.step-card{background:white;border:1px solid #e5ebf2;border-radius:16px;padding:18px;box-shadow:0 5px 18px #14263d0a}
    .metric-card{min-height:108px}.metric-label{color:#74849a;font-size:.82rem;font-weight:600}
    .metric-value{font-size:1.55rem;font-weight:800;color:#132b45;margin:6px 0}
    .metric-help,.step-card p{color:#8290a2;font-size:.8rem}
    .step-card{min-height:150px}.step-number{background:#e4f6f5;color:#087e80;border-radius:9px;padding:6px 10px;display:inline-block;margin-bottom:12px;font-weight:800}
    .stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"]{background:#087e80;border:0;border-radius:10px;color:white;font-weight:700}
    div[data-testid="stExpander"]{background:white;border-radius:12px;border:1px solid #e5ebf2}
    </style>""", unsafe_allow_html=True)
def page_header(title, subtitle):
    st.title(title)
    st.markdown(f'<p class="hero-sub">{subtitle}</p>',unsafe_allow_html=True)
    st.write("")
def metric_card(label,value,help_text):
    label,value,help_text = (html.escape(str(x)) for x in (label,value,help_text))
    st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-help">{help_text}</div></div>',unsafe_allow_html=True)
