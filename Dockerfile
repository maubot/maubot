FROM node:12 AS frontend-builder

COPY ./maubot/management/frontend /frontend
RUN cd /frontend && yarn --prod && yarn build

FROM alpine:3.11

RUN apk add --no-cache \
        ca-certificates \
        su-exec \
        py3-aiohttp \
        py3-sqlalchemy \
        py3-attrs \
        py3-bcrypt \
        py3-cffi \
        py3-psycopg2 \
        py3-ruamel.yaml \
        py3-jinja2 \
        py3-click \
        py3-packaging \
        py3-markdown \
        py3-pillow \
        py3-magic \
        py3-feedparser \
        py3-dateutil
# TODO remove pillow, magic and feedparser when maubot supports installing dependencies

COPY requirements.txt /opt/maubot/requirements.txt
WORKDIR /opt/maubot
RUN apk add --virtual .build-deps \
        python3-dev \
        build-base \
        git \
    && pip3 install -r requirements.txt \
        dateparser langdetect python-gitlab giteapy \
    && apk del .build-deps
# TODO also remove dateparser, langdetect, python-gitlab and giteapy when maubot supports installing dependencies

COPY . /opt/maubot
COPY ./docker/mbc.sh /usr/local/bin/mbc
COPY --from=frontend-builder /frontend/build /opt/maubot/frontend
ENV UID=1337 GID=1337 XDG_CONFIG_HOME=/data
VOLUME /data

CMD ["/opt/maubot/docker/run.sh"]
