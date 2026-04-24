import requests
from bs4 import BeautifulSoup
import json

url = "https://www.imdb.com/chart/moviemeter/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, "html.parser")

# Find the JSON-LD script tag
json_ld = soup.find("script", type="application/ld+json")
if json_ld:
    data = json.loads(json_ld.string)
    print("JSON-LD found.")
    # Check for genres
    if "itemListElement" in data:
        first_item = data["itemListElement"][0]
        print(f"First item keys: {first_item.keys()}")
        if "item" in first_item:
            movie = first_item["item"]
            print(f"Movie keys: {movie.keys()}")
            if "genre" in movie:
                print(f"Genres: {movie['genre']}")
            else:
                print("No genres in JSON-LD item.")
else:
    print("No JSON-LD found.")
