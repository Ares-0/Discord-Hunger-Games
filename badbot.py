# Work with Python 3.6
import discord
from discord.ext import commands
import random
import asyncio
import io
import aiohttp
import badbot_info	# this file is local to my computer and has my token and username. Manual enter yours below.

# I'd rather not import all just yet
from hg_bot import prep_game
from hg_bot import advance_n
from hg_bot import wipe
from hg_bot import send_gallery
from hg_bot import check_over
from hg_bot import process_reaction

# Import this from badbot_info or enter it yourself if this was from github.
TOKEN = badbot_info.TOKEN
ME = badbot_info.OWNER
HG_CHANNEL = badbot_info.HG_CHANNEL

bot = commands.Bot(command_prefix='$')
context = None

####################### HUNGER GAMES ###############################

@bot.command()
async def advance(ctx, *args):
	global context
	if(not await check_channel(ctx)):
		return

	context = ctx
	n = 1
	if(len(args) > 0):
		n = int(args[0])
	async with ctx.typing():
		await advance_n(n)
	await context.message.delete()

@bot.command()
async def start(ctx):
	global context
	if(not await check_channel(ctx)):
		return
	
	context = ctx
	async with ctx.typing():
		await prep_game(ctx)
	
	await context.message.delete()

@bot.command()
async def quit(ctx):
	if(not await check_channel(ctx)):
		return
	
	# ???????????????????
	print("signing off...")
	wipe()
	await bot.logout()
	for task in asyncio.Task.all_tasks():
		task.cancel()
	print("done.")

@bot.command()
async def alive(ctx):
	if(not await check_channel(ctx)):
		return

	async with ctx.typing():
		await send_gallery(1)

@bot.command()
async def dead(ctx):
	if(not await check_channel(ctx)):
		return

	async with ctx.typing():
		await send_gallery(2)

@bot.command()
async def run(ctx, *args):
	if(not await check_channel(ctx)):
		return

	# run game to completion n times
	n = 1
	if(len(args) > 0):
		n = int(args[0])
	for x in range(n):
		await prep_game(ctx)
		while(not check_over()):
			await advance_n(100)
	print("batch done")
	await ctx.send("batch done, {0}".format(ctx.author.mention))

@bot.event
async def on_reaction_add(reaction, user):
	if(user == bot.user):
		return
	if(not await check_channel(reaction)):		# :thinking:
		return

	process_reaction(reaction.message.embeds[0].title, user)

# check if channel is appropriate Hunger Games channel
async def check_channel(ctx):
	if(ctx.message.channel.id == HG_CHANNEL):
		return True
	else:
		#emoji = '\U0001274C'
		emoji = '❌'
		await ctx.message.add_reaction(emoji)
		return False



#####################################################################






######################## EXAMPLES / TESTING ############################## 
@bot.command()
async def echo(ctx, arg):
    await ctx.send(arg)

@bot.command()
async def hello(ctx):
	await ctx.send("Hello, {0}".format(ctx.author.mention))

@bot.command()
async def embed_full(ctx, arg):
	embedVar = discord.Embed(title=arg, color=0x00ff00, url='https://discord.js.org/', description="Some description here")
	embedVar.add_field(name="Field1", value="hi", inline=True)
	embedVar.add_field(name="Field2", value="hi2", inline=True)
	str = "https://i.imgur.com/wSTFkRM.png"
	embedVar.set_image(url='https://i.imgur.com/wSTFkRM.png')
	embedVar.set_thumbnail(url=str)
	embedVar.set_author(name="Some author", url='https://discord.js.org/', icon_url="https://i.imgur.com/wSTFkRM.png")
	embedVar.set_footer(text='Some footer text here', icon_url='https://discord.js.org/')
	await ctx.send(embed=embedVar)


# async def status_task():
# 	while True:
# 		await asyncio.sleep(10)
# 		#print('beep')

	

@bot.event
async def on_ready():
	print("Discord.py version: ", end=' ')
	print(discord.__version__)
	print('Logged in as', end=' ')
	print(bot.user.name)
	print(bot.user.id)
	print('------')
	#client.loop.create_task(status_task())


bot.run(TOKEN)

