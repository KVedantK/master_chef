import requests
from bs4 import BeautifulSoup
import json
import time
import os
from urllib.parse import urlparse
import re

def clean_text(text):
    return re.sub(r'[\W_]+', '_', text).lower()

def extract_intererst_text(soup, url):
    if "wikipedia.org" in url or "wikibooks.org" in url:
        container = soup.find(id="bodyContent") or soup.find(id="mw-content-text")
    elif "wordpress.com" in url:
        container = soup.find('article') or soup.find(class_="entry-content") or soup.find('main')
    else:
        container = soup.find('main') or soup.body

    if not container: return ""

    for junk in container.select("script, style, footer, nav, .mw-editsection, .sharedaddy"):
        junk.extract()

    blocks = [t.get_text().strip() for t in container.find_all(['h1', 'h2', 'h3', 'p', 'li'])]
    return "\n\n".join([b for b in blocks if len(b) > 5])

def scrape_data_to_json():
    output_dir = "corpus_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open('master_urls.json', 'r', encoding='utf-8') as f:
        urls_to_scrape = json.load(f)

    headers = {"User-Agent": "tester"}

    print(f"Scraping {len(urls_to_scrape)} pages local file")

    for item in urls_to_scrape:
        url = item['url']
        title = item.get('cuisine_name') or item.get('name') or item.get('title')
        filename = f"{clean_text(title)}.json"
        filepath = os.path.join(output_dir, filename)


        parsed_url = urlparse(url)
        domain = parsed_url.netloc

        print(f"Processing: {title}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            content = extract_intererst_text(soup, url)

            if content:
                page_data = {
                    "cuisine_name": title,
                    "url": url,
                    "content": content,
                    "metadata": {
                        "source": domain,
                        "category": "East Asian",
                        "filename": filename
                    }
                }

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(page_data, f, indent=4, ensure_ascii=False)
            
            time.sleep(1)

        except Exception as e:
            print(f"{title}: {e}")

    print(f"\nAll files saved in /{output_dir}")


