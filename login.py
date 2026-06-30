import streamlit as st
from ui_components import render_logo


def require_auth():
    if not st.user.is_logged_in:
        st.warning("🔒 Please log in first.")
        st.switch_page("login.py")
        st.stop()


tcol1, tcol2 = st.columns([1, 4])
tcol2.title("Data Visualiser - Login")
render_logo(tcol1)

if st.user.is_logged_in:
    st.success("Login Successful")
    st.write("Use Sidebar to navigate app")
else:
    st.login("microsoft")