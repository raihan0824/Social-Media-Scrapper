import re
import os
import json
import logging
import instaloader
from requests.exceptions import ContentDecodingError

logger_instagram = logging.getLogger('Scraping-Instagram')

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
    

def parse_url_ig(url:str)->str:
    match = re.search(r'(?:reel|p)/([^/?]+)', url)
    if match:
        value = match.group(1)
        url_final = f"https://instagram.com/p/{value}"
        shortcode = value
    else:
        print("Value not found")
    return url_final,shortcode

def extract_instagram_data(soup):
    description_meta = soup.find('meta', attrs={'property': 'og:title'})
    if description_meta:
        description_content = description_meta.get('content')
        match = re.search(r'^(.+) on Instagram: "(.*)"', description_content, re.DOTALL)
        if match:
            quoted_text = match.group(2).strip()
            return quoted_text
    raise ContentDecodingError

def extract_instagram_username(soup):
    user_meta = soup.find('meta', attrs={'name': 'twitter:title'})
    if user_meta:
        user_content = user_meta.get('content')
        match = re.search(r"@(\w+)", user_content)
        if match:
            return match.group(1)
    logger_instagram.error('Cannot parse username')
    return ""

def fetch_instagram_post(session, shortcode, parsed_url):
    post = instaloader.Post.from_shortcode(session.context, shortcode)
    return {
        "username": post.owner_username,
        "content": post.caption,
        "url": parsed_url
    }