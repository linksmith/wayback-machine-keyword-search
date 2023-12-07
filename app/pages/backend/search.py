import pandas as pd
from bs4 import BeautifulSoup
from meilisearch import Client
from tqdm import tqdm
import urllib.request
import json
import concurrent.futures
from urllib.error import HTTPError
import os
import pdfplumber
from pydantic import BaseModel
from typing import Dict, List, Optional, Any, Tuple
import json
from io import BytesIO
import streamlit as st

class IndexConfig(BaseModel):
    host: str
    api_key: str
    index_name: str
    proxy_http: str
    proxy_https: str

class BaseContent(BaseModel):
    text: str
    title: Optional[str]

class Page(BaseModel):
    timestamp: str
    original: str
    mimetype: str
    statuscode: str
    digest: str
    length: str

class DomainPages(BaseModel):
    domain: str
    pages: List[Page]

class PageContent(BaseModel):
    id: Optional[int]
    title: str
    domain: str
    timestamp: str
    unix_timestamp: Optional[int]
    wayback_machine_url: str
    url: str
    text: str
    mimetype: str

class DomainPagesContent(BaseModel):
    domain: str
    pages_contents: List[PageContent]

df = None
all_domains_pages_df = None

def fetch_pages(domain: str, proxy) -> Tuple[str, Optional[bytes]]:
    url = f'https://web.archive.org/cdx/search/cdx?url={domain}&output=json&collapse=digest&matchType=domain&fl=timestamp,original,mimetype,statuscode,digest,length&filter=statuscode:200&filter=mimetype:text/html|application/pdf'
    response = proxy.open(url)
    return domain, response

def convert_json_to_page(json_data: List[List[str]]) -> List[Page]:
    pages = []
    for page in json_data[1:]:
        page = Page(
            timestamp=page[0],
            original=page[1],
            mimetype=page[2],
            statuscode=page[3],
            digest=page[4],
            length=page[5]
        )
        pages.append(page)
    return pages

def fetch_all_domain_pages(domain_names: List, proxy) -> List[DomainPages]:
    all_domain_pages = [] 

    print(f"Total domains to be fetched: {len(domain_names)}...")
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []

        for domain in domain_names:
            future = executor.submit(fetch_pages, domain, proxy)
            futures.append(future)
            
        for future in concurrent.futures.as_completed(futures):
            domain, response = future.result()
            
            if response is None:
                continue

            response_json = json.load(response)
            pages = convert_json_to_page(response_json)
            domain_pages = DomainPages(domain=domain, pages=pages)

            all_domain_pages.append(domain_pages)

    # reorder all_domain_pages by pages length from smallest to largest
    all_domain_pages = sorted(all_domain_pages, key=lambda x: len(x.pages))

    print(f"Total fetched domains: {len(all_domain_pages)}.")
    print(f"Total pages fetched: {sum([len(domain_pages.pages) for domain_pages in all_domain_pages])}.")

    return all_domain_pages

def read_pdf_content(pdf_path: str) -> Optional[BaseContent]:
    pdf_content = ''
    pdf_title = ''
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pdf_title = pdf.metadata['title']
            for page in pdf.pages:
                pdf_content += page.extract_text() + ' '
    except:
        return None

    return BaseContent(text=pdf_content, title=pdf_title)

def fetch_pdf_content(original_content: bytes, pdf_url: str) -> Optional[BaseContent]:
    download_folder = 'downloads'  # Assuming the download folder exists
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    filename = os.path.join(download_folder, pdf_url.split('/')[-1])

    if not os.path.exists(filename):
        with open(filename, 'wb') as f:
            f.write(original_content)

    return read_pdf_content(filename)

def fetch_pdf_content_on_the_fly(content, url):
    pdf_content = ''
    pdf_title = ''

    try:
        with pdfplumber.open(BytesIO(content)) as pdf:
            pdf_content = ' '.join(page.extract_text() for page in pdf.pages)
            if pdf.metadata is not None and 'title' in pdf.metadata:
                pdf_title = pdf.metadata['title']

        if pdf_title == '':
            pdf_title = url.split('/')[-1]
    except:
        return None

    return BaseContent(text=pdf_content, title=pdf_title)

def fetch_html_content(original_content: bytes) -> Optional[BaseContent]:
    soup = BeautifulSoup(original_content, 'html.parser')
    text = soup.get_text()
    text = text.replace('\n', ' ').replace(' +', ' ')
    title = soup.title.string if soup.title else ''

    return BaseContent(text=text, title=title)

def fetch_content(wayback_machine_url: str, proxy) -> Optional[bytes]:
    try:
        response = proxy.open(wayback_machine_url)
        if response.status == 200:
            return response.read()
    except:
        return None
    return None
   
