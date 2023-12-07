import streamlit as st
from pages.backend.functions import get_domains, delete_domain, get_domain_names_list

def main():
    st.set_page_config(page_title="Delete Domains - Wayback Machine Keyword Search", page_icon=":mag:", layout="centered")
    st.markdown("""<style>p { margin: 0; } h1 { color: rgb(255 120 165) } h5 a { margin: 0.1rem 0; color: rgb(228, 19, 89) !important; text-decoration: none } hr { margin: 1em 0px; } .st-emotion-cache-5rimss a { color: rgb(96, 108, 139) } .stMarkdown { color: rgb(96, 108, 139) } .stMarkdown strong { color: black; }""", unsafe_allow_html=True)
    
    st.markdown('''# Delete domains''')

    domain_names = get_domains()
    domain_names_list = get_domain_names_list(domain_names)

    domain_names_multiselect = st.multiselect(
        'Select domains to delete',
        domain_names_list
    )

    delete_domain_button =  st.button('Delete domains from collection')

    if delete_domain_button:
        if domain_names_multiselect is not None:

            for domain_name in domain_names_multiselect:
                delete_domain(domain_name)    
            
            st.success('Domains deleted from collection.')
    
    st.markdown("""<style>p { margin: 0; } h1 { color: rgb(255 120 165) } h5 a { margin: 0.1rem 0; color: rgb(228, 19, 89) !important; text-decoration: none } hr { margin: 1em 0px; } .st-emotion-cache-5rimss a { color: rgb(96, 108, 139) } .stMarkdown { color: rgb(96, 108, 139) } .stMarkdown strong { color: black; }""", unsafe_allow_html=True)
   
if __name__ == "__main__":
    main()
