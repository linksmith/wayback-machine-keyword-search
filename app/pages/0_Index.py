import streamlit as st
from sqlalchemy import text
from datetime import datetime
import numpy as np
from pages.backend.functions import get_domains, create_domains_dataframe, rebuild_index, get_domain_names_list
import pandas as pd

def main():
    st.set_page_config(page_title="Domains - Wayback Machine Keyword Search", page_icon=":mag:", layout="centered")
    st.markdown("""<style>p { margin: 0; } h1 { color: rgb(255 120 165) } h5 a { margin: 0.1rem 0; color: rgb(228, 19, 89) !important; text-decoration: none } hr { margin: 1em 0px; } .st-emotion-cache-5rimss a { color: rgb(96, 108, 139) } .stMarkdown { color: rgb(96, 108, 139) } .stMarkdown strong { color: black; }""", unsafe_allow_html=True)
    
    st.markdown('''# Domains''')

    domain_names = get_domains()
    domain_names_data = create_domains_dataframe(domain_names)
    domain_names_df = st.dataframe(
        domain_names_data,
        column_config={
            "name": "Domains",
            "id": None,
            "domain_name": st.column_config.TextColumn(
                "Domain", width=300
            ),
            "start_date": st.column_config.DateColumn(
                "From", width=100
            ),
            "end_date": st.column_config.DateColumn(
                "To", width=100
            ),
            "created": None,
            "updated": None
        },
        hide_index=True
    )
    
    run_index_btn = st.button(
        'Rebuild index', 
        type="primary", 
    )
    st.text("Keep in mind that rebuilding the index will take up to a few hours.")

    if run_index_btn:

        progress_text = "Rebuldling index. Please wait..."
        rebuilding_index_progress = st.progress(0, text=progress_text)

        rebuild_index(rebuilding_index_progress)

        rebuilding_index_progress.empty()

        st.toast("Index rebuilt successfully.", icon='🎉')

if __name__ == "__main__":
    main()
