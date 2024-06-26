import requests
from bs4 import BeautifulSoup

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