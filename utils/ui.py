import html
import streamlit as st
def apply_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
    html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
    /* Colours come from .streamlit/config.toml so light & dark both stay consistent.
       Custom components below use translucent colours + inherited text, so they adapt to either theme. */
    header[data-testid="stHeader"]{background:transparent}
    .block-container{padding-top:3.5rem}
    h1,h2,h3{font-family:'Manrope',sans-serif;letter-spacing:-.01em}
    [data-testid="stSidebar"]{border-right:1px solid rgba(128,128,128,.2)}
    .hero-sub{opacity:.7;font-size:1.02rem;margin-top:-8px}
    .metric-card,.step-card{background:rgba(128,128,128,.10);border:1px solid rgba(128,128,128,.25);border-radius:16px;padding:18px;color:inherit}
    .metric-card{min-height:108px}.metric-label{opacity:.7;font-size:.82rem;font-weight:600}
    .metric-value{font-size:1.55rem;font-weight:800;color:inherit;margin:6px 0}
    .metric-help,.step-card p{opacity:.6;font-size:.8rem}
    .step-card{min-height:150px}
    .step-number{background:rgba(20,184,166,.18);color:#14b8a6;border-radius:9px;padding:6px 10px;display:inline-block;margin-bottom:12px;font-weight:800}
    .stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"]{background:#0d9488;border:0;border-radius:10px;color:#fff;font-weight:700}
    .stButton>button[kind="primary"]:hover,.stFormSubmitButton>button[kind="primary"]:hover{background:#14b8a6;color:#fff}
    .stButton>button,.stFormSubmitButton>button{border-radius:10px}
    div[data-testid="stForm"]{border:1px solid rgba(128,128,128,.3);border-radius:14px;padding:1.2rem}
    div[data-testid="stExpander"]{border-radius:12px;border:1px solid rgba(128,128,128,.25)}
    .stTabs [data-baseweb="tab"]{font-weight:600}
    </style>""", unsafe_allow_html=True)
def page_header(title, subtitle):
    st.title(title)
    st.markdown(f'<p class="hero-sub">{subtitle}</p>',unsafe_allow_html=True)
    st.write("")
def metric_card(label,value,help_text):
    label,value,help_text = (html.escape(str(x)) for x in (label,value,help_text))
    st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-help">{help_text}</div></div>',unsafe_allow_html=True)