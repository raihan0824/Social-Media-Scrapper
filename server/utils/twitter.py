import re
import requests
from datetime import datetime
from playwright.async_api import async_playwright

def get_tweet_id(url):
    match = re.search(r'/status/(\d+)', url)
    if match:
        tweet_id = match.group(1)
        return tweet_id
    else:
        raise requests.exceptions.ContentDecodingError
    
def transform_tweet_url(url: str) -> str:
    match = re.search(r'/status/(\d+)', url)
    if match:
        tweet_id = match.group(1)
        return f"https://platform.twitter.com/embed/Tweet.html?id={tweet_id}"
    raise requests.exceptions.ContentDecodingError

def extract_twitter_datetime(created_at_str):
    match_date = re.search(r'(\d{1,2}:\d{2}(?: [AP]M)?) · (\d{1,2} \b\w+\b \d{2})', created_at_str)
    if match_date:
        time_str, date_str = match_date.groups()
        created_at = parse_date_time(date_str, time_str)
        return created_at.strftime('%Y-%m-%d %H:%M:%S')
    return None

def parse_date_time(date_str, time_str):
    try:
        return datetime.strptime(f'{date_str} {time_str}', '%d %b %y %I:%M %p')
    except ValueError:
        return datetime.strptime(f'{date_str} {time_str}', '%d %b %y %H:%M')
    
def get_tweet_result(id):
    url = f"https://cdn.syndication.twimg.com/tweet-result?id={id}&lang=en&token=123"
    try:
        response = requests.get(url)
        return response.json()
    except:
        raise requests.exceptions.ConnectionError
    
async def fetch_tweet_data(url_transformed, _xhr_calls):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        page.on("response", lambda response: _xhr_calls.append(response) if response.request.resource_type == "xhr" else None)
        await page.goto(url_transformed)
        await page.wait_for_selector("[role='article']", timeout=3000)
        tweet_calls = next(f for f in _xhr_calls if "tweet-result" in f.url)
        data = await tweet_calls.json()
        created_at_str = extract_twitter_datetime(data['created_at'])
        if created_at_str:
            data['created_at'] = created_at_str
        return data