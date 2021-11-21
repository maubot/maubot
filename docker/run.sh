#!/bin/sh

function fixperms {
	chown -R $UID:$GID /var/log /data /opt/maubot
}

function fixconfig {
	# If the DB path is the default relative path, replace it with an absolute /data path
	_db_url=$(yq e '.database' /data/config.yaml)
	if [[ _db_url == "sqlite:///maubot.db" ]]; then
		yq e -i '.database = "sqlite:////data/maubot.db"' /data/config.yaml
	fi
	_log_path=$(yq e '.logging.handlers.file.filename' /data/config.yaml)
	if [[ _log_path == "./maubot.log" ]]; then
		yq e -i '.logging.handlers.file.filename = "/var/log/maubot.log"' /data/config.yaml
	fi
	# Set the correct resource paths
	yq e -i '
		.server.override_resource_path = "/opt/maubot/frontend" |
		.plugin_directories.upload = "/data/plugins" |
		.plugin_directories.load = ["/data/plugins"] |
		.plugin_directories.trash = "/data/trash" |
		.plugin_directories.db = "/data/dbs"
	' /data/config.yaml
}

cd /opt/maubot

mkdir -p /var/log/maubot /data/plugins /data/trash /data/dbs

if [ ! -f /data/config.yaml ]; then
	cp example-config.yaml /data/config.yaml
	# Apply some docker-specific adjustments to the config
	echo "Config file not found. Example config copied to /data/config.yaml"
	echo "Please modify the config file to your liking and restart the container."
	fixperms
	fixconfig
	exit
fi

alembic -x config=/data/config.yaml upgrade head
fixperms
fixconfig
mv -n /data/plugins/*.db /data/dbs/

exec su-exec $UID:$GID python3 -m maubot -c /data/config.yaml
