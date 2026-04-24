import os
import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from supabase import create_client, Client

# Configuration
IMDB_URL = "https://www.imdb.com/chart/moviemeter/"

def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return create_client(url, key)

async def scrape_imdb():
    print(f"Fetching {IMDB_URL} with Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a realistic user agent
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Navigate and wait for the script tag to be present
        await page.goto(IMDB_URL, wait_until="load", timeout=60000)
        
        # Extract __NEXT_DATA__
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
                "year": node['releaseYear']['year'] if node.get('releaseYear') else None,
                "imdb_id": node['id'],
                "imdb_url": f"https://www.imdb.com/title/{node['id']}/",
                "rank": edge['currentRank'],
                "rating": node['ratingsSummary']['aggregateRating'] if node.get('ratingsSummary') else None,
                "genres": [g['genre']['text'] for g in node.get('genres', {}).get('genres', [])] if node.get('genres') else []
            }
            movies_to_process.append(movie)
        
        return movies_to_process

def save_to_supabase(supabase: Client, movies):
    print(f"Saving {len(movies)} movies to Supabase (single table)...")
    
    records = []
    for m in movies:
        record = {
            "title": m['title'],
            "release_year": m['year'],
            "imdb_id": m['imdb_id'],
            "imdb_url": m['imdb_url'],
            "rank": m['rank'],
            "rating": m['rating'],
            "genres": ", ".join(m['genres']) if m['genres'] else None,
            "scrape_date": datetime.now().isoformat()
        }
        records.append(record)
        
    # Insert all records at once (batch insert)
    res = supabase.table("trending_movies").insert(records).execute()
    print("Batch insert successful.")

async def main():
    try:
        movies = await scrape_imdb()
        print(f"Successfully scraped {len(movies)} movies.")
        
        if os.environ.get("SUPABASE_URL"):
            supabase = get_supabase()
            save_to_supabase(supabase, movies)
            print("Data sync complete.")
        else:
            print("SUPABASE_URL not set, skipping database sync. Scraped data sample:")
            print(json.dumps(movies[:3], indent=2))
            
    except Exception as e:
        print(f"Error: {e}")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
