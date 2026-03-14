import requests
from bs4 import BeautifulSoup
import json
import time
import os
import re

def slugify(text):
    """Converts page titles to clean filenames (e.g., 'BBQ Pork' -> 'bbq_pork')"""
    return re.sub(r'[\W_]+', '_', text).lower()

def extract_meaningful_text(soup, url):
    """Targets main content and ignores footers/nav."""
    if "wikipedia.org" in url or "wikibooks.org" in url:
        container = soup.find(id="bodyContent") or soup.find(id="mw-content-text")
    elif "wordpress.com" in url:
        container = soup.find('article') or soup.find(class_="entry-content") or soup.find('main')
    else:
        container = soup.find('main') or soup.body

    if not container: return ""

    # Remove the 'fat' (Edit links, nav, footers)
    for junk in container.select("script, style, footer, nav, .mw-editsection, .sharedaddy"):
        junk.extract()

    # Keep headers, paragraphs, and lists (the recipes/facts)
    blocks = [t.get_text().strip() for t in container.find_all(['h1', 'h2', 'h3', 'p', 'li'])]
    return "\n\n".join([b for b in blocks if len(b) > 5])

def scrape_to_individual_jsons():
    # 1. Setup output directory
    output_dir = "corpus_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open('master_urls.json', 'r', encoding='utf-8') as f:
        urls_to_scrape = json.load(f)

    headers = {"User-Agent": "AI-Coursework-Bot/1.0"}

    print(f"🚀 Scraping {len(urls_to_scrape)} pages into individual JSON files...")

    for item in urls_to_scrape:
        url = item['url']
        title = item.get('cuisine_name') or item.get('name') or item.get('title')
        filename = f"{slugify(title)}.json"
        filepath = os.path.join(output_dir, filename)

        print(f"📄 Processing: {title}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            content = extract_meaningful_text(soup, url)

            if content:
                # 2. Structure the data for this specific page
                page_data = {
                    "cuisine_name": title,
                    "url": url,
                    "content": content,
                    "metadata": {
                        "source": "Wikipedia" if "wikipedia" in url else "Wikibooks" if "wikibooks" in url else "Blog",
                        "category": "East Asian",
                        "filename": filename
                    }
                }

                # 3. Save as individual file
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(page_data, f, indent=4, ensure_ascii=False)
            
            time.sleep(0.5) # Fast but polite

        except Exception as e:
            print(f"❌ Failed {title}: {e}")

    print(f"\n✅ All files saved in /{output_dir}")


scrape_to_individual_jsons()