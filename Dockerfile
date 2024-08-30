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


RUN apt-get -y install git jq
RUN pip3 install yt-dlp


COPY requirements.txt requirements.txt
RUN pip3 uninstall -y -r requirements.txt

COPY constraints.txt constraints.txt
RUN pip3 install -r requirements.txt -c constraints.txt --no-cache-dir

RUN apt-get install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libatspi2.0-0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2

RUN playwright install chromium

COPY . .

CMD [ "uvicorn", "app:app" , "--host", "0.0.0.0", "--port", "5555", "--reload" ]
