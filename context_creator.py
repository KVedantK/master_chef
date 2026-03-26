import os
from data_generator import collect_all_data
from scraper import scrape_data_to_json
from data_ingestion_v2 import data_loading
from pathlib import Path

DB_PATH = Path("./corpus_data")

def run_pipeline():
    print("--- Phase 1: Collecting Sources ---")
    collect_all_data()
    
    print("--- Phase 2: Scraping Data ---")
    scrape_data_to_json()
    
    print("--- Phase 3: Ingesting into Chroma ---")
    data_loading(str(DB_PATH))


run_pipeline()
