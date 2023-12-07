import streamlit as st
from sqlalchemy import text
from datetime import datetime
import numpy as np
import pandas as pd
from pages.backend.search import get_index, IndexConfig
from pages.backend.search import rebuild_index as rebuild_search_index

def create_domains_dataframe(domain_names):       
    return pd.DataFrame(domain_names)

def create_table():
    conn = st.connection('collection_db', type='sql')
    with conn.session as s:
        s.execute(
            text('CREATE TABLE IF NOT EXISTS collection (id SERIAL PRIMARY KEY, domain_name text, start_date int, end_date int, created int, updated int);')
        )    
        s.commit()

def get_domains():
    domain_names = []
    conn = st.connection('collection_db', type='sql')
    with conn.session as s:
        c = s.execute(text('select * from collection'))
        domain_names = c.all()

    return domain_names

# create function to add domain to collection
def add_domain(domain_name, start_date, end_date, created, updated):
    conn = st.connection('collection_db', type='sql')
    with conn.session as s:        
        s.execute(text('INSERT INTO collection (domain_name, start_date, end_date, created, updated) VALUES (:domain_name, :start_date, :end_date, :created, :updated)'), {'domain_name': domain_name, 'start_date': start_date, 'end_date': end_date, 'created': created, 'updated': updated})
        s.commit()
        return True

def get_domain_names_list(domain_names):
    domain_names_list = []

    for domain_name in domain_names:
        domain_names_list.append(domain_name[1])

    return domain_names_list

# create function to delete domain from collection
def delete_domain(domain_name):
    conn = st.connection('collection_db', type='sql')
    with conn.session as s:
        s.execute(text('DELETE FROM collection WHERE domain_name = :domain_name'), {'domain_name': domain_name})
        s.commit()
        return True

# show all domains in collection
def rebuild_index(rebuilding_index_progress):
    domain_names = get_domains()
    domain_names_list = get_domain_names_list(domain_names)

    if len(domain_names_list) == 0:
        st.error('No domains provided.')
        return

    config = IndexConfig(
        host=st.secrets.meilisearch.host, 
        api_key=st.secrets.meilisearch.api_key,
        index_name=st.secrets.meilisearch.index_name,
        proxy_http=st.secrets.proxy.http,
        proxy_https=st.secrets.proxy.https
    )

    return rebuild_search_index(
        domain_names=domain_names_list, 
        config=config, 
        rebuilding_index_progress=rebuilding_index_progress
    )

def get_index():
    config = IndexConfig(
        host=st.secrets.meilisearch.host, 
        api_key=st.secrets.meilisearch.api_key,
        index_name=st.secrets.meilisearch.index_name,
        proxy_http=st.secrets.proxy.http,
        proxy_https=st.secrets.proxy.https
    )

    return get_index(config)