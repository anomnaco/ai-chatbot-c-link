FROM python:3.11-slim-buster

ARG BRANCH_NAME
ENV BRANCH_NAME=$BRANCH_NAME
ARG COMMIT_HASH
ENV COMMIT_HASH=$COMMIT_HASH
ENV DSCLOUD_APP_VERSION=${BRANCH_NAME}.${COMMIT_HASH}

WORKDIR /app

RUN apt-get -y update
RUN apt-get -y install git jq
RUN pip3 install yt-dlp

RUN apt-get update && \
    apt-get install -y \
    sudo \
    curl \
    git \
    build-essential \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libffi-dev \
    liblzma-dev

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt --no-cache-dir

COPY . .

CMD [ "uvicorn", "app:app" , "--host", "0.0.0.0", "--port", "5555", "--reload" ]
