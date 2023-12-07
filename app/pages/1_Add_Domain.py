import streamlit as st
from datetime import datetime
from pages.backend.functions import get_domains, add_domain, get_domain_names_list

def main():
    st.set_page_config(page_title="Add Domain - Wayback Machine Keyword Search", page_icon=":mag:", layout="centered")
    st.markdown("""<style>p { margin: 0; } h1 { color: rgb(255 120 165) } h5 a { margin: 0.1rem 0; color: rgb(228, 19, 89) !important; text-decoration: none } hr { margin: 1em 0px; } .st-emotion-cache-5rimss a { color: rgb(96, 108, 139) } .stMarkdown { color: rgb(96, 108, 139) } .stMarkdown strong { color: black; }""", unsafe_allow_html=True)
       
    st.markdown('''# Add domain''')

    domain_name_input = st.text_input("Enter domain name")
    use_date_filter = st.checkbox('Constrain collection period')

    today = datetime.today()

    if use_date_filter:
        min_date, max_date = st.slider(
            "Select a date range",
            value=(datetime(1990, 1, 1), datetime(today.year, today.month, today.day)),
            format="YYYY-MM-DD"
        )

    success = False

    if st.button('Add domain to collection'):
        if domain_name_input is None or domain_name_input == '':
            st.error('Domain name is required.')
            return
        
        if domain_name_input.startswith('http://') or domain_name_input.startswith('https://'):
            st.error('Domain name should not start with http:// or https://.')
            return

        if domain_name_input.endswith('/'):
            st.error('Domain name should not end with /.')
            return

        if domain_name_input.startswith('www.'):
            st.error('Domain name should not start with www.')
            return
        
        # check if domain already exists in collection
        domain_names = get_domains()
        domain_names_list = get_domain_names_list(domain_names)
        if domain_name_input in domain_names_list:
            st.error('Domain already exists in collection.')
            return
        
        # check domain name has correct domain format (e.g. example.com)
        if domain_name_input.count('.') < 1:
            st.error('Domain name should have at least one dot.')
            return

        # check if domain name has not illegal characters
        illegal_characters = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '+', '=', '{', '}', '[', ']', '|', '\\', ':', ';', '"', '\'', '<', '>', ',', '?']
        for illegal_character in illegal_characters:
            if illegal_character in domain_name_input:
                st.error('Domain name should not contain illegal characters.')
                return
        
        # convert domain name to lowercase
        domain_name_input = domain_name_input.lower()

        min_date_timestamp = None
        max_date_timestamp = None
        if use_date_filter:
            min_date_timestamp = int(min_date.timestamp())
            max_date_timestamp = int(max_date.timestamp())
        created_unix = int(today.timestamp())
        updated_unix = int(today.timestamp())

        success = add_domain(domain_name_input, min_date_timestamp, max_date_timestamp, created_unix, updated_unix)

        if success:
            st.success('Domain added to collection.')
        else:
            st.error('Something went wrong. Domain not added to collection.')
 
if __name__ == "__main__":
    main()
