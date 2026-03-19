import streamlit as st
import streamlit_authenticator as stauth
from ui_components import *

def to_dict(obj):
    if hasattr(obj, 'items'):
        return {k: to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_dict(i) for i in obj]
    else:
        return obj
    
def require_auth():
    if not st.session_state.get("authentication_status"):
        st.warning("🔒 Please log in first.")
        st.switch_page("login.py")
        st.stop()
    authenticator = get_authenticator()
    if authenticator:
        authenticator.logout(location="sidebar")

def get_authenticator():
    """Get authenticator from session or recreate it."""
    if "authenticator" not in st.session_state:
        authenticator = stauth.Authenticate(
            to_dict(st.secrets["credentials"]),
            st.secrets["cookie"]["name"],
            st.secrets["cookie"]["key"],
            st.secrets["cookie"]["expiry_days"],
        )
        st.session_state["authenticator"] = authenticator
    return st.session_state["authenticator"]

authenticator = get_authenticator()

st.session_state["authenticator"] = authenticator

tcol1, tcol2 = st.columns([1,4])
tcol2.title("Data Visualiser - Login")
render_logo(tcol1)

authenticator.login()

if st.session_state.get("authentication_status"):
    st.success("Login Successful")
    st.write("Use Sidebar to navigate app")
    authenticator.logout(location="sidebar")
elif st.session_state.get("authentication_status") is False:
    st.error("Incorrect username or password")
else:
    st.warning("please enter your username and password")