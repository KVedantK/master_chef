# context_creator.py
import os
from data_generator import collect_all_sources
from scraper import scrape_to_individual_jsons
from data_ingestion_v2 import data_loading

def run_pipeline():
    print("--- Phase 1: Collecting Sources ---")
    #collect_all_sources()
    
    print("--- Phase 2: Scraping Data ---")
    #scrape_to_individual_jsons()
    
    print("--- Phase 3: Ingesting into Chroma ---")
    # This is the function we fixed that creates the 3030 chunks
    data_loading("./corpus_data")


run_pipeline()