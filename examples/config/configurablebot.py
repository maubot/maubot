from typing import Type
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from maubot import Plugin, MessageEvent
from maubot.handlers import command


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("whitelist")
        helper.copy("command_prefix")


class ConfigurableBot(Plugin):
    async def start(self) -> None:
        self.config.load_and_update()

    def get_command_name(self) -> str:
        return self.config["command_prefix"]

    @command.new(name=get_command_name)
    async def hmm(self, evt: MessageEvent) -> None:
        if evt.sender in self.config["whitelist"]:
            await evt.reply("You're whitelisted 🎉")

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
