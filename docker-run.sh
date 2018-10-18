#!/bin/sh

cd /opt/maubot

# Replace database path in config.
sed -i "s#sqlite:///maubot.db#sqlite:////data/maubot.db#" /data/config.yaml
sed -i "s#- ./plugins#- /data/plugins#" /data/config.yaml
sed -i "s#./logs/maubot.log#/var/log/maubot/maubot.log#" /data/config.yaml

mkdir -p /var/log/maubot

# Check that database is in the right state
alembic -x config=/data/config.yaml upgrade head

if [ ! -f /data/config.yaml ]; then
	cp example-config.yaml /data/config.yaml
	echo "Didn't find a config file."
	echo "Copied default config file to /data/config.yaml"
	echo "Modify that config file to your liking."
	echo "Start the container again after that to generate the registration file."
	exit
fi

python3 -m maubot -c /data/config.yaml
