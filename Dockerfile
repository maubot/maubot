FROM docker.io/alpine:3.8

ENV UID=1338 \
    GID=1338

COPY . /opt/maubot
WORKDIR /opt/maubot
RUN apk add --no-cache \
      python3-dev \
      build-base \
      py3-aiohttp \
      py3-sqlalchemy \
      py3-attrs \
      ca-certificates \
      su-exec \
 && pip3 install -r requirements.txt -r optional-requirements.txt

VOLUME /data

CMD ["/opt/mautrix-telegram/docker-run.sh"]
