import logging
import re
import json
import warnings

import requests
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException
from requests.exceptions import ContentDecodingError
from facebook_scraper import get_posts

from server.utils.instagram import IGSessionManager,parse_url_ig,extract_instagram_data,extract_instagram_username,fetch_instagram_post
from server.utils.twitter import get_tweet_id, get_tweet_result, extract_twitter_datetime,fetch_tweet_data,transform_tweet_url

from schema.response import ResponseBody


warnings.filterwarnings("ignore", module='facebook_scraper.extractors')

# Initialize loggers
logger_instagram = logging.getLogger('Scraping-Instagram')
logger_facebook = logging.getLogger('Scraping-Facebook')
logger_tiktok = logging.getLogger('Scraping-TikTok')
logger_twitter = logging.getLogger('Scraping-Twitter')

# Initialize session manager
ig_session_manager = IGSessionManager('./cookies/instagram')

scraping_router = APIRouter(tags=["Scraping Engine"])

@scraping_router.get("/api/v2/scrape-tweet")
def scrape_tweet_v2(url: str):
    try:
        tweet_id = get_tweet_id(url)
        data = get_tweet_result(tweet_id)
        created_at_str = extract_twitter_datetime(data['created_at'])
        if created_at_str:
            data['created_at'] = created_at_str
        return data
    except ContentDecodingError:
        raise HTTPException(status_code=406, detail="Cannot get tweet ID from URL")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Cannot get response from Twitter")
    except Exception as e:
        logger_twitter.error(e)
        raise HTTPException(status_code=500, detail="Unknown error!")

@scraping_router.get("/api/v1/scrape-tweet")
async def scrape_tweet_v1(url: str):
    _xhr_calls = []
    url_transformed = transform_tweet_url(url)
    try:
        data = await fetch_tweet_data(url_transformed, _xhr_calls)
        return data
    except ContentDecodingError:
        raise HTTPException(status_code=406, detail="Cannot get tweet ID from URL")
    except Exception as e:
        logger_twitter.error(e)
        raise HTTPException(status_code=500, detail="Unknown error!")


@scraping_router.get("/api/v1/scrape-ig")
def scrape_ig(url: str)->ResponseBody:
    parsed_url, shortcode = parse_url_ig(url)
    session, cookie = ig_session_manager.get_next_session()
    try:
        response = requests.get(parsed_url, cookies=cookie)
        soup = BeautifulSoup(response.text, 'html.parser')

        data_type_meta = soup.find('meta', attrs={'property': 'og:type'})
        if data_type_meta and data_type_meta.get('content') == 'profile':
            raise HTTPException(status_code=403, detail='The post is on a private user.')

        content = extract_instagram_data(soup)
        username = extract_instagram_username(soup)

        return ResponseBody(username=username,content=content,url=parsed_url)

    except ContentDecodingError:
        logger_instagram.error("Cannot scrape using bs4, use 3rd party app instead...")
        try:
            return fetch_instagram_post(session, shortcode, parsed_url)
        except Exception as e:
            logger_instagram.error(e)
            raise HTTPException(status_code=500, detail="Unknown error!")

@scraping_router.get("/api/v1/scrape-tiktok")
def scrape_tiktok(url: str)->ResponseBody:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    url = url.replace("photo", "video")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to retrieve the page")

    soup = BeautifulSoup(response.text, 'html.parser')
    script_tags = soup.find_all('script', {'type': 'application/json'})
    for tag in script_tags:
        try:
            data = json.loads(tag.string)
            if "webapp.video-detail" in str(data):
                data_parsed = data["__DEFAULT_SCOPE__"]["seo.abtest"]
                data_desc = data["__DEFAULT_SCOPE__"]["webapp.video-detail"]
                return ResponseBody(
                    username=data_desc["itemInfo"]["itemStruct"]["author"]["nickname"],
                    content=data_desc["itemInfo"]["itemStruct"]["desc"],
                    url=data_parsed["canonical"]
                )
        except json.JSONDecodeError:
            continue
    raise HTTPException(status_code=500, detail="Cannot find element!")

@scraping_router.get("/api/v1/scrape-youtube")
def scrape_youtube(url: str)->ResponseBody:
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to retrieve the page")

    soup = BeautifulSoup(response.text, 'html.parser')
    youtube_title = re.sub(r'\s-\sYouTube$', '', soup.find("title").text)
    youtube_handle = soup.find("link", {"itemprop": "name"})["content"]

    return ResponseBody(username=youtube_handle,content=youtube_title,url=url)


@scraping_router.get("/api/v1/scrape-facebook")
async def scrape_facebook(url: str)->ResponseBody:
    try:
        try:
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
                url_redirect = redirect_url_raw.split("0;url=")[1]
                response = requests.get(url_redirect, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                redirect_count += 1

            username_content = soup.find('meta', attrs={'property': 'og:title'}).get('content')

            if len(username_content.split("| By"))>1:
                username = username_content.split("| By")[1].strip()
                content = username_content.split("| By")[0].strip()
            else:
                username = username_content.split("|")[1].strip()
                content = username_content.split("|")[0].strip()

            return ResponseBody(username=username,content=content,url=url)
        
        except Exception:
            logger_facebook.error(f"Cannot scrape using bs4, use 3rd party method...")
            gen=get_posts(
                post_urls=[url],
                cookies='./cookies/facebook/facebook_cookies.json'

            )
            post = next(gen)

            return ResponseBody(username=post["username"],content=post["text"],url=url)
        
    except Exception as e:
        logger_facebook.error(e)
        raise HTTPException(
            status_code=500,
            detail="unknown error!"
        )
