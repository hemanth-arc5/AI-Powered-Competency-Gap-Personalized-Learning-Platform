import streamlit as st
DEFAULT_PROFILE = {"name":"","email":"","level":"Beginner","field":"Computer Science"}
def init_state():
    defaults = {"profile":DEFAULT_PROFILE.copy(),"goal":"","custom_goal":"","assessment_answers":{},"scores":{},"gaps":[],"learning_plan":[],"quiz_score":None,"quiz_feedback":""}
    for key,value in defaults.items():
        if key not in st.session_state: st.session_state[key] = value
def reset_demo():
    """Clear learning data but keep the user logged in."""
    keep = {k: st.session_state[k] for k in ("user",) if k in st.session_state}
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.session_state.update(keep)
    init_state()
    if "user" in st.session_state:
        st.session_state.profile["name"] = st.session_state.user["name"]
        st.session_state.profile["email"] = st.session_state.user["email"]
    st.session_state.goto = "Home"
def logout():
    for key in list(st.session_state.keys()): del st.session_state[key]
