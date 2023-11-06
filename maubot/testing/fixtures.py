# maubot - A plugin-based Matrix bot system.
# Copyright (C) 2023 Aurélien Bompard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from pathlib import Path
import asyncio
import logging

from ruamel.yaml import YAML
import aiohttp
import pytest
import pytest_asyncio

from maubot import Plugin
from maubot.loader import PluginMeta
from maubot.standalone.loader import FileSystemLoader
from mautrix.util.async_db import Database
from mautrix.util.config import BaseProxyConfig, RecursiveDict
from mautrix.util.logging import TraceLogger

from .bot import TestBot


@pytest_asyncio.fixture
async def maubot_test_bot():
    return TestBot()


@pytest.fixture
def maubot_upgrade_table():
    return None


@pytest.fixture
def maubot_plugin_path():
    return Path(".")


@pytest.fixture
def maubot_plugin_meta(maubot_plugin_path):
    yaml = YAML()
    with open(maubot_plugin_path.joinpath("maubot.yaml")) as fh:
        plugin_meta = PluginMeta.deserialize(yaml.load(fh.read()))
    return plugin_meta


@pytest_asyncio.fixture
async def maubot_plugin_db(tmp_path, maubot_plugin_meta, maubot_upgrade_table):
    if not maubot_plugin_meta.get("database", False):
        return
    db_path = tmp_path.joinpath("maubot-tests.db").as_posix()
    db = Database.create(
        f"sqlite:{db_path}",
        upgrade_table=maubot_upgrade_table,
        log=logging.getLogger("db"),
    )
    await db.start()
    yield db
    await db.stop()


@pytest.fixture
def maubot_plugin_class():
    return Plugin


@pytest.fixture
def maubot_plugin_config_class():
    return BaseProxyConfig


@pytest.fixture
def maubot_plugin_config_dict():
    return {}


@pytest.fixture
def maubot_plugin_config_overrides():
    return {}


@pytest.fixture
def maubot_plugin_config(
    maubot_plugin_path,
    maubot_plugin_config_class,
    maubot_plugin_config_dict,
    maubot_plugin_config_overrides,
):
    yaml = YAML()
    with open(maubot_plugin_path.joinpath("base-config.yaml")) as fh:
        base_config = RecursiveDict(yaml.load(fh))
    maubot_plugin_config_dict.update(maubot_plugin_config_overrides)
    return maubot_plugin_config_class(
        load=lambda: maubot_plugin_config_dict,
        load_base=lambda: base_config,
        save=lambda c: None,
    )


@pytest_asyncio.fixture
async def maubot_plugin(
    maubot_test_bot,
    maubot_plugin_db,
    maubot_plugin_class,
    maubot_plugin_path,
    maubot_plugin_config,
    maubot_plugin_meta,
):
    loader = FileSystemLoader(maubot_plugin_path, maubot_plugin_meta)
    async with aiohttp.ClientSession() as http:
        instance = maubot_plugin_class(
            client=maubot_test_bot.client,
            loop=asyncio.get_running_loop(),
            http=http,
            instance_id="tests",
            log=TraceLogger("test"),
            config=maubot_plugin_config,
            database=maubot_plugin_db,
            webapp=None,
            webapp_url=None,
            loader=loader,
        )
        await instance.internal_start()
        yield instance
