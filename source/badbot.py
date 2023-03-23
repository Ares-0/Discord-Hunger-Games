# Work with Python 3.6
import discord
from discord.ext import commands
import logging

import bot_info # this file is local to my computer and has my token and username. Manually enter yours below.


# Import this from bot_info or enter it yourself if this was from github.
TOKEN = bot_info.TOKEN
ME = bot_info.OWNER
HG_CHANNEL = bot_info.HG_CHANNEL

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='~', case_insensitive=True, intents=intents)
bot.remove_command('help')
# logging.basicConfig(level=logging.INFO)

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
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandNotFound):  # Quietly catch erroneous ~X commands
		pass
	elif isinstance(error, commands.MissingPermissions):
		await ctx.send('I might not have permissions for that')

@bot.event
async def on_ready():
	print("Discord.py version: ", end=' ')
	print(discord.__version__)
	#client.loop.create_task(status_task())

	await bot.load_extension("cogs.test")
	await bot.load_extension("cogs.utils")
	await bot.load_extension("cogs.server")
	await bot.load_extension("cogs.games")
	await bot.load_extension("cogs.personal")

	await bot.change_presence(activity=discord.Game(name="with simulations"))
	print('Logged in as', end=' ')
	print(bot.user.name)
	print(bot.user.id)
	print('------')

bot.run(TOKEN)
