import streamlit as st
import meilisearch
from streamlit_searchbox import st_searchbox
from typing import Any, List

st.title('Wayback Machine Keyword Search')

def init_meilisearch_index():
    client = meilisearch.Client('http://127.0.0.1:7700', 'masterKey')

    # An index is where the documents are stored.
    index = client.index('movies')

    documents = [
        { 'id': 1, 'title': 'Carol', 'genres': ['Romance', 'Drama'] },
        { 'id': 2, 'title': 'Wonder Woman', 'genres': ['Action', 'Adventure'] },
        { 'id': 3, 'title': 'Life of Pi', 'genres': ['Adventure', 'Drama'] },
        { 'id': 4, 'title': 'Mad Max: Fury Road', 'genres': ['Adventure', 'Science Fiction'] },
        { 'id': 5, 'title': 'Moana', 'genres': ['Fantasy', 'Action']},
        { 'id': 6, 'title': 'Philadelphia', 'genres': ['Drama'] },
    ]

    # If the index 'movies' does not exist, Meilisearch creates it when you first add the documents.
    index.add_documents(documents) # => { "uid": 0 }

    return index

# function with list of labels
def search_movies(searchterm: str) -> List[any]:
    result = []

    if searchterm:
        result = index.search(searchterm)
        print(result)

    return [item['title'] for item in result['hits']]
    # AttributeError: 'list' object has no attribute 'title' fix



index = init_meilisearch_index()

# pass search function to searchbox
selected_value = st_searchbox(
    search_function=search_movies,
    key="movies_searchbox",
)
