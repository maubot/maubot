#!/bin/sh

CONFIG=${CONFIG:-/data/config.yaml}

function fixperms {
	chown -R $UID:$GID /var/log /data /opt/maubot
}

function fixconfig {
	# If the DB path is the default relative path, replace it with an absolute /data path
	_db_url=$(yq e '.database' ${CONFIG})
	if [[ _db_url == "sqlite:///maubot.db" ]]; then
		yq e -i '.database = "sqlite:////data/maubot.db"' ${CONFIG}
	fi
	_log_path=$(yq e '.logging.handlers.file.filename' ${CONFIG})
	if [[ _log_path == "./maubot.log" ]]; then
		yq e -i '.logging.handlers.file.filename = "/var/log/maubot.log"' ${CONFIG}
	fi
	# Set the correct resource paths
	yq e -i '
		.server.override_resource_path = "/opt/maubot/frontend" |
		.plugin_directories.upload = "/data/plugins" |
		.plugin_directories.load = ["/data/plugins"] |
		.plugin_directories.trash = "/data/trash" |
		.plugin_directories.db = "/data/dbs"
	' ${CONFIG}
}

cd /opt/maubot

mkdir -p /var/log/maubot /data/plugins /data/trash /data/dbs

if [ ! -f ${CONFIG} ]; then
	cp example-config.yaml ${CONFIG}
	# Apply some docker-specific adjustments to the config
	echo "Config file not found. Example config copied to ${CONFIG}"
	echo "Please modify the config file to your liking and restart the container."
	fixperms
	fixconfig
	exit
fi

alembic -x config=${CONFIG} upgrade head
fixperms
fixconfig
mv -n /data/plugins/*.db /data/dbs/

exec su-exec $UID:$GID python3 -m maubot -c ${CONFIG}