def process_page(page: Page, domain: str, proxy) -> Optional[PageContent]:
    wayback_machine_url = f'https://web.archive.org/web/{page.timestamp}/{page.original}'
    wayback_machine_content_url = f'https://web.archive.org/web/{page.timestamp}if_/{page.original}'

    if page.mimetype == 'application/pdf':
        original_content = fetch_content(
            wayback_machine_url=wayback_machine_content_url,
            proxy=proxy
        )   
        
        if original_content is None:
            return None
        content = fetch_pdf_content_on_the_fly(original_content, page.original)
    elif page.mimetype == 'text/html':
        original_content = fetch_content(wayback_machine_content_url, proxy)     
        if original_content is None:       
            return None

        content = fetch_html_content(original_content)
    else:
        return None

    if content is None:
        return None
        
    if content.text is None or len(content.text) < 500:
        return None

    unix_timestamp = int(pd.to_datetime(page.timestamp).timestamp())

    return PageContent(
        title=content.title,
        domain=domain,
        timestamp=page.timestamp,
        unix_timestamp=unix_timestamp,
        wayback_machine_url=wayback_machine_url,
        url=page.original,
        text=content.text,
        mimetype=page.mimetype
    )

def fetch_domain_pages_content(all_domain_pages: List[DomainPages], proxy, rebuilding_index_progress, use_threads: bool = False) -> List[DomainPagesContent]:
    domain_pages_content_list = []

    if use_threads:
        for domain_pages in all_domain_pages:
            domain_pages_content = DomainPagesContent(domain=domain_pages.domain, pages_contents=[])

            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = []

                for page in domain_pages.pages:
                    future = executor.submit(process_page, page, domain_pages.domain, proxy)
                    futures.append(future)

                total_domain_futures = len(futures)
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    result = future.result()
                    if result is not None:
                        domain_pages_content.pages_contents.append(result)
                    rebuilding_index_progress.progress((i + 1) / total_domain_futures, text=f"Fetching content for domain '{domain_pages.domain}'...")
  
                domain_pages_content_list.append(domain_pages_content)
    else:

        for domain_pages in all_domain_pages:
            domain_pages_content = DomainPagesContent(domain=domain_pages.domain, pages_contents=[])

            total_domain_pages = len(domain_pages.pages)
            for i, page in enumerate(domain_pages.pages):
                result = process_page(page, domain_pages.domain)
                if result is not None:
                    domain_pages_content.pages_contents.append(result)
                rebuilding_index_progress.progress((i + 1) / total_domain_pages, text=f"Fetching content for domain '{domain_pages.domain}'...")

            domain_pages_content_list.append(domain_pages_content)

    return domain_pages_content_list

def create_index(all_domain_pages_content: List[DomainPagesContent], config: IndexConfig) -> None:  
    client = Client(config.host, config.api_key)
    client.create_index(config.index_name, {'primaryKey': 'id'})

    index = client.index(config.index_name)
    index.update_filterable_attributes([
        'unix_timestamp',
        'domain',
    ])

    all_pages_content = []
    total_pages = 0

    for domain_pages_content in all_domain_pages_content:
        print(f"Adding {len(domain_pages_content.pages_contents)} pages from domain '{domain_pages_content.domain}' to Meilisearch index...")
        total_pages += len(domain_pages_content.pages_contents)
        all_pages_content.extend(domain_pages_content.pages_contents)

    # update all_pages_content and set id as index starting with 1
    for i, page_content in enumerate(all_pages_content):
        page_content.id = i + 1
                
    # convert all_pages_content to dictoionary
    all_pages_content_dict = [page_content.dict() for page_content in all_pages_content]

    # add all_pages_content_dict to Meilisearch index
    index.add_documents(all_pages_content_dict)

    print(f"Total pages added to Meilisearch index: {total_pages}.")

def set_proxy(proxy_http: str, proxy_https: str) -> None:
    return urllib.request.build_opener(
        urllib.request.ProxyHandler(
            {
                'http': proxy_http,
                'https': proxy_https
                }
            )
    )

def rebuild_index(domain_names: List[str], config: IndexConfig, rebuilding_index_progress) -> None:
    proxy = set_proxy(config.proxy_http, config.proxy_https)

    all_domain_pages = fetch_all_domain_pages(
        domain_names=domain_names, 
        proxy=proxy
    )
    
    threaded_domain_pages_content_list = fetch_domain_pages_content(
        all_domain_pages=all_domain_pages,
        proxy=proxy, 
        rebuilding_index_progress=rebuilding_index_progress,
        use_threads=True
    )

    create_index(threaded_domain_pages_content_list, config)

def get_index(config: IndexConfig) -> Any:
    client = Client(
        config.host, 
        config.api_key
    )
    
    index = client.index(config.index_name)
    
    index.update_filterable_attributes([
        'unix_timestamp',
        'domain',
    ])

    return index