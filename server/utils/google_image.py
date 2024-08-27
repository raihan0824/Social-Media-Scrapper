from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import requests
import time
from selenium.webdriver.common.action_chains import ActionChains


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.service import Service
from selenium.webdriver.support.ui import WebDriverWait
import random
import logging
import decorator

BASE_URL = 'https://images.google.com/'
CHROMEDRIVER=''

def retry(howmany, **kwargs):
    timewait=kwargs.get('timewait', 1.0) # seconds
    timeout = kwargs.get('timeout', 0.0) # seconds
    raise_error = kwargs.get('raise_error', True)
    time.sleep(timewait)
    @decorator.decorator
    def tryIt(func, *fargs, **fkwargs):
        for trial in range(howmany):
            try:
                return func(*fargs, **fkwargs)
            except Exception as e:
                error_msg = f'Error in {func.__name__} function at {trial+1} trial : {e}'
                if timeout is not None: time.sleep(timeout)
        if raise_error:
            raise Exception(f'{error_msg}')
    return tryIt

def create_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless') 
    if CHROMEDRIVER:
        service = Service(executable=CHROMEDRIVER)
        driver = webdriver.Chrome(options=chrome_options,service=service)
    else:
        driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    return driver

def query_to_url(query):
    q = quote_plus(query.strip())
    return f'https://www.google.com/search?q={q}&udm=2'

def extract_image_urls(driver, url, doc_ids):

    img_urls = []
    for doc_id in doc_ids:
        # Open Url
        driver.get(f'{BASE_URL}{doc_id}')

        # Get img_url
        time.sleep(1)
        img = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH,'//*[@id="imp"]/div[1]/div[1]/div[2]/div/div[2]/c-wiz/div/div[2]/div/a/img[1]')))
        img_urls.append(img.get_attribute('src'))
        
    return img_urls

def hover_randomly(driver, n):
    hover_1 = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="rso"]/div/div/div[1]/div/div/div[1]')))
    ActionChains(driver).move_to_element(hover_1).perform()
    for _ in range(5):
        hover = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, f'//*[@id="rso"]/div/div/div[1]/div/div/div[{random.randint(2,10)}]')))
        ActionChains(driver).move_to_element(hover).perform()
    if n>10:
        driver.execute_script('window.scrollBy(0, 1000)')
        for _ in range(5):
            hover = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, f'//*[@id="rso"]/div/div/div[1]/div/div/div[{random.randint(10,20)}]')))
            ActionChains(driver).move_to_element(hover).perform()
    if n>20:
        driver.execute_script('window.scrollBy(0, 1000)')
        for _ in range(5):
            hover = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.XPATH, f'//*[@id="rso"]/div/div/div[1]/div/div/div[{random.randint(20,30)}]')))
            ActionChains(driver).move_to_element(hover).perform()

@retry(3)
def google_get_image(query, n: int=1):
    # Open URL
    url = query_to_url(query)
    driver = create_driver()
    driver.get(url)
    time.sleep(3)
    hover_randomly(driver, n)
        
    # Get n random image ids
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    doc_ids = [tag.get('href', '') for tag in soup.find_all('a') if 'imgres' in tag.get('href', '')]
    doc_ids = list(set(doc_ids))
    # print(f'Captured doc_ids: {len(doc_ids)}')
    if not doc_ids:
        raise ValueError("No captured images")
    choosen_ids = random.choices(doc_ids, k=n)

    # Get image url
    img_urls = extract_image_urls(driver, url, choosen_ids)
    return img_urls


# Tester
if __name__ == '__main__':
    query = 'tom & jerry'
    url = google_get_image(query)
    print(url)
    url = google_get_image(query)
    print(url)
    url = google_get_image(query)
    print(url)
    url = google_get_image(query)
    print(url)
    url = google_get_image(query)
    print(url)