FROM node:12 AS frontend-builder

COPY ./maubot/management/frontend /frontend
RUN cd /frontend && yarn --prod && yarn build

FROM alpine:3.11

ENV UID=1337 \
    GID=1337

COPY . /opt/maubot
COPY --from=frontend-builder /frontend/build /opt/maubot/frontend
WORKDIR /opt/maubot
RUN apk add --no-cache --virtual .build-deps \
      gcc \
      musl-dev \
      python3-dev \
  && apk add --no-cache \
      ca-certificates \
      py3-aiohttp \
      py3-sqlalchemy \
      py3-attrs \
      py3-bcrypt \
      py3-cffi \
      py3-pillow \
      py3-magic \
      py3-psycopg2 \
      py3-ruamel.yaml \
      py3-jinja2 \
      py3-click \
      py3-packaging \
      py3-markdown \
      su-exec \
  && pip3 install -r requirements.txt \
      dateparser \
      feedparser \
      langdetect \
      python-gitlab \
  && apk del .build-deps
# TODO remove pillow, magic and feedparser when maubot supports installing dependencies

VOLUME /data

CMD ["/opt/maubot/docker/run.sh"]
