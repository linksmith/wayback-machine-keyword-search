import streamlit as st
import pandas as pd
from meilisearch import Client
from streamlit_searchbox import st_searchbox
from typing import Any, List
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

st.title('Wayback Machine Keyword Search')

# def init_meilisearch_index():
#     client = Client('http://127.0.0.1:7700', 'masterKey')

#     # An index is where the documents are stored.
#     index = client.index('movies')

#     documents = [
#         { 'id': 1, 'title': 'Carol', 'genres': ['Romance', 'Drama'] },
#         { 'id': 2, 'title': 'Wonder Woman', 'genres': ['Action', 'Adventure'] },
#         { 'id': 3, 'title': 'Life of Pi', 'genres': ['Adventure', 'Drama'] },
#         { 'id': 4, 'title': 'Mad Max: Fury Road', 'genres': ['Adventure', 'Science Fiction'] },
#         { 'id': 5, 'title': 'Moana', 'genres': ['Fantasy', 'Action']},
#         { 'id': 6, 'title': 'Philadelphia', 'genres': ['Drama'] },
#     ]

#     # If the index 'movies' does not exist, Meilisearch creates it when you first add the documents.
#     index.add_documents(documents) # => { "uid": 0 }

#     return index

# # function with list of labels
# def search_movies(searchterm: str) -> List[any]:
#     result = []

#     if searchterm:
#         result = index.search(searchterm)
#         print(result)

#     return [item['title'] for item in result['hits']]
#     # AttributeError: 'list' object has no attribute 'title' fix

# index = init_meilisearch_index()

# Step 1: Load the JSON Lines file into a Pandas DataFrame
def load_jsonl_to_dataframe(file_path):
    # check if file_path exists?
    path = Path(file_path)
    if not path.is_file():
        print("File path {} does not exist. Exiting...".format(file_path))
        return None
    else:
        return pd.read_json(path, lines=True)

def convert_html_to_text(df, html_column):
    df[html_column] = df[html_column].apply(lambda x: BeautifulSoup(x, 'html.parser').get_text())
    return df

# Step 2: Initialize Meilisearch Client
def initialize_meilisearch(host, api_key=None):
    return Client(host, api_key)

# Step 3: Create or get an index in Meilisearch
def create_or_get_index(client, index_name, primary_key=None):
    # Try to get the index if it already exists
    try:
        return client.index(index_name)
    except Exception:
        # If not, create a new one
        return client.create_index(uid=index_name, primary_key=primary_key)

# Step 4: Add documents to the index
def add_documents_to_index(index, documents, primary_key, batch_size=50):
    progress_bar = st.progress(0)
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        index.add_documents()
        response = index.add_documents(batch, primary_key)
        print(response)
        progress = (i + len(batch)) / len(documents)
        progress_bar.progress(progress)
    progress_bar.progress(1.0)
    print("All documents added to index.")

# Step 5: Search function with list of labels
def search_websites(searchterm: str) -> List[any]:
    result = []

    if searchterm:
        result = index.search(searchterm)
        print(result)

    return [item['title'] for item in result['hits']]

def check_documents(documents):
    # Check if documents is a list
    if not isinstance(documents, list):
        print("Error: documents is not a list.")
        return False

    # Check if documents is not empty
    if not documents:
        print("Error: documents list is empty.")
        return False

    # Check if each item in documents is a dictionary
    for doc in documents:
        if not isinstance(doc, dict):
            print("Error: document is not a dictionary.")
            return False

    # Check if each dictionary in documents is not empty
    for doc in documents:
        if not doc:
            print("Error: document dictionary is empty.")
            return False

    print("All checks passed.")
    return True
    
def delete_all_indexes(client):
    indexes = client.get_raw_indexes()
    print(indexes)

    for index_result in indexes['results']:
        client.delete_index(index_result['uid'])
        print("deleted", index_result['uid'])
    print("All indexes deleted.")

# Main process
def main(jsonl_file_path, meilisearch_host, index_name, primary_ke=None, meilisearch_api_key=None):
    df = load_jsonl_to_dataframe(jsonl_file_path)
    if df is None:
        return
    else:
        print(df.head(), df.shape)

    df['id'] = range(len(df))
    # df = df.head(100)
    df = convert_html_to_text(df, 'html')
    documents = df.to_dict(orient='records')
    check_documents(documents)

    client = initialize_meilisearch(meilisearch_host, meilisearch_api_key)
    index = create_or_get_index(client, index_name, primary_key)
    add_documents_to_index(index, documents, primary_key, 50)

jsonl_file_path = 'data/external/dataset_expired-article-hunter_2023-11-27_15-03-44-819.jsonl'
meilisearch_host = 'http://127.0.0.1:7700'  # Replace with your Meilisearch host
index_name = 'club-of-budapest-4' 
meilisearch_api_key = 'masterKey'
primary_key = None


# Initialize MeiliSearch Client
client = Client(meilisearch_host,meilisearch_api_key)  # Replace with your MeiliSearch URL and API key
index = client.index(index_name)  # Replace with your index name
index.update_filterable_attributes([
  'timestamp'
])
# Search box
query = st.text_input("Enter your search query")

# if st.button('Run index'):
#     main(jsonl_file_path, meilisearch_host, index_name, primary_key, meilisearch_api_key)

# if st.button('Delete all indexes'):
#     client = initialize_meilisearch(meilisearch_host, meilisearch_api_key)
#     delete_all_indexes(client)

# Slider for filtering (assuming the field is named 'price')
today = datetime.today()

min_date, max_date = st.slider(
    "Select a date range",
    value=(datetime(1990, 1, 1), datetime(today.year, today.month, today.day)),
    format="YYYY-MM-DD"
)

if query:
    # Format dates for filtering
    min_date_str = min_date.strftime('%Y%m%d%H%M%S')
    max_date_str = max_date.strftime('%Y%m%d%H%M%S')

    # Conduct search with filters
    search_params = {
        'filter': f'timestamp >= {min_date_str} AND timestamp <= {max_date_str}',
        'attributesToHighlight': ['text'],
    }
    results = index.search(query, search_params)
    
    # add subtitle for search results
    st.markdown(f"### Found {results['estimatedTotalHits']} results for '{query}'")

    # Display results
    for result in results['hits']:
        if 'title' in result:
            st.markdown(f"### {result['title']}")
        
        st.markdown(f"[{result['wayback_machine_url']}]({result['wayback_machine_url']})")
        # st.markdown(f"**Timestamp:** {result['timestamp']}")
        # result['timestamp'] is an int and has format  %Y%m%d%H%M%S 
        # formet this value to human readable
        timestamp = datetime.strptime(str(result['timestamp']), '%Y%m%d%H%M%S')
        st.markdown(f"**Snapshot:** {timestamp}")
        
        # Get the highlighted text
        highlighted_text = result['_formatted']['text']

        # Replace <em> and </em> with their HTML entity equivalents
        highlighted_text = highlighted_text.replace('<em>', '**[').replace('</em>', ']**')

        # Find the position of the highlighted text
        start_pos = highlighted_text.find('**[')
        end_pos = highlighted_text.find(']**')

        # Get a snippet of 100 chars surrounding the highlighted text
        snippet_start = max(0, start_pos - 100)
        snippet_end = min(len(highlighted_text), end_pos + 100)
        snippet = highlighted_text[snippet_start:snippet_end]

        st.markdown(f"**Text:** {snippet}")

        
        
