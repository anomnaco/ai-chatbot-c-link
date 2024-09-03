FROM python:3.11-slim-buster

ARG BRANCH_NAME
ENV BRANCH_NAME=$BRANCH_NAME
ARG COMMIT_HASH
ENV COMMIT_HASH=$COMMIT_HASH
ENV DSCLOUD_APP_VERSION=${BRANCH_NAME}.${COMMIT_HASH}

WORKDIR /app

#RUN apt-get -y update
RUN apt-get update && \
    apt-get install -y sudo python3-pip

RUN apt-get -y install git jq wget unzip
RUN pip3 install yt-dlp


COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt --no-cache-dir

RUN apt-get install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libatspi2.0-0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2

RUN playwright install chromium


RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    --no-install-recommends

# Add Google Chrome repository and key
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update

# Install a specific version of Google Chrome if available
RUN apt-cache madison google-chrome-stable \
    && apt-get install -y google-chrome-stable=114.0.5735.90-1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver for compatibility with Chrome version
RUN wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm chromedriver_linux64.zip

# Set Chrome as default browser (optional)
ENV CHROME_BIN=/usr/bin/google-chrome

#RUN wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip \
#    && unzip chromedriver_linux64.zip \
#    && mv chromedriver /usr/local/bin/chromedriver \
#    && chmod +x /usr/local/bin/chromedriver \
#    && rm chromedriver_linux64.zip

#RUN wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip" \
#    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
#    && rm /tmp/chromedriver.zip \
#    && chmod +x /usr/local/bin/chromedriver

COPY . .

CMD [ "uvicorn", "app:app" , "--host", "0.0.0.0", "--port", "5555", "--reload" ]
