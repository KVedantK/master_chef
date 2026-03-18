import requests
from bs4 import BeautifulSoup
import json
import time

# --- Your existing logic slightly standardized ---

def extract_east_asian_urls(main_url):
    headers = {"User-Agent": "AI-Coursework-Bot/1.0"}
    try:
        response = requests.get(main_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        heading_id = soup.find(id="East_Asian_cuisine")
        if not heading_id: return []
        parent_heading_div = heading_id.find_parent('div', class_='mw-heading')
        link_container = parent_heading_div.find_next_sibling('div', class_='div-col')
        
        found_links = []
        if link_container:
            for li in link_container.find_all('li'):
                anchor = li.find('a', href=True)
                if anchor:
                    path = anchor['href']
                    if path.startswith('/wiki/') and ':' not in path:
                        found_links.append({
                            "title": anchor.get_text().strip(),
                            "url": f"https://en.wikipedia.org{path}",
                            "source": "Wikipedia"
                        })
        return found_links
    except Exception as e:
        print(f"Wiki Error: {e}")
        return []

def get_links_from_page(url, headers):
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        links = []
        tree_items = soup.find_all('div', class_='CategoryTreeItem')
        for item in tree_items:
            a = item.find('a', href=True)
            if a: links.append({'title': a.text.strip(), 'url': f"https://en.wikibooks.org{a['href']}"})
        category_div = soup.find('div', id='mw-pages')
        if category_div:
            for a in category_div.find_all('a', href=True):
                links.append({'title': a.text.strip(), 'url': f"https://en.wikibooks.org{a['href']}"})
        return links
    except: return []

def collect_all_sources():
    all_extracted_data = []
    headers = {"User-Agent": "User/1.0"}
    
    # 1. Wikipedia Discovery
    print("🌐 Extracting Wikipedia links...")
    wiki_links = extract_east_asian_urls("https://en.wikipedia.org/wiki/List_of_cuisines")
    all_extracted_data.extend(wiki_links)

    # 2. Wikibooks Discovery
    print("📚 Extracting Wikibooks links...")
    base_wikibook = "https://en.wikibooks.org/wiki/Cookbook:East_Asian_cuisines"
    initial_items = get_links_from_page(base_wikibook, headers)
    seen_urls = set()

    for item in initial_items:
        if "Category:" in item['url']:
            sub_recipes = get_links_from_page(item['url'], headers)
            for sub in sub_recipes:
                if "Category:" not in sub['url'] and sub['url'] not in seen_urls:
                    all_extracted_data.append({"title": sub['title'], "url": sub['url'], "origin": item['title']})
                    seen_urls.add(sub['url'])
            time.sleep(0.2)
        else:
            if item['url'] not in seen_urls:
                all_extracted_data.append({"title": item['title'], "url": item['url'], "origin": "Main Page"})
                seen_urls.add(item['url'])

    # 3. Adding WordPress Category Links from Image
    print("📝 Adding WordPress blog categories...")
    blog_links = [
        {"title": "Japan Category", "url": "https://aroundtheworldin80cuisinesblog.wordpress.com/category/12-japan/"},
        {"title": "Taiwan Category", "url": "https://aroundtheworldin80cuisinesblog.wordpress.com/category/22-taiwan/"},
        {"title": "Korea Category", "url": "https://aroundtheworldin80cuisinesblog.wordpress.com/category/71-korea/"},
        {"title": "Southern China Category", "url": "https://aroundtheworldin80cuisinesblog.wordpress.com/category/32-southern-china/"}
    ]
    all_extracted_data.extend(blog_links)

    # Final Save
    with open('master_urls.json', 'w', encoding='utf-8') as f:
        json.dump(all_extracted_data, f, indent=4, ensure_ascii=False)
    
    print(f"\n✅ Done! Saved {len(all_extracted_data)} total URLs to master_urls.json")



