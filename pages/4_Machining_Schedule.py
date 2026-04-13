# machining changes to weld page:
# site is done on operation i think? more complex logic
# different operations - might need their own charts or their own categories or something
import streamlit as st
st.title("WORK IN PROGRESS")

import streamlit as st
from data import *
from ui_components import *

st.set_page_config(layout="wide")

from login import require_auth
require_auth()

load_css('stylesheet.css')

tcol1, tcol2 = st.columns([1, 4])
tcol2.title("Machining Schedule")
render_logo(tcol1)