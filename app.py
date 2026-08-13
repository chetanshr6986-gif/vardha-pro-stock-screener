import streamlit as st
import runpy

st.set_page_config(
    page_title="Vardha Pro Stock Screener",
    layout="wide"
)

runpy.run_path("vardha_pro_screener_v3_3.py")
