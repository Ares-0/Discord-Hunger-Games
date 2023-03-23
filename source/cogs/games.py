import bot_info
import discord
import os

from pathlib import Path
from datetime import datetime
from discord.ext import commands
from cogs.utils import getset

HG_CHANNEL = bot_info.HG_CHANNEL
GM = bot_info.GM

from hg_bot import Game

io_dir = Path(os.path.abspath(__file__)).parent / "../../io"

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.game = None # replace with dict of form {"guild_id": <game>}
        # TODO: error checking if this is None

    # List of hunger games commands
    @commands.command()
    async def hg_help(self, ctx): # TODO: update after everything else
        embed=discord.Embed(title="Hunger Games GM Commands", description="Must be a gamemaster to execute")
        embed.set_thumbnail(url="https://imgur.com/KoHvsJM.png")
        embed.add_field(name="~ready", value="Prepares the game files", inline=False)
        embed.add_field(name="~cast", value="Validates and saves attached cast.txt file", inline=True)
        embed.add_field(name="~set", value="Sets up game, displays cast", inline=False)
        embed.add_field(name="~advance <n>", value="Displays up to <n> events", inline=False)
        embed.add_field(name="~run", value="Executes a game to completion at max speed", inline=False)
        await ctx.send(embed=embed)

        embed=discord.Embed(title="Hunger Games Universal Commands", description="Anyone may execute")
        embed.set_thumbnail(url="https://imgur.com/KoHvsJM.png")
        embed.add_field(name="~alive", value="Shows a gallery of the remaining champions", inline=False)
        embed.add_field(name="~dead", value="Shows a gallery of the champions who have died", inline=False)
        embed.add_field(name="~album <link>", value="Stores given album link or displays current link", inline=False)
        embed.add_field(name="~check", value="Check if (a) user has GM permissions (b) channel has games permissions", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def advance(self, ctx, *args):
        if(not await check_channel(ctx) or not await check_gm(ctx)):
            return

        if self.game is None:
            await ctx.message.add_reaction('❌')
            return

        n = 1
        if(len(args) > 0):
            n = int(args[0])
        async with ctx.typing():
            await self.game.advance_n(n)

    @commands.command()
    async def ready(self, ctx):
        if(not await check_channel(ctx) or not await check_gm(ctx)):
            return

        self.game = Game(ctx)
        # await self.game.prep_game()
        await ctx.message.add_reaction('✅')

    @commands.command()
    async def set(self, ctx):
        if(not await check_channel(ctx) or not await check_gm(ctx)):
            return

        if self.game is None:
            self.game = Game(ctx)

        async with ctx.typing():
            await self.game.prep_game()

        await ctx.message.add_reaction('✅')

    @commands.command()
    async def end(self, ctx):
        if self.game is not None:
            self.game = None
            await ctx.message.add_reaction('✅')

    @commands.command()
    async def check(self, ctx):
        """Check permissions of both channel and author"""
        if(await check_channel(ctx)):
            await ctx.message.add_reaction('✅')
        if(await check_gm(ctx)):
            await ctx.message.add_reaction('☑️')

    @commands.command()
    async def album(self, ctx, *args):
        """Save or print the saved hg album link"""
        await getset("album", ctx, *args)

    @commands.command()
    async def cast(self, ctx):
        """Upload new cast_in.txt file, or check the current one"""
        if(not await check_gm(ctx)):
            return

        if(len(ctx.message.attachments) > 0):
            # check and save attatched file
            attach = True
            try:
                await ctx.message.attachments[0].save(fp= io_dir/"cast.txt")
            except:
                emoji = '❌'
                await ctx.message.add_reaction(emoji)
                await ctx.send("File upload error")
                return
            errs, err_str = self.game.check_list_of_champions("cast.txt")
        elif self.game is None:
            # No game, quit
            print("No games are running")
            await ctx.message.add_reaction('❌')
            return
        else:
            # check current game file
            attach = False
            print("checking current file")
            errs, err_str = self.game.check_list_of_champions()

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
                os.rename(io_dir / "cast.txt", io_dir / "cast_in.txt")
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
        self.game = Game(ctx)
        for x in range(n):
            await self.game.prep_game()
            while(not self.game.check_over()):
                await self.game.advance_n(100)
        print("batch done")
        await ctx.send(f"batch done, {ctx.author.mention}")

    @commands.command()
    async def alive(self, ctx):
        if(not await check_channel(ctx)):
            return

        async with ctx.typing():
            await self.game.send_gallery("alive")

    @commands.command()
    async def dead(self, ctx):
        if(not await check_channel(ctx)):
            return

        async with ctx.typing():
            await self.game.send_gallery("dead")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if(user == self.bot.user):		# if a bot is reacting, ignore
            return

        if(reaction.message.author.id != self.bot.user.id):	# if message isn't this bots message, ignore
            return
        
        if(reaction.message.channel.id in HG_CHANNEL):		# if message is in HG channel
            self.game.process_reaction(reaction.message.embeds[0].title, user)

async def check_channel(ctx):
    """check if channel is appropriate Hunger Games channel"""
    if(ctx.message.channel.id in HG_CHANNEL):
        return True
    else:
        emoji = '❌'
        print("bad channel attempted")
        await ctx.message.add_reaction(emoji)
        return False

async def check_gm(ctx):
    """check if user is appropriate hunger games game master"""
    if(ctx.message.author.id in GM):
        return True
    else:
        emoji = '✖️'
        print("bad author attempted")
        await ctx.message.add_reaction(emoji)
        return False

async def setup(bot):
    await bot.add_cog(Games(bot))
