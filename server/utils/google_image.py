import asyncio
from playwright.async_api import async_playwright
from urllib.parse import quote_plus
import random
from bs4 import BeautifulSoup

BASE_URL = "https://www.google.com"

async def create_browser_context():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    return context, browser

async def query_to_url(query):
    q = quote_plus(query.strip())
    return f'https://www.google.com/search?q={q}&udm=2'

async def extract_image_urls(page, doc_ids):
    img_urls = []
    for doc_id in doc_ids:
        # Open URL
        await page.goto(f'{BASE_URL}{doc_id}')
        await page.wait_for_timeout(1000)

        # Get img_url
        img = await page.wait_for_selector('//*[@id="imp"]/div[1]/div[1]/div[2]/div/div[2]/c-wiz/div/div[2]/div/a/img[1]', timeout=2000)
        img_urls.append(await img.get_attribute('src'))

    return img_urls

async def hover_randomly(page, n):
    hover_1 = await page.wait_for_selector('//*[@id="rso"]/div/div/div[1]/div/div/div[1]', timeout=5000)
    await hover_1.hover()

    for _ in range(5):
        hover = await page.wait_for_selector(f'//*[@id="rso"]/div/div/div[1]/div/div/div[{random.randint(2,10)}]', timeout=1000)
        await hover.hover()

    if n > 10:
        await page.evaluate('window.scrollBy(0, 1000)')
        for _ in range(5):
            hover = await page.wait_for_selector(f'//*[@id="rso"]/div/div/div[1]/div/div/div[{random.randint(10,20)}]', timeout=1000)
            await hover.hover()

    if n > 20:
        await page.evaluate('window.scrollBy(0, 1000)')
        for _ in range(5):
            hover = await page.wait_for_selector(f'//*[@id="rso"]/div/div/div[1]/div/div/div[{random.randint(20,30)}]', timeout=1000)
            await hover.hover()

async def google_get_image(query, n: int = 1):
    context, browser = await create_browser_context()
    page = await context.new_page()

    try:
        # Open URL
        url = await query_to_url(query)
        await page.goto(url)
        await page.wait_for_timeout(3000)
        await hover_randomly(page, n)

        # Get n random image ids
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        doc_ids = [tag.get('href', '') for tag in soup.find_all('a') if 'imgres' in tag.get('href', '')]
        doc_ids = list(set(doc_ids))
        
        if not doc_ids:
            raise ValueError("No captured images")
        chosen_ids = random.choices(doc_ids, k=n)

        # Get image URLs
        img_urls = await extract_image_urls(page, chosen_ids)
    finally:
        await browser.close()

    return img_urls

# Example usage
if __name__=='__main__':
    result = asyncio.run(google_get_image("tom & jerry", n=5))

    print(result)