import asyncio
from datetime import datetime
from urllib.parse import quote
import json
import nest_asyncio
from playwright.async_api import async_playwright
import logging
import dotenv
import os

# Scraping Functions

dotenv.load_dotenv('.env')
X_COOKIE_PATH = 'cookies/twitter/twitter_cookies.json'

BASE_URL = 'https://x.com'

nest_asyncio.apply()
logger = logging.getLogger(__name__)

async def scrape_search_result(url, _xhr_calls):
    async with async_playwright() as pw:
        # Initiate playwright
        device = pw.devices['Desktop Chrome']
        browser = await pw.chromium.launch(headless=True, slow_mo=50, args=["--start-maximized"])
        context = await browser.new_context(**device)

        # Load Cookies
        page = await context.new_page()
        with open(X_COOKIE_PATH, 'r') as f:
            cookies = json.loads(f.read())
            await context.add_cookies(cookies)
        
        page.on("response", lambda response: _xhr_calls.append(response) if response.request.resource_type == "xhr" else None)
        await page.goto(url)

        # Load Data
        await page.evaluate("window.scrollBy(0, window.innerHeight)")
        await asyncio.sleep(5)

        # Process tweets
        tweet_call = next( f for f in _xhr_calls if "SearchTimeline" in f.url )
        data = await tweet_call.json() 
        carousels = data['data']['search_by_raw_query']['search_timeline']['timeline']['instructions'][2]['entries'][0]['content']['items']
        results = []
        for ob in carousels:
            try:
                post_medias = [ o['media_url_https'] for o in ob['item']['itemContent']['tweet_results']['result']['legacy']['extended_entities']['media']]
                results.extend(post_medias)
            except Exception as _:
                pass
    return list(set(results))

def convert_query_to_url(query):
    return f'{BASE_URL}/search?q={quote(query)}&src=typed_query&f=media'

if __name__ == '__main__':
    query = 'Mulyono'

    url = convert_query_to_url(query)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    resp = loop.run_until_complete(scrape_search_result(url, []))
    print(resp)