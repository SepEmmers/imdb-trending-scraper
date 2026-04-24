import os
import json
import asyncio
import csv
from datetime import datetime
from playwright.async_api import async_playwright

# Configuration
IMDB_URL = "https://www.imdb.com/chart/moviemeter/"
CSV_FILE_PATH = "data/trending_movies.csv"

async def scrape_imdb():
    print(f"Fetching {IMDB_URL} with Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        await page.goto(IMDB_URL, wait_until="load", timeout=60000)
        script_content = await page.locator("script#__NEXT_DATA__").inner_text()
        await browser.close()
        
        if not script_content:
            raise Exception("Could not find __NEXT_DATA__ script tag")
        
        data = json.loads(script_content)
        
        try:
            chart_data = data['props']['pageProps']['pageData']['chartTitles']['edges']
        except KeyError:
            print("Could not find chart data in expected JSON path.")
            raise

        movies_to_process = []
        for edge in chart_data:
            node = edge['node']
            movie = {
                "title": node['titleText']['text'],
                "release_year": node['releaseYear']['year'] if node.get('releaseYear') else None,
                "imdb_id": node['id'],
                "imdb_url": f"https://www.imdb.com/title/{node['id']}/",
                "rank": edge['currentRank'],
                "rating": node['ratingsSummary']['aggregateRating'] if node.get('ratingsSummary') else None,
                "genres": ", ".join([g['genre']['text'] for g in node.get('genres', {}).get('genres', [])]) if node.get('genres') else None,
                "scrape_date": datetime.now().isoformat()
            }
            movies_to_process.append(movie)
        
        return movies_to_process

def save_to_csv(movies):
    print(f"Saving {len(movies)} movies to CSV ({CSV_FILE_PATH})...")
    
    os.makedirs(os.path.dirname(CSV_FILE_PATH), exist_ok=True)
    file_exists = os.path.isfile(CSV_FILE_PATH)
    
    with open(CSV_FILE_PATH, mode='a', newline='', encoding='utf-8') as f:
        if not movies:
            return
            
        fieldnames = list(movies[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
            
        for m in movies:
            writer.writerow(m)
            
    print("CSV write successful.")

async def main():
    try:
        movies = await scrape_imdb()
        print(f"Successfully scraped {len(movies)} movies.")
        save_to_csv(movies)
    except Exception as e:
        print(f"Error: {e}")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

