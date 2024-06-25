import re
import os
import requests
import json
import logging
import instaloader
from bs4 import BeautifulSoup

logger_instagram = logging.getLogger('Scraping-Instagram')
logger_facebook = logging.getLogger('Scraping-Facebook')
logger_tiktok = logging.getLogger('Scraping-TikTok')
logger_twitter = logging.getLogger('Scraping-Twitter')

def parse_url_ig(url:str)->str:
    match = re.search(r'(?:reel|p)/([^/?]+)', url)
    if match:
        value = match.group(1)
        url_final = f"https://instagram.com/p/{value}"
        shortcode = value
    else:
        print("Value not found")
    return url_final,shortcode

def redirect_fb_soup(url:str)->str:
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
    
    return url_redirect

class IGSessionManager:
    def __init__(self, cookies_dir):
        self.sessions = []
        self.parsed_cookies=[]
        self.usernames=[]
        self.load_sessions(cookies_dir)
        self.current_index = 0

    def load_sessions(self, cookies_dir):
        cookie_files = [f for f in os.listdir(cookies_dir) if f.endswith('.json')]
        if not cookie_files:
            raise Exception("No cookie files found")

        for cookie_file in cookie_files:
            with open(os.path.join(cookies_dir, cookie_file), "r") as f:
                ig_cookies = json.load(f)
            username_extracted = re.search(r'cookies_(.+)\.json', cookie_file).group(1)
            self.usernames.append(username_extracted)
            cookie_dict = {cookie['name']: cookie['value'] for cookie in ig_cookies}
            self.parsed_cookies.append(cookie_dict)
            insta_loader = instaloader.Instaloader(download_pictures=False,
                                                   download_comments=False,
                                                   download_videos=False,
                                                   max_connection_attempts=1)
            insta_loader.load_session(username=username_extracted, session_data=cookie_dict)
            self.sessions.append(insta_loader)
            logger_instagram.info(f"Loaded cookies from {cookie_file}")

    def get_next_session(self):
        if not self.sessions:
            raise Exception("No sessions available")
        session = self.sessions[self.current_index]
        cookie = self.parsed_cookies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.sessions)
        logger_instagram.info(f"Use {self.usernames[self.current_index]} session..")
        return session,cookie
