from __future__ import annotations

import asyncio
import os
import random
import sys
from datetime import datetime
from os.path import dirname
from os.path import join
from typing import Final

import discord
from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv
from heckbot.adaptor.config_adaptor import ConfigAdaptor
from heckbot.types.constants import ADMIN_CONSOLE_CHANNEL_ID
from heckbot.types.constants import BOT_COMMAND_PREFIX
from heckbot.types.constants import BOT_CUSTOM_STATUS
from heckbot.types.constants import PRIMARY_GUILD_ID

load_dotenv(join(dirname(__file__), '.env'))


class HeckBot(commands.Bot):
    _token: str = os.getenv('DISCORD_TOKEN')
    after_ready_task: asyncio.Task[None]
    _cogs: Final[list] = [
        'config',
        'events',
        'gif',
        'moderation',
        'poll',
        'react',
    ]

    def __init__(self):
        intents: Intents = Intents(
            messages=True,
            message_content=True,
            typing=True,
            presences=True,
            members=True,
        )
        super().__init__(
            command_prefix=BOT_COMMAND_PREFIX,
            intents=intents,
            owner_id=277859399903608834,
            reconnect=True,
            case_insensitive=False,
        )
        self.uptime: datetime = datetime.utcnow()
        self.config = ConfigAdaptor()

    def run(self, **kwargs):
        load_dotenv(join(dirname(__file__), '.env'))
        super().run(os.getenv('DISCORD_TOKEN'))

    async def setup_hook(
            self,
    ) -> None:
        """
        Asynchronous setup code for the bot before gateway connection
        :return:
        """
        self.after_ready_task = asyncio.create_task(self.after_ready())

        self.remove_command('help')

        # load cogs
        for cog in self._cogs:
            try:
                await self.load_extension(f'src.heckbot.cogs.{cog}')
            except Exception as ex:
                print(f'Could not load extension {cog}: {ex}')
                raise ex

    async def after_ready(
            self,
    ):
        """
        Asynchronous post-ready code for the bot
        :return:
        """
        await self.wait_until_ready()

        self.uptime = datetime.utcnow()

        await self.change_presence(
            status=discord.Status.online,
            # TODO save this constant into a global config elsewhere
            activity=discord.Game(BOT_CUSTOM_STATUS),
        )

        # alert channels of bot online status
        for guild in self.guilds:
            print(
                f'{self.user} has connected to the following guild: '
                f'{guild.name}(id: {guild.id})',
            )
            if guild.id == PRIMARY_GUILD_ID:
                channel = guild.get_channel(ADMIN_CONSOLE_CHANNEL_ID)
                await channel.send(
                    self.config.get_message(guild.id, 'welcomeMessage'),
                )

        print(
            f'----------------HeckBot---------------------'
            f'\nBot is online as user {self.user}'
            f'\nConnected to {(len(self.guilds))} guilds.'
            f'\nDetected OS: {sys.platform.title()}'
            f'\n--------------------------------------------',
        )


if __name__ == '__main__':
    random.seed(0)
    HeckBot().run()
