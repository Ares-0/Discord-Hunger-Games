import asyncio
import discord
import bot_info
import emoji
import re

from discord.ext import commands

JOURNAL_CHANNEL = bot_info.JOURNAL_CHANNEL
JOURNAL_HEADER = bot_info.JOURNAL_HEADER
HEADER_CHANNEL = bot_info.HEADER_CHANNEL

class Personal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.id == self.bot.user.id:		# if self is reacting, ignore
            return
        
        if(reaction.message.channel.id in JOURNAL_CHANNEL):		# if message is in right channel
            await react_all(reaction, self.bot)

    # Repeats the argument given
    @commands.command()
    async def echo2(self, ctx, *args):
        await ctx.send(' '.join(args))

async def react_all(reaction, bot):
    guild = reaction.message.guild
    head_channel = discord.utils.get(guild.channels, id=HEADER_CHANNEL)
    head_msg = await head_channel.fetch_message(JOURNAL_HEADER)
    emjs = extract_emojis(head_msg.content)

    count = len(emjs)
    for e in emjs:
        emoji = e
        await reaction.message.add_reaction(emoji)
    
    await asyncio.sleep(5)

    print("boom B")
    print(reaction.message.reactions)
    while any(react.me for react in reaction.message.reactions):
        for react in reaction.message.reactions:
            if react.me:
                await react.remove(bot.user)


def extract_emojis(message):
    defaults = ''.join(c for c in message if c in emoji.UNICODE_EMOJI['en'])
    custom = re.findall(r'<:[a-z]*:[0-9]*>', message)
    final = [e for e in defaults]
    for x in custom:
        final.append(x)
    return final

def setup(bot):
    bot.add_cog(Personal(bot))
