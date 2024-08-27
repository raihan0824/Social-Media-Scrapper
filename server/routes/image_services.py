from fastapi import APIRouter,HTTPException
import logging
from collections import Counter
from typing import List
import asyncio
import random

from server.utils.google_image import google_get_image
from server.utils.twitter_image import scrape_search_result, convert_query_to_url

image_router=APIRouter(tags=["Image Scraper Engine"])

logger = logging.getLogger('Image-Scraper')


@image_router.post("/api/v1/scrape-image-google")
def scrape_image_google(queries: List[str]):
    query_counter = Counter(queries)
    results = []
    for query, num_images in query_counter.items():
        urls = google_get_image(query, num_images)
        for url in urls:
            results.append((query, url))
    return results

@image_router.post("/api/v1/scrape-image-x")
def scrape_image_x(queries: List[str]):
    query_counter = Counter(queries)
    results = []
    for query, num_images in query_counter.items():
        url = convert_query_to_url(query)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        urls = loop.run_until_complete(scrape_search_result(url, []))
        urls_chosen = random.choices(urls, k=num_images)
        for url in urls_chosen:
            results.append((query, url))


    return results