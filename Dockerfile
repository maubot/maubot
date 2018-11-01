FROM alpine:3.8

COPY . /opt/maubot
WORKDIR /opt/maubot
RUN apk add --no-cache \
      py3-aiohttp \
      py3-sqlalchemy \
      py3-attrs \
      py3-bcrypt \
      py3-cffi \
      ca-certificates \
 && pip3 install -r requirements.txt

VOLUME /data

CMD ["/opt/maubot/docker-run.sh"]
