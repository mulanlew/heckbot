from __future__ import annotations

import asyncio

import discord
from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext.commands import Context
from heckbot.adapter.reaction_table_adapter import ReactionTableAdaptor

from bot import HeckBot


class React(commands.Cog):
    """
    Cog for enabling reaction-matching-related features in the bot.
    """

    _association_repository: ReactionTableAdaptor = ReactionTableAdaptor()

    def __init__(
            self,
            bot: HeckBot,
    ) -> None:
        """
        Constructor method
        :param bot: Instance of the running Bot
        """
        self._bot: HeckBot = bot

    @commands.command()
    async def react(
            self,
            ctx: Context[Bot],
            subcommand: str,
            pattern: str | None = None,
            reaction: str | None = None,
    ) -> None:
        """
        General purpose reaction-matching root command. Aliases the
        functionality of all other reaction-matching commands by using
        the subcommand parameter to select which function to perform.
        :param ctx:
        :param subcommand:
        :param pattern:
        :param reaction:
        :return:
        """
        if subcommand == 'add':
            await self.radd(ctx, pattern, reaction)
        elif subcommand in ['remove', 'delete', 'rm', 'del']:
            await self.rdel(ctx, pattern, reaction)
        elif subcommand in ['list', 'lst']:
            await self.rlist(ctx, pattern)

    @commands.command(aliases=['reactadd', 'associate', 'assoc', 'radd'])
    async def react_add(
            self,
            ctx: Context[Bot],
            pattern: str,
            reaction: str,
    ) -> None:
        """
        Reaction association command. Creates an association between a
        pattern and reaction such that any messages which contain the
        specified pattern will be reacted with the specified reaction,
        permission permitting.
        :param ctx: Command context
        :param pattern: Pattern string to match with the reaction
        :param reaction: Reaction to respond with
        """
        await self.radd(ctx, pattern, reaction)

    @commands.command(
        aliases=[
            'reactdelete', 'dissociate', 'dissoc',
            'rdel', 'reactdel', 'reactremove',
            'reactrem', 'rrem',
        ],
    )
    async def react_delete(
            self,
            ctx: Context[Bot],
            pattern: str,
            reaction: str | None = None,
    ) -> None:
        """
        Reaction dissociation command. Removes an association between a
        pattern and reaction. If no reaction is specified, the bot will
        remove all associations with the specified pattern.

        See the documentation for the associate command for what an
        association represents.
        :param ctx: Command context
        :param pattern: Pattern string to remove associations from
        :param reaction: Reaction to (no longer) respond with
        """
        await self.rdel(ctx, pattern, reaction)

    @commands.command(
        aliases=[
            'reactlist', 'listassociations', 'rlist',
            'rlst',
        ],
    )
    async def react_list(
            self,
            ctx: Context[Bot],
            pattern: str | None = None,
    ) -> None:
        if ctx.guild is not None:
            await self.rlist(ctx, pattern)

    @commands.Cog.listener('on_message')
    async def on_message(
            self,
            message: discord.Message,
    ) -> None:
        """
        Event listener triggered whenever the bot detects a message.
        This listener will attempt to match the text contents of the
        given message with all registered reaction associations to react
        all appropriate reactions based on the contents of the message.
        :param message: The Discord message to be analyzed
        """
        if message.author.bot or (
                await self._bot.get_context(message)
        ).valid:
            return

        text = message.content.lower()
        guild = message.guild
        if guild is None:
            return

        associations = self._association_repository.get_all_reactions(
            str(guild.id),
        )
        for word, emojis in associations.items():
            if word in text:
                for emoji in emojis:
                    asyncio.get_event_loop().create_task(
                        message.add_reaction(emoji),
                    )

    async def radd(
            self,
            ctx,
            pattern,
            reaction,
    ):
        self._association_repository.add_reaction(
            str(ctx.guild.id),
            pattern,
            reaction,
        )
        await ctx.send(
            f'Successfully associated the keyword '
            f'\"{pattern}\" with the reaction '
            f'\"{reaction}\"!',
        )

    async def rdel(
            self,
            ctx,
            pattern,
            reaction,
    ):
        if reaction is None:
            self._association_repository.remove_all_reactions(
                str(ctx.guild.id),
                pattern,
            )
            await ctx.send(
                f'Successfully dissociated the keyword '
                f'\"{pattern}\" from all reactions!',
            )
        else:
            self._association_repository.remove_reaction(
                str(ctx.guild.id),
                pattern,
                reaction,
            )
            await ctx.send(
                f'Successfully dissociated the keyword '
                f'\"{pattern}\" with the reaction '
                f'\"{reaction}\"!',
            )

    async def rlist(
            self,
            ctx,
            pattern,
    ):
        if pattern:
            associations: str = str(
                self._association_repository.get_reactions(
                    str(ctx.guild.id),
                    pattern,
                ),
            )
        else:
            associations = str(
                self._association_repository.get_all_reactions(
                    str(ctx.guild.id),
                ),
            )
        await ctx.send(associations)


async def setup(
        bot: HeckBot,
) -> None:
    """
    Setup function for registering the react-match cog.
    :param bot: Instance of the running Bot
    """
    await bot.add_cog(React(bot))
