# Work with Python 3.6
import discord
from discord.ext import commands
import logging

import bot_info # this file is local to my computer and has my token and username. Manually enter yours below.

# HG Stuff
from hg_bot import process_reaction


# Import this from bot_info or enter it yourself if this was from github.
TOKEN = bot_info.TOKEN
ME = bot_info.OWNER
HG_CHANNEL = bot_info.HG_CHANNEL

bot = commands.Bot(command_prefix='~', case_insensitive=True)
bot.remove_command('help')
logging.basicConfig(level=logging.INFO)







# Keeping events in this file for now?

# async def status_task():
# 	while True:
# 		await asyncio.sleep(10)
# 		#print('beep')

# direct mention redirect
@bot.event
async def on_message(message):
	if bot.user.mentioned_in(message):
		if("count" in message.content):
			ctx = await bot.get_context(message)
			# await count(ctx)
			await ctx.invoke(bot.get_command("count"))
		await message.channel.send("hello!")

	await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
	if(user == bot.user):		# if bot is reacting, ignore
		return

	if(reaction.message.author.id != bot.user.id):	# if message isn't bot message, ignore
		return
	
	if(reaction.message.channel.id in HG_CHANNEL):		# if message is in HG channel
		process_reaction(reaction.message.embeds[0].title, user)

@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandNotFound):  # Quietly catch erroneous ~X commands
		pass
	elif isinstance(error, commands.MissingPermissions):
		await ctx.send('I might not have permissions for that')

@bot.event
async def on_ready():
	print("Discord.py version: ", end=' ')
	print(discord.__version__)
	print('Logged in as', end=' ')
	print(bot.user.name)
	print(bot.user.id)
	print('------')
	await bot.change_presence(activity=discord.Game(name="with simulations"))
	#client.loop.create_task(status_task())
	bot.load_extension("cogs.test")
	bot.load_extension("cogs.utils")
	bot.load_extension("cogs.server")
	bot.load_extension("cogs.games")
	bot.load_extension("cogs.personal")

bot.run(TOKEN)
