import asyncio
import bot_info
import discord
import os
import random
import yaml

from pathlib import Path
from discord.ext import commands

ERROR_CHANNEL = bot_info.ERROR_CHANNEL
ME = bot_info.OWNER
io_dir = Path(os.path.abspath(__file__)).parent / "../../io"

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Testing the reporting
    @commands.command()
    async def report_test(self, ctx, *args):
        await report_error(self.bot, ' '.join(args))

    # Saves or prints the saved gw schedule
    @commands.command()
    async def link(self, ctx, *args):
        await getset("LINK", ctx, *args)

    # Randomly* selects between given arguments
    @commands.command()
    async def choose(self, ctx, *args):
        arg = ' '.join(args)
        x = arg.split(',')
        result = x[random.randint(0, len(x)-1)]

        winner = ""
        for y in x:
            if("freohr" in y or "nise" in y):
                winner = y
                break
        
        if(random.random() < 0.5):
            result = winner
        await ctx.send(result)

    # List of commands
    @commands.command()
    async def help(self, ctx):
        embed=discord.Embed(title="Sailor Mars Commands", description="Use '~' to trigger.")
        embed.set_thumbnail(url="https://imgur.com/KoHvsJM.png")
        embed.add_field(name="~gw", value="Displays the current group watch schedule", inline=False)
        embed.add_field(name="~gw < link >", value="Updates the current group watch schedule", inline=False)
        embed.add_field(name="~gw2", value="Displays the group watch schedule with time sensitive highlights", inline=False)
        embed.add_field(name="~count", value="Plays a 5 second countdown in voice", inline=False)
        embed.add_field(name="~source", value="Prints github source", inline=False)
        await ctx.send(embed=embed)

    # Prints a link to the source code on github
    @commands.command()
    async def source(self, ctx):
        await ctx.send("https://github.com/Ares-0/Discord-Hunger-Games")

    # force leave voice
    @commands.command()
    async def leave(self, ctx):
        voice_channel = self.bot.voice_clients
        for x in voice_channel:
            print(f"leaving {x.channel.name}")
            await x.disconnect()

    # rest emoji reacting
    @commands.command()
    async def emote(self, ctx):
        await try_react(ctx, '✅')

    @commands.command()
    async def quit(self, ctx):
        if(ctx.message.author.id is not ME):
            return
        
        # ???????????????????
        print("signing off...")
        # wipe()
        await self.bot.logout()
        for task in asyncio.Task.all_tasks():
            task.cancel()
        print("done.")

# Print the given message in my error channel
async def report_error(bot, message):
    global ERROR_CHANNEL
    global ME
    channel = bot.get_channel(ERROR_CHANNEL)
    await channel.send(
        f"{(await bot.fetch_user(ME)).mention}, an error has occured:\n{message}"
    )

async def try_react(ctx, emoji):
    try:
        await ctx.message.add_reaction(emoji)
    except discord.Forbidden as e:
        pass
    except Exception as e:
        print(e)

class Data:
	data = {}

	def write(self):
		with open(io_dir / "data.yml", "w") as f:
			yaml.dump(self.data, f)

	def read(self):
		with open(io_dir / "data.yml", "r") as f:
			self.data = yaml.safe_load(f)
	
	def get(self, key):
		if key in self.data:
			return self.data[key]
		else:
			return None
	
	def set(self, key, value):
		self.data.update({key: value})

# Save or print user saved data
async def getset(key, ctx, *args):
	global data
		
	# if there is an attachment, save it's URL
	if(len(ctx.message.attachments) > 0):
		data.set(key, ctx.message.attachments[0].url)
		data.write()
		await try_react(ctx, '✅')
	# if there is a single argument, save the argument as URL
	elif(len(args) == 1):
		s = args[0].split("?")
		data.set(key, s[0])
		data.write()
		await try_react(ctx, '✅')
	# If many args, join and save them
	elif(len(args) > 1):
		s = ' '.join(args)
		data.set(key, s)
		data.write()
		await try_react(ctx, '✅')
	# if there is neither, print the saved data
	else:
		# nothing saved
		if(data.get(key) is None):
			await ctx.send("No link saved")
		# print saved link
		else:
			await ctx.send(data.get(key))

data = Data()
def setup(bot):
    bot.add_cog(Utils(bot))
    data.read()