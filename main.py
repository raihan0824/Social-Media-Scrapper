import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.routes import conversion_services, main_services, image_services
import uvicorn
import os
import logging
os.makedirs('logs', exist_ok=True)

app = FastAPI(
    title=f"Scraper API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(main_services.scraping_router)
app.include_router(conversion_services.conversion_router)
app.include_router(image_services.image_router)

@app.get('/')
def ping():
    return{'msg':'acknowledged'}

# 

if __name__ == '__main__':
    # Setup logging here
    class FileAndConsoleHandler(logging.StreamHandler):
        def __init__(self, filename, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.file_handler = logging.FileHandler(filename)

        def emit(self, record):
            # Write log to the console
            super().emit(record)
            
            # Write log to the file
            self.file_handler.emit(record)

        def close(self):
            self.file_handler.close()

    handler = FileAndConsoleHandler('./logs/scraper-api.log')
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('[%(asctime)s] - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logging.getLogger('').addHandler(handler)
    logging.getLogger('').setLevel(logging.INFO)
    logging.getLogger('facebook_scraper.extractors').setLevel(logging.ERROR)

    logger = logging.getLogger('Scraper API')
    
    logger.info(f"{os.getenv('service_name','development')} service started")
    logger.info(f"host: {os.getenv('HOST','0.0.0.0')}:{os.getenv('PORT','5000')}")
    uvicorn.run("main:app", port=int(os.getenv('PORT','5001')), host=os.getenv('HOST','0.0.0.0'),workers=1)  #HACK port to 8045
