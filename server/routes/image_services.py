from fastapi import APIRouter, HTTPException,Query
from typing import Optional
import logging
from collections import Counter
from typing import List
import asyncio
import random

from server.utils.google_image import google_get_image
from server.utils.twitter_image import scrape_search_result, convert_query_to_url

image_router=APIRouter(tags=["Image Engine"])

logger = logging.getLogger('Image-Scraper')


@image_router.get("/api/v1/scrape-image-google")
def scrape_image_google(queries: Optional[List[str]] = Query(None)):
    query_counter = Counter(queries)
    
    result_dict = {}
    for query, num_images in query_counter.items():
        urls = asyncio.run(google_get_image(query, n=num_images))
        result_dict[query] = urls

    results = []
    for query in queries:
        urls = result_dict[query]
        index = queries.index(query) % len(urls)
        results.append({
            'query': query,
            'url': urls[index]
        })

    return results

@image_router.get("/api/v1/scrape-image-x")
def scrape_image_x(queries: Optional[List[str]]=Query(None)):
    query_counter = Counter(queries)
    result_dict = {}
    for query, num_images in query_counter.items():
        url = convert_query_to_url(query)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        urls = loop.run_until_complete(scrape_search_result(url, []))
        urls_chosen = random.choices(urls, k=num_images)
        result_dict[query] = urls_chosen


    results = []
    for query in queries:
        urls = result_dict[query]
        index = queries.index(query) % len(urls)
        results.append({
            'query': query,
            'url': urls[index]
        })

    return results