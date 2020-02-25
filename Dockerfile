FROM node:12 AS frontend-builder

COPY ./maubot/management/frontend /frontend
RUN cd /frontend && yarn --prod && yarn build

FROM alpine:3.11

COPY requirements.txt /opt/maubot/requirements.txt
WORKDIR /opt/maubot
RUN apk add --no-cache --virtual .build-deps \
        python3-dev \
        build-base \
        git \
    && apk add --no-cache \
        ca-certificates \
        su-exec \
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
    && pip3 install -r requirements.txt \
        feedparser dateparser langdetect python-gitlab \
    && apk del .build-deps
# TODO remove pillow, magic and feedparser when maubot supports installing dependencies

COPY . /opt/maubot
COPY ./docker/mbc.sh /usr/local/bin/mbc
COPY --from=frontend-builder /frontend/build /opt/maubot/frontend
ENV UID=1337 GID=1337 XDG_CONFIG_HOME=/data
VOLUME /data

CMD ["/opt/maubot/docker/run.sh"]
