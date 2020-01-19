#!/bin/sh

cd /opt/maubot

if [ ! -f /config/config.yaml ]; then
	echo "Config file not found."
	exit
fi

mkdir -p /data/trash /data/dbs
alembic -x config=/config/config.yaml upgrade head
python3 -m maubot -c /config/config.yaml
