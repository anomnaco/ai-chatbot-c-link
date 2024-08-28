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
RUN apt-get -y install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev
RUN curl https://pyenv.run | bash

# Update shell configuration
ENV PATH="/root/.pyenv/bin:/root/.pyenv/shims:${PATH}"
RUN /bin/bash -c "source ~/.bashrc && \
    eval \"\$(pyenv init --path)\" && \
    eval \"\$(pyenv init -)\" && \
    eval \"\$(pyenv virtualenv-init -)\"

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt --no-cache-dir

COPY . .

CMD [ "uvicorn", "app:app" , "--host", "0.0.0.0", "--port", "5555", "--reload" ]
