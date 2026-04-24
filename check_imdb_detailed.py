import requests
from bs4 import BeautifulSoup

url = "https://www.imdb.com/chart/moviemeter/?view=detailed"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, "html.parser")

# Look for movie items
items = soup.select("li.ipc-metadata-list-summary-item")
print(f"Found {len(items)} items.")

if items:
    first = items[0]
    title = first.select_one("a.ipc-title-link-wrapper h3.ipc-title__text")
    print(f"Title: {title.text if title else 'N/A'}")
    
    # Check for genres
    # On IMDb detailed view, genres are usually listed under the title/rating.
    # Let's see all text in the first item.
    print(f"Item text: {first.text[:500]}...")
