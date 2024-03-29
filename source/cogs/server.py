import asyncio
import bot_info
import datetime
import discord
import os
import random
import re
import logging

from pathlib import Path
from discord.ext import commands
from cogs.utils import report_error, getset, try_react

io_dir = Path(os.path.abspath(__file__)).parent / "../../io"
logger = logging.getLogger('discord')

class Server(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Play a local mp3 file in voice chat
    @commands.command()
    async def count(self, ctx):
        # If author not in voice, move on
        if ctx.author.voice is not None:
            voice_channel = ctx.author.voice.channel
            vc = None
            message = "Generic VC exception occured"	# generic
            try:	# this often doesn't complete still
                out = f"connecting to \"{voice_channel.name}\" in \"{voice_channel.guild.name}\"..."
                logger.info(out)
                vc = await asyncio.wait_for(voice_channel.connect(timeout=5.0), 5.0)
            except asyncio.TimeoutError:
                logger.error("timed out")
                message = "TimeoutError"
                await ctx.send("I timed out, try trying again (no promises)")
                for voice in self.bot.voice_clients:
                    print(voice)
                    if(voice.channel.guild == ctx.message.guild):
                        logger.info(f"leaving {voice.channel.name}")
                        await voice.disconnect(force=True)
            except discord.ClientException:
                print("Am I already in a channel? If not, try again")
                await ctx.send("I might already be counting somewhere")
                message = "ClientException: Already connected to a voice channel"
            except Exception as e:
                print("other exception occured")
                print(type(e))
                print(e.args)
                print(e)
                await ctx.send("Something WEIRD happened")
            if vc is None:
                await try_react(ctx, '❌')
                await report_error(self.bot, message)
                return
            
            logger.info("done connecting")
            await try_react(ctx, '✅')
            file = get_count_file()
            try:
                vc.play(discord.FFmpegPCMAudio(executable="/usr/bin/ffmpeg", source=file))
            except Exception as e:
                await report_error(self.bot, f"error connecting to voice chat:\n{e.__repr__()}")
                print(e)
                await try_react(ctx, '❌')
                await try_react(ctx, '✅')
                await vc.disconnect()

            # Sleep while audio is playing.
            while vc.is_playing():
                await asyncio.sleep(0.1)
            await vc.disconnect()
            logger.info("done disconnecting")
        else:
            await ctx.send("You are not in a voice channel.")
    
    # Saves or prints the saved gw schedule
    @commands.command()
    async def gw(self, ctx, *args):
        await getset("GW", ctx, *args)
    
    # Saves or prints the saved gw schedule PART 2
    @commands.command()
    async def eugw(self, ctx, *args):
        await getset("EUGW", ctx, *args)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        ctx = await self.bot.get_context(message)

        # debug
        # if message.author.name == "masterofares":
            # print(type(message.author) == discord.user.User) # if originated from a dm
        
        # if dm, potential suggestion box
        if type(message.author) == discord.user.User and not message.author.bot:
            await handle_suggestion_box(self, ctx, message)

        # check content for potential pedantic bangs
        content = " " + message.content.lower()
        if " teppen" in content or " tepen" in content:
            await pedantic_bangs(ctx, message, "Teppen", 15)
        
        if " keijo" in content:
            await pedantic_bangs(ctx, message, "Keijo", 8)

async def handle_suggestion_box(self, ctx, message):
    channel = self.bot.get_channel(bot_info.ERROR_CHANNEL)

    week_num = datetime.datetime.now().isocalendar()[1]
    user_hash = hash(message.author.name + str(week_num))
    suggestion_text = f"user hash: {user_hash}\nmessage: {message.content}"
    await channel.send(suggestion_text)

async def pedantic_bangs(ctx, message, text, num):
    # Dont correct every time
    if random.random() < 0.9:
        return

    # Just skip links. Its fine (technically redundant now)
    if len(re.findall(f"http\S*{text.lower}", message.content.lower())) > 0:
        return

    # If too little or too many, correct
    if f"{text}{'!'*num}" not in message.content or f"{text}{'!'*(num+1)}" in message.content:
        await ctx.send(f"Ahem, perhaps you meant {text}{'!'*num}")

# Return the mp3 file used for counting
def get_count_file():
    global io_dir
    count_files = [f for f in os.listdir(io_dir) if f.startswith("counting")]
    weights = [0]*len(count_files)
    for i,c in enumerate(count_files):
        a = c.split("_")[-1]
        weights[i] = int(a.split(".")[0])
    return str(io_dir / random.choices(count_files, weights, k=1)[0])

async def setup(bot):
    await bot.add_cog(Server(bot))
