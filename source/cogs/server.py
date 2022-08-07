import asyncio
import discord
import os
import random
import re

from pathlib import Path
from discord.ext import commands
from cogs.utils import report_error, getset

io_dir = Path(os.path.abspath(__file__)).parent / "../../io"

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
                out = "connecting to \"" + str(voice_channel.name) + "\" in \"" + str(voice_channel.guild.name) + "\"..."
                print(out, flush=True, end='')
                # vc = await voice_channel.connect(timeout=5.0)
                vc = await asyncio.wait_for(voice_channel.connect(timeout=5.0), 10.0)
            except asyncio.TimeoutError:
                print("timed out")
                message = "TimeoutError"
                await ctx.send("I timed out, try trying again (no promises)")
                for voice in self.bot.voice_clients:
                    if(voice.server == ctx.message.server):
                        print(f"leaving {voice.channel.name}")
                        await voice.disconnect()
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
                await ctx.message.add_reaction('❌')
                await report_error(message)
                return
            
            print("done")
            await ctx.message.add_reaction('✅')
            file = get_count_file()
            try:
                vc.play(discord.FFmpegPCMAudio(executable="C:/Program Files/ffmpeg/bin/ffmpeg.exe", source=file))
            except Exception as e:
                report_error("error connecting to voice chat")
                print(e)
                await ctx.message.add_reaction('❌')
                await ctx.message.clear_reaction('✅')
                await vc.disconnect()

            # Sleep while audio is playing.
            while vc.is_playing():
                await asyncio.sleep(0.1)
            await vc.disconnect()
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
        # if message.author.nick == "Ares":
        content = " " + message.content.lower()
        if " teppen" in content or " tepen" in content:
            await pedantic_bangs(ctx, message, "Teppen", 15)
        
        if " keijo" in content:
            await pedantic_bangs(ctx, message, "Keijo", 8)

async def pedantic_bangs(ctx, message, text, num):
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

def setup(bot):
    bot.add_cog(Server(bot))
