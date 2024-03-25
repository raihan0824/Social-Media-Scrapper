import re

def parse_url_ig(url:str)->str:
    match = re.search(r'(?:reel|p)/([^/?]+)', url)
    if match:
        value = match.group(1)
        url_final = f"https://instagram.com/p/{value}"
    else:
        print("Value not found")
    return url_final