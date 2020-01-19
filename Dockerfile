FROM node:12 AS frontend-builder

COPY ./maubot/management/frontend /frontend
RUN cd /frontend && yarn --prod && yarn build

FROM alpine:3.11

WORKDIR /opt/maubot
RUN apk add --no-cache \
      py3-aiohttp \
      py3-sqlalchemy \
      py3-attrs \
      py3-bcrypt \
      py3-cffi \
      build-base \
      python3-dev \
      ca-certificates \
      su-exec \
      py3-pillow \
      py3-magic \
      py3-psycopg2 \
      py3-ruamel.yaml \
      py3-jinja2 \
      py3-click \
      py3-packaging \
      py3-markdown

COPY requirements.txt /opt/maubot/requirements.txt

RUN pip3 install -r requirements.txt feedparser dateparser langdetect python-gitlab

COPY . /opt/maubot
COPY --from=frontend-builder /frontend/build /opt/maubot/frontend

# TODO remove pillow, magic and feedparser when maubot supports installing dependencies

VOLUME /data
VOLUME /config
VOLUME /plugins

CMD ["/opt/maubot/docker/run.sh"]
