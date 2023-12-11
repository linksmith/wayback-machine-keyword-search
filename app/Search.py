import streamlit as st
import pandas as pd
from meilisearch import Client
from streamlit_searchbox import st_searchbox
from typing import Any, List
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
from pages.backend.functions import search, create_table

def main():
    st.set_page_config(page_title="Search - Wayback Machine Keyword Search", page_icon=":mag:", layout="centered")
    st.markdown("""<style>.st-emotion-cache-1y4p8pa {  padding: 2rem 1rem 10rem; } p { margin: 0; } h1 { color: rgb(255 120 165) } h5 a { margin: 0.1rem 0; color: rgb(228, 19, 89) !important; text-decoration: none } hr { margin: 1em 0px; } .st-emotion-cache-5rimss a { color: rgb(96, 108, 139) } .stMarkdown { color: rgb(96, 108, 139) } .stMarkdown strong { color: black; }""", unsafe_allow_html=True)

    create_table()

    st.markdown('''# Search''')   

    # Search box
    query = st.text_input("Enter your search query", on_change=lambda: st.session_state.pop('page', None))
    
    col1, col2 = st.columns([0.2, 0.8])

    with col1:
        use_date_filter = st.checkbox('Date filter')

    with col2:
        use_domain_filter = st.checkbox('Domain filter')

    if use_date_filter:
        today = datetime.today()
        min_date, max_date = st.slider(
            "Select a date range",
            value=(datetime(1990, 1, 1), datetime(today.year, today.month, today.day)),
            format="YYYY-MM-DD"
        )

    if use_domain_filter:
        domain_filter = st.multiselect(
            'Select domains',
            [
                "clubofbudapest.org.au",
                "clubofbudapest.fw.hu",
                "clubofbudapest.de",
                "iwc.org.hu",
                "clubofbudapest.hu",
                "budapestklub.matav.hu",
                "clubofbudapest.cz",
                "clubofbudapest.ca",
                "club-of-budapest.de",
                "cobusa.org",
                "clubdebudapest.org",
                "worldshiftnetwork.org",
                "globalspirit.org",
                "club-of-budapest.org",
                "budapestklub.hu",
                "club-de-budapest.asso.fr",
                "club-of-budapest.com",
                "club-of-budapest.it",
                "clubofbudapest.com",
                "clubofbudapest.org"
            ]
        )

    if 'offset' not in st.session_state:
        st.session_state.offset = 0

    if query:
            
        # Conduct search with filters
        search_params = {
            # 'filter': f'timestamp >= {min_date_timestamp} AND timestamp < {max_date_timestamp}',
            'attributesToHighlight': ['text'],
            'highlightPreTag': "**[",
            'highlightPostTag': "]**",
            'limit': 10,
            'offset': st.session_state.offset,
        }
        
        if use_domain_filter and len(domain_filter) > 0:
            # convert list to string in the format of "domain IN ['clubofbudapest.org.au', 'clubofbudapest.fw.hu']"
            domain_filter_str = str(domain_filter)
            
            search_params['filter'] = f'domain IN ' + domain_filter_str
        
        if use_date_filter:
            # Format min_date to UNIX timestamp
            min_date_timestamp = int(min_date.timestamp())
            max_date_timestamp = int(max_date.timestamp())

            date_filter_str = f'unix_timestamp >= {min_date_timestamp} AND unix_timestamp < {max_date_timestamp}'

            if 'filter' in search_params:
                search_params['filter'] += f' AND ' + date_filter_str
            else:
                search_params['filter'] = date_filter_str
            
        results = search(query, search_params)

        st.markdown(f"### Found {results['estimatedTotalHits']} results for '{query}'")
        st.markdown(f'Page {st.session_state.offset + 1} of {int(results["estimatedTotalHits"] / 10) + 1}')

        st.markdown('---')

        # Display results
        for result in results['hits']:
            st.markdown(f"{result['domain']}")
            st.markdown(f"##### [{result['title']}]({result['wayback_machine_url']})")
            
            # human readable timestamp with only date
            timestamp = datetime.fromtimestamp(result['unix_timestamp']).strftime('%Y-%m-%d')
        
            # Get the highlighted text
            highlighted_text = result['_formatted']['text']

            # # Replace <em> and </em> with their HTML entity equivalents
            # highlighted_text = highlighted_text.replace('<em>', '**').replace('</em>', '**')

            # # Find the position of the highlighted text
            start_pos = highlighted_text.find('**[')
            end_pos = highlighted_text.find(']**')

            # Get a snippet of 100 chars surrounding the highlighted text
            snippet_start = max(0, start_pos - 150)
            snippet_end = min(len(highlighted_text), end_pos + 150)
            snippet = highlighted_text[snippet_start:snippet_end]

            st.markdown(f"*{timestamp}* - {snippet}")

            st.markdown('---')

        col1, col2, col3, col4 = st.columns([30, 20, 20, 30])

        with col2:
            if st.button("Previous page", disabled=st.session_state.offset == 0):
                if st.session_state.offset > 0:
                    st.session_state.offset -= 1

        with col3:
            if st.button("Next page"):
                st.session_state.offset += 1

if __name__ == "__main__":
    main()
