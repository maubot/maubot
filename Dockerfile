FROM node:12 AS frontend-builder

COPY ./maubot/management/frontend /frontend
RUN cd /frontend && yarn --prod && yarn build

FROM alpine:3.12

RUN echo $'\
@edge http://dl-cdn.alpinelinux.org/alpine/edge/main\n\
@edge http://dl-cdn.alpinelinux.org/alpine/edge/testing\n\
@edge http://dl-cdn.alpinelinux.org/alpine/edge/community' >> /etc/apk/repositories

RUN apk add --no-cache \
        python3 py3-pip py3-setuptools py3-wheel \
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
        py3-alembic@edge \
        py3-cssselect@edge \
        py3-commonmark@edge \
        py3-pygments \
        py3-tz@edge \
        py3-tzlocal@edge \
        py3-regex@edge \
        py3-wcwidth@edge \
        # encryption
        py3-cffi \
        olm-dev \
        py3-pycryptodome \
        py3-unpaddedbase64 \
        py3-future \
        # plugin deps
        py3-pillow \
        py3-magic \
        py3-feedparser \
        py3-dateutil \
        py3-lxml \
        py3-gitlab@edge \
        py3-semver@edge
# TODO remove pillow, magic, feedparser, lxml, gitlab and semver when maubot supports installing dependencies

COPY requirements.txt /opt/maubot/requirements.txt
COPY optional-requirements.txt /opt/maubot/optional-requirements.txt
WORKDIR /opt/maubot
RUN apk add --virtual .build-deps python3-dev build-base git \
    && sed -Ei 's/psycopg2-binary.+//' optional-requirements.txt \
    && pip3 install -r requirements.txt -r optional-requirements.txt \
        dateparser langdetect python-gitlab pyquery cchardet \
    && apk del .build-deps
# TODO also remove dateparser, langdetect and pyquery when maubot supports installing dependencies

COPY . /opt/maubot
COPY ./docker/mbc.sh /usr/local/bin/mbc
COPY --from=frontend-builder /frontend/build /opt/maubot/frontend
ENV UID=1337 GID=1337 XDG_CONFIG_HOME=/data
VOLUME /data

CMD ["/opt/maubot/docker/run.sh"]
