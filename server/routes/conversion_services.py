
from fastapi import APIRouter,HTTPException
from requests.exceptions import TooManyRedirects
import requests
import logging
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse,urlunparse
from facebook_scraper import get_posts
import json

from schema.response import ConversionBody

conversion_router=APIRouter(tags=["URL Conversion Engine"])

logger_facebook = logging.getLogger('Conversion-Facebook')
logger_tiktok = logging.getLogger('Conversion-TikTok')

@conversion_router.get("/api/v1/convert-tiktok-url")
def convert_tiktok_url(url:str)->ConversionBody:
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
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve the page"
        )

    try:
        data_parsed=data_json["__DEFAULT_SCOPE__"]["seo.abtest"]
        tiktok_address=data_parsed["canonical"]
        return ConversionBody(url=tiktok_address)
    except:
        raise HTTPException(
            status_code=500,
            detail="Cannot find element!"
        )

@conversion_router.get("/api/v1/convert-facebook-url")
def convert_fb_url(url: str)->ConversionBody:
    parsed_url = urlparse(url)
    
    # Check if the URL has a video ID directly in its query
    if "v=" in parsed_url.query:
        video_id = re.search(r"v=(\d+)", url).group(1)
        return {"url": f"https://www.facebook.com/reel/{video_id}"}
    
    try:
        try:
            # Use API to resolve the final URL if not directly available
            api_url = f"https://api.redirect-checker.net/?url={url}&timeout=5&maxhops=10&format=json"
            response = requests.get(api_url).json()
            redirect_url_raw = response["data"][0]["response"]["info"]["redirect_url"]
            # Process the redirect URL to extract or clean it
            if not redirect_url_raw.strip():
                redirect_url_clean = url
            else:
                redirect_url_clean = redirect_url_raw
            
            # Clean up the URL to remove query and fragment parts if not a PHP link
            parsed_url = urlparse(redirect_url_clean)
            if "php" not in redirect_url_clean and "fbid" not in redirect_url_clean:
                final_url = urlunparse(parsed_url._replace(query='', fragment=''))
            else:
                final_url = redirect_url_clean
            
            if "login" in final_url:
                raise TooManyRedirects
            return ConversionBody(url=final_url)
        except TooManyRedirects:
            try:
                logger_facebook.error("use other converting method...")
                gen=get_posts(
                    post_urls=[url],
                    cookies='./cookies/facebook/facebook_cookies.json'

                )
                post = next(gen)
                return ConversionBody(url=post["post_url"])
            except TooManyRedirects:
                raise HTTPException(
                    status_code=508,
                    detail="Too many redirects!"
                )
        
    except Exception as e:
        logger_facebook.error(e)
        raise HTTPException(
            status_code=500,
            detail="unknown error!"
        )
