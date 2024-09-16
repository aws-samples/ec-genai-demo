import logging
import streamlit as st
from st_pages import get_nav_from_toml

# ログの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

nav = get_nav_from_toml(".streamlit/pages_sections.toml")
pg = st.navigation(nav)
pg.run()
