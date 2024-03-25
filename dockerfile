FROM python:3.8
ENV TZ=Asia/Jakarta
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /opt/app

# Install system dependencies required by Playwright
RUN apt-get update && apt-get install -y wget unzip libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 libxfixes3 libxi6 libxrandr2 libxss1 libxtst6 libnss3 libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libgbm1 libgtk-3-0

COPY requirements.txt ./
RUN pip install -r requirements.txt

# Install Playwright and download browsers
RUN pip install playwright
RUN playwright install

COPY . ./
EXPOSE 8045
CMD ["python", "main.py"]