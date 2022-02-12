import bot_info
import discord
import os

from pathlib import Path
from datetime import datetime
from discord.ext import commands
from cogs.utils import getset

HG_CHANNEL = bot_info.HG_CHANNEL
GM = bot_info.GM

# I'd rather not import all just yet
from hg_bot import prep_game
from hg_bot import advance_n
from hg_bot import wipe
from hg_bot import send_gallery
from hg_bot import check_over
from hg_bot import check_list_of_champions

io_dir = Path(os.path.abspath(__file__)).parent / "../../io"

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # List of hunger games commands
    @commands.command()
    async def hg_help(self, ctx):
        embed=discord.Embed(title="Sailor Mars Commands", description="Use '~' to trigger. Must be a gamemaster to execute")
        embed.set_thumbnail(url="https://imgur.com/KoHvsJM.png")
        embed.add_field(name="~ready", value="Prepares the game and displays the champions", inline=False)
        embed.add_field(name="~advance <n>", value="Displays <n> events, or fewer if the round is ending", inline=False)
        embed.add_field(name="~alive", value="Shows a gallery of the remaining champions", inline=False)
        embed.add_field(name="~dead", value="Shows a gallery of the champions who have died", inline=False)
        embed.add_field(name="~run", value="Executes a game to completion with no further input necessary, at max speed", inline=False)
        embed.add_field(name="~reset", value="Reloads the settings, events, and cast list", inline=False)
        embed.add_field(name="~cast", value="Saves attached cast.txt file. Throws errors if format is incorrect", inline=False)
        embed.add_field(name="~check", value="Check 1: if user has GM permissions. Check 2: if channel has permissions for games", inline=False)
        embed.add_field(name="~album <link>", value="If blank, display current album link. Otherwise, stores given link", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def advance(self, ctx, *args):
        global context
        if(not await check_channel(ctx) or not await check_gm(ctx)):
            return

        context = ctx
        n = 1
        if(len(args) > 0):
            n = int(args[0])
        async with ctx.typing():
            await advance_n(n)

    @commands.command()
    async def reset(self, ctx):
        if(not await check_channel(ctx) or not await check_gm(ctx)):
            return
        wipe()
        emoji = '✅'
        await ctx.message.add_reaction(emoji)

    # Check permissions of both channel and author
    @commands.command()
    async def check(self, ctx):
        if(await check_channel(ctx)):
            emoji = '✅'
            await ctx.message.add_reaction(emoji)
        if(await check_gm(ctx)):
            emoji = '☑️'
            await ctx.message.add_reaction(emoji)

    # Save or print the saved hg album link
    @commands.command()
    async def album(self, ctx, *args):
        await getset("album", ctx, *args)

    # Upload new cast_in.txt file
    @commands.command()
    async def cast(self, ctx):
        if(not await check_gm(ctx)):
            return
        
        if(len(ctx.message.attachments) > 0):
            # check attatched file
            attach = True
            try:
                await ctx.message.attachments[0].save(fp= io_dir/"tmp.txt")
            except:
                emoji = '❌'
                await ctx.message.add_reaction(emoji)
                await ctx.send("File upload error")
                return
            errs, err_str = check_list_of_champions("tmp.txt")
        else:
            # check current file
            attach = False
            print("checking current file")
            errs, err_str = check_list_of_champions()

        if errs == 0:
            if attach:
                # backup old file and slot in new one
                try:
                    time = datetime.now().strftime("%y-%m-%d-%H-%M-%S")
                    os.rename(io_dir / "cast_in.txt", io_dir / f"cast_in{time}.txt")
                except Exception as e:
                    print(e)
                    emoji = '❌'
                    await ctx.message.add_reaction(emoji)
                    await ctx.send("File save error, yell at Ares")
                os.rename(io_dir / "tmp.txt", io_dir / "cast_in.txt")
            emoji = '✅'
            await ctx.message.add_reaction(emoji)
        else:
            emoji = '❌'
            await ctx.message.add_reaction(emoji)
            await ctx.send(f"Errors on {errs} lines\n```{err_str}```")

    @commands.command()
    async def run(self, ctx, *args):
        if(not await check_channel(ctx) or not await check_gm(ctx)):
            return

        # run game to completion n times
        n = 1
        if(len(args) > 0):
            n = int(args[0])
        for x in range(n):
            await prep_game(ctx)
            while(not check_over()):
                await advance_n(100)
            if(1==0):
                print(x)
        print("batch done")
        await ctx.send("batch done, {0}".format(ctx.author.mention))

    @commands.command()
    async def alive(self, ctx):
        if(not await check_channel(ctx)):
            return

        async with ctx.typing():
            await send_gallery(1)

    @commands.command()
    async def dead(self, ctx):
        if(not await check_channel(ctx)):
            return

        async with ctx.typing():
            await send_gallery(2)

    @commands.command()
    async def ready(self, ctx):
        global context
        if(not await check_channel(ctx) or not await check_gm(ctx)):
            return
        
        context = ctx
        async with ctx.typing():
            await prep_game(ctx)
        
        emoji = '✅'
        await ctx.message.add_reaction(emoji)

# check if channel is appropriate Hunger Games channel
async def check_channel(ctx):
	if(ctx.message.channel.id in HG_CHANNEL):
		return True
	else:
		emoji = '❌'
		print("bad channel attempted")
		await ctx.message.add_reaction(emoji)
		return False

# check if user is appropriate hunger games game master
async def check_gm(ctx):
	if(ctx.message.author.id in GM):
		return True
	else:
		emoji = '✖️'
		print("bad author attempted")
		await ctx.message.add_reaction(emoji)
		return False

def setup(bot):
    bot.add_cog(Games(bot))
