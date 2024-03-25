
from fastapi import APIRouter
import warnings 
import requests
import logging
import json
from playwright.async_api import async_playwright
from server.utils.tools_ig import parse_url_ig
from datetime import datetime
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse,urlunparse
logger = logging.getLogger('Scraping-Log')
        
warnings.filterwarnings("ignore")
scraping_router=APIRouter(tags=["Scraping Engine"])

@scraping_router.get("/api/v1/scrape-tweet")
async def scrape_tweet(url: str):
    _xhr_calls = []

    async def parse_date_time(date_str, time_str):
        try:
            return datetime.strptime(f'{date_str} {time_str}', '%d %b %y %I:%M %p')
        except ValueError:
            return datetime.strptime(f'{date_str} {time_str}', '%d %b %y %H:%M')

    def transform_url(url: str) -> str:
        match = re.search(r'/status/(\d+)', url)
        if match:
            tweet_id = match.group(1)
            return f"https://platform.twitter.com/embed/Tweet.html?id={tweet_id}"
        else:
            return None

    url_transformed = transform_url(url)

    async def intercept_response(response):
        if response.request.resource_type == "xhr":
            _xhr_calls.append(response)
        return response

    date_time_pattern = r'(\d{1,2}:\d{2}(?: [AP]M)?) · (\d{1,2} \b\w+\b \d{2})'

    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        page.on("response", intercept_response)
        await page.goto(url_transformed)
        await page.wait_for_selector("[data-testid='tweetText']",timeout=3000)

        tweet_calls = [f for f in _xhr_calls if "tweet-result" in f.url][0]
        data = await tweet_calls.json()
        match = re.search(date_time_pattern, data['created_at'])
        if match:
            time_str, date_str = match.groups()
            created_at = await parse_date_time(date_str, time_str)
            data['created_at'] = created_at.strftime('%Y-%m-%d %H:%M:%S') #TODO debug this to +7 hours
        
        return data

@scraping_router.get("/api/v1/scrape-ig")
def scrape_ig(url: str):
    url=parse_url_ig(url)
    response = requests.get(url)
    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    description_meta = soup.find('meta', attrs={'property': 'og:title'})
    if description_meta:
        description_content = description_meta.get('content')
    else:
        description_content = "No description found"

    # Regular expression pattern to match the username and the quoted text
    pattern = r'^(.+) on Instagram: "(.*)"'

    # Use re.search to find matches
    match = re.search(pattern,description_content ,re.DOTALL)
    if match:
        username = match.group(1).strip()
        quoted_text = match.group(2).strip()
    else:
        print("No match found")
    output = {
        "username":username,
        "content":quoted_text,
        "url":url
    }

    return output

@scraping_router.get("/api/v1/scrape-tiktok")
def scrape_tiktok(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    url = url.replace("photo","video")
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for script tags that might contain a JSON object
        # This is a guess; you'll need to find the correct script tag on the actual page
        script_tags = soup.find_all('script', {'type': 'application/json'})
        # Iterate through the script tags to find the one containing the video details
        for tag in script_tags:
            # Try to parse the content of the script tag as JSON
            try:
                data = json.loads(tag.string)
                # If the data has the key you're looking for, print it
                if "webapp.video-detail" in str(data):
                    # print(data)
                    data_json=data
                    break
            except json.JSONDecodeError:
                continue  # If JSON decoding fails, move on to the next tag
    else:
        print("Failed to retrieve the page")

    data_parsed=data_json["__DEFAULT_SCOPE__"]["seo.abtest"]

    data_desc=data_json["__DEFAULT_SCOPE__"]["webapp.video-detail"]

    tiktok_address=data_parsed["canonical"]
    # tiktok_address=urlparse(tiktok_address)
    # tiktok_address=urlunparse(tiktok_address._replace(netloc='tiktok.com', query='', fragment=''))
    tiktok_handle=data_desc["itemInfo"]["itemStruct"]["author"]["nickname"]
    tiktok_caption=data_desc["itemInfo"]["itemStruct"]["desc"]
    output={
        "username":tiktok_handle,
        "content":tiktok_caption,
        "url":tiktok_address
    }
    return output

@scraping_router.get("/api/v1/convert-tiktok-url")
def convert_tiktok_url(url:str):
    # Make a request to get the HTML content
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    response = requests.get(url, headers=headers)
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        # Look for script tags that might contain a JSON object
        # This is a guess; you'll need to find the correct script tag on the actual page
        script_tags = soup.find_all('script', {'type': 'application/json'})

        # Iterate through the script tags to find the one containing the video details
        for tag in script_tags:
            # Try to parse the content of the script tag as JSON
            try:
                data = json.loads(tag.string)
                if "seo.abtest" in str(data):
                    # print(data)
                    data_json=data
                    break
            except json.JSONDecodeError:
                continue  # If JSON decoding fails, move on to the next tag
    else:
        print("Failed to retrieve the page")

    data_parsed=data_json["__DEFAULT_SCOPE__"]["seo.abtest"]
    tiktok_address=data_parsed["canonical"]
    return {
        "url":tiktok_address,
    }

@scraping_router.get("/api/v1/scrape-youtube")
def scrape_youtube(url: str):
    # Make a request to get the HTML content
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        youtube_title=soup.find("title").text
        youtube_title = re.sub(r'\s-\sYouTube$', '', youtube_title)
        youtube_handle=soup.find("link", {"itemprop": "name"})["content"]
        output={
            "username":youtube_handle,
            "content":youtube_title,
            "url":url
        }

    return output