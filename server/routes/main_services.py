
from fastapi import APIRouter,status,HTTPException
import warnings 
import requests
import logging
import json
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
from server.utils.tools_ig import parse_url_ig
from datetime import datetime
import re
import time
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

    # Validate if the post private or not
    temp_url = soup.find('link', attrs={'hreflang': 'x-default'}).get('href')
    if '/p/' not in temp_url:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = 'The post is on a private user.'
        )
    
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

@scraping_router.get("/api/v1/scrape-tripadvisor")
async def scrape_ta(url: str):
    parsed_url = urlparse(url)
    if parsed_url.netloc.endswith(".com"):
        new_netloc = parsed_url.netloc.replace(".com", ".co.id")
        url = urlunparse(parsed_url._replace(netloc=new_netloc))
    about = {}
    async with async_playwright() as pw:
        browser = await pw.firefox.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        # page.on("response", intercept_response)
        await page.goto(url)
        await page.wait_for_selector("[data-test-target='restaurant-detail-info']",timeout=10000)
        page_content = await page.content()
        soup = BeautifulSoup(page_content, 'html.parser')
        restaurant_detail = soup.find("div",attrs={"data-test-target":"restaurant-detail-info"})
        title = restaurant_detail.find("h1").get_text()
        review_cards = soup.findAll("div",attrs={"class":"reviewSelector"})
        reviews=[]
        for review_card in review_cards:
            review = review_card.find("p",attrs={"class":"partial_entry"})
            reviews.append(review.get_text())
        
        rating_and_reviews_section = soup.find(text="Penilaian dan ulasan")
        if rating_and_reviews_section:
            rating_and_reviews = rating_and_reviews_section.find_previous('div').find_previous('div').get_text(separator=" ")
            rating = rating_and_reviews.split("ulasan")[1].strip().split(" ")[0]
            n_reviews = rating_and_reviews.split("ulasan")[1].strip().split("ulasan")[0].split(" ")[2]
            # Regex pattern to find the numbers before and after "dari"
            pattern = r"(\d+(?:\.\d+)?)\s+dari\s+(\d+(?:\.\d+)?)"
            match = re.search(pattern, rating_and_reviews)
            if match:
                ranking = match.group(1)
                of_total = match.group(2)
        else:
            rating_and_reviews = "No rating and reviews section found"
        
        about["reviews"] = reviews
        output = {
            "rating":rating,
            "n_reviews":n_reviews,
            "ranking":ranking,
            "of_total":of_total,
            "title":title,
            "about":about,
            "url":url
        }
        return output

@scraping_router.get("/api/v1/convert-facebook-url")
def convert_fb_url(url: str):
    headers = {
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'en-US,en;q=0.8',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    }
    with open('cookies.json', 'r') as f:
        cookies = json.load(f)

    # Create a session object
    session = requests.Session()
    session.headers.update(headers)

    # Add cookies to the session
    for c in cookies:
        expires = c.get("expirationDate") or c.get("Expires raw")
        if expires:
            expires = int(expires / 1000)
            session.cookies.set(name=c['name'], 
                                value=c['value'], 
                                domain=c['domain'],
                                secure=c["secure"],
                                path=c["path"],
                                expires=expires)

    # Make the request using the session with cookies
    response = session.get(url)

    if response.status_code == 200:
        link_header = response.headers.get('Link')
        if link_header:
            # Extract URL from the Link header
            start = link_header.find('<') + 1
            end = link_header.find('>')
            converted_url = link_header[start:end]
            if "php" not in url:
                parsed_url = urlparse(converted_url)
                final_url = urlunparse(parsed_url._replace(query='', fragment=''))
            else:
                final_url = converted_url
            return {"url":final_url}
        else:
            return "No Link header found"
    else:
        return f"Failed to retrieve location, status code: {response.status_code}"
    
@scraping_router.get("/api/v1/scrape-facebook")
async def scrape_facebook(url: str):
    if "php" in url:
        _xhr_calls = []
        async def intercept_response(response):
            if response.request.resource_type == "xhr":
                _xhr_calls.append(response)
            return response

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()
            page.on("response", intercept_response)
            await page.goto(url)
            await page.wait_for_load_state('load')
            # await page.wait_for_selector("[data-testid='tweetText']",timeout=3000)
            tweet_calls = [f for f in _xhr_calls if "https://www.facebook.com/ajax/bulk-route-definitions/" in f.url][0]
            data_raw = await tweet_calls.text()
            data = data_raw.split("for (;;);")[1]
            json_data = json.loads(data)
            first_key = next(iter(json_data['payload']['payloads']))

            # Retrieve the data using the dynamic key
            specific_data = json_data['payload']['payloads'][first_key]
            parsed_data = specific_data["result"]["exports"]["meta"]["title"]
            splitted_data = parsed_data.split("-")
            username = splitted_data[0].strip()
            content = splitted_data[1].strip()
            output = {
                "username":username,
                "content":content,
                "url":url
            }
            return output
    else:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15'
        }
        response = requests.get(url,headers=headers)
        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        redirect_count = 0
        max_redirects = 3
        while "redirecting" in soup.find("title").text.lower() and redirect_count < max_redirects:
            redirect_url_raw = soup.find('meta', attrs={'http-equiv': 'refresh'}).get('content')
            url = redirect_url_raw.split("0;url=")[1]
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            redirect_count += 1

        username = soup.find('meta', attrs={'property': 'og:title'}).get('content')
        if len(username.split("| By"))>1:
            username = username.split("| By")[1].strip()

        content = soup.find('meta', attrs={'property': 'og:description'}).get('content')

        output = {
            "username":username,
            "content":content,
            "url":url
        }

        return output