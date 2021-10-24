# Work with Python 3.6
import discord
from discord.ext import commands
import random
import asyncio
import io
import os
import aiohttp
import math
import importlib
from pathlib import Path
from datetime import datetime
from PIL import Image
from PIL import ImageEnhance
import bot_info # this file is local to my computer and has my token and username. Manually enter yours below.

# I'd rather not import all just yet
from hg_bot import prep_game
from hg_bot import advance_n
from hg_bot import wipe
from hg_bot import send_gallery
from hg_bot import check_over
from hg_bot import process_reaction

# Import this from bot_info or enter it yourself if this was from github.
TOKEN = bot_info.TOKEN
ME = bot_info.OWNER
HG_CHANNEL = bot_info.HG_CHANNEL
GM = bot_info.GM
ERROR_CHANNEL = bot_info.ERROR_CHANNEL

bot = commands.Bot(command_prefix='~', case_insensitive=True)
bot.remove_command('help')
context = None
io_dir = Path(os.path.abspath(__file__)).parent / "../io"

####################### STORED DATA ################################
GW_LINK = None

class Data:				# move to .ini file?
	GW_link = None
	test = "abc"
	test2 = 123

	# these temp measures aren't going to scale at all.
	def write(self):
		members = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]

		with open(io_dir / "data", "w") as f:
			for name in members:
				num = getattr(self, name)
				line = name + "," + str(num) + "\n"
				f.write(line)

	def read(self):
		with open(io_dir / "data", "r") as f:
			for line in f:
				x = line.split(",")
				setattr(self, x[0], x[1][:-1])

data = Data()

####################### HUNGER GAMES ###############################

@bot.command()
async def advance(ctx, *args):
	global context
	if(not await check_channel(ctx) or not await check_gm(ctx)):
		return

	context = ctx
	n = 1
	if(len(args) > 0):
		n = int(args[0])
	async with ctx.typing():
		await advance_n(n)
	#await context.message.delete()

@bot.command()
async def ready(ctx):
	global context
	if(not await check_channel(ctx) or not await check_gm(ctx)):
		return
	
	context = ctx
	async with ctx.typing():
		await prep_game(ctx)
	
	emoji = '✅'
	await ctx.message.add_reaction(emoji)

@bot.command()
async def quit(ctx):
	if(ctx.message.author.id is not ME):
		return
	
	# ???????????????????
	print("signing off...")
	wipe()
	await bot.logout()
	for task in asyncio.Task.all_tasks():
		task.cancel()
	print("done.")

@bot.command()
async def reset(ctx):
	if(not await check_channel(ctx) or not await check_gm(ctx)):
		return
	wipe()
	emoji = '✅'
	await ctx.message.add_reaction(emoji)

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

@bot.event
async def on_reaction_add(reaction, user):
	if(user == bot.user):		# if bot is reacting, ignore
		return

	if(reaction.message.author.id != bot.user.id):	# if message isn't bot message, ignore
		return
	
	sup = 0
	if(reaction.message.channel.id in HG_CHANNEL):		# if message is in HG channel
		sup = process_reaction(reaction.message.embeds[0].title, user)
	
	verbose = False
	if sup <= 10 and sup > 0 and verbose:
		# remove previous number
		for x in reaction.message.reactions:
			if x.me:
				await x.remove(bot.user)
		# apply new number
		emoji_nums = [' ', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'] # 0 technically never used
		sup = min(sup, 10)
		await reaction.message.add_reaction(emoji_nums[sup])
	elif sup == 11:
		for x in reaction.message.reactions:
			if x.me:
				await x.remove(bot.user)
		await reaction.message.add_reaction('🔟')
		await reaction.message.add_reaction('➕')
	# do nothing for 12+
	# do nothing for -1

# Check permissions of both channel and author
@bot.command()
async def check(ctx):
	if(await check_channel(ctx)):
		emoji = '✅'
		await ctx.message.add_reaction(emoji)
	if(await check_gm(ctx)):
		emoji = '☑️'
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

# Prints a link to the current hunger games album (hardcoded fn)
@bot.command()
async def album(ctx):
	await ctx.send("<https://imgur.com/a/uGV33o6>")

# TODO
# function to reload the hg_bot.py module so I don't have to restart the whole bot if only hg_bot.py was changed

#####################################################################

# List of commands
@bot.command()
async def help(ctx):
	embed=discord.Embed(title="Sailor Mars Commands", description="Use '~' to trigger.")
	embed.set_thumbnail(url="https://imgur.com/KoHvsJM.png")
	embed.add_field(name="~gw", value="Displays the current group watch schedule", inline=False)
	embed.add_field(name="~gw < link >", value="Updates the current group watch schedule", inline=False)
	embed.add_field(name="~gw2", value="Displays the group watch schedule with time sensitive highlights", inline=False)
	embed.add_field(name="~count", value="Plays a 5 second countdown in voice", inline=False)
	embed.add_field(name="~source", value="Prints github source", inline=False)
	await ctx.send(embed=embed)

# Prints a link to the source code on github
@bot.command()
async def source(ctx):
	await ctx.send("https://github.com/Ares-0/Discord-Hunger-Games")

# Saves or prints the saved gw schedule
@bot.command()
async def gw(ctx, *args):
	global data
		
	# if there is an attachment, save it's URL
	if(len(ctx.message.attachments) > 0):
		data.GW_link = ctx.message.attachments[0].url
		data.write()
		emoji = '✅'
		await ctx.message.add_reaction(emoji)
	# if there is an argument, save the argument as URL
	elif(len(args) > 0):
		s = args[0].split("?")
		data.GW_link = s[0]
		data.write()
		emoji = '✅'
		await ctx.message.add_reaction(emoji)
	# if there is neither, print the saved data
	else:
		# nothing saved
		if(data.GW_link is None):
			await ctx.send("No link saved")
		# print saved link
		else:
			await ctx.send(data.GW_link)

# Saves or prints the saved gw schedule, but with some color manipulation
@bot.command()
async def gw2(ctx, *args):
	global data
	if(len(args) < 1):
		if(data.GW_link is None):
			await ctx.send("No link saved")
		else:
			async with aiohttp.ClientSession() as session:
				async with session.get(data.GW_link) as resp:
					if resp.status != 200:
						return await context.send('Could not download file...')
					image_data = io.BytesIO(await resp.read())
			im = Image.open(image_data)
			
			xs = (0, 102, 253, 406, 559, 739, 917, 1069, 1208)		# this is called hard coding
			dy = 22

			# get x values (aka day)
			x0, y0, x1, y1 = (0, 0, 100, im.size[1])
			day = datetime.today().weekday() + 0
			idx = (day+1)%7+1
			x0 = xs[idx]
			x1 = xs[idx+1]
			
			# get y values (aka time)
			starttime = 19.5		# time of day in CST of first watch
			now = datetime.now()
			c = now.hour + now.minute/60
			slot = math.floor((c-starttime)/0.5)
			slot = max(slot, 0)
			y0 = dy*slot + 22
			
			# color operations
			crop = im.copy()
			crop = crop.crop((x0, y0, x1, y1))
			converter = ImageEnhance.Color(im)
			im = converter.enhance(0)
			im.paste(crop, (x0, y0))

			# save and post
			crop.save("crop.png")
			im.save("gw.png")
			file=discord.File("gw.png", filename="gw.png")
			await ctx.send(file=file)

			#file=discord.File("crop.png", filename="crop.png")
			#await ctx.send(file=file)
	else:
		s = args[0].split("?")
		data.GW_link = s[0]
		data.write()
		emoji = '✅'
		await ctx.message.add_reaction(emoji)

# Play a local mp3 file in voice chat
@bot.command()
async def count(ctx):
	# If author not in voice, move on
	if ctx.author.voice is not None:
		voice_channel = ctx.author.voice.channel
		vc = None
		message = "Generic VC exception occured"	# generic
		try:	# this often doesn't complete still
			out = "connecting to \"" + str(voice_channel.name) + "\" in \"" + str(voice_channel.guild.name) + "\"..."
			print(out, flush=True, end='')
			vc = await voice_channel.connect(timeout=5.0)
		except asyncio.TimeoutError:
			print("timed out")
			message = "TimeoutError"
		except discord.ClientException:
			print("Am I already in a channel? If not, try again")
			await ctx.send("I might already be counting somewhere")
			message = "ClientException: Already connected to a voice channel"
		except Exception as e:
			print("other exception occured")
			print(type(e))
			print(e.args)
			print(e)
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

# Return the mp3 file used for counting
def get_count_file():
	global io_dir
	count_files = [f for f in os.listdir(io_dir) if f.startswith("counting")]
	weights = [0]*len(count_files)
	for i,c in enumerate(count_files):
		a = c.split("_")[-1]
		weights[i] = int(a.split(".")[0])
	return str(io_dir / random.choices(count_files, weights, k=1)[0])

# Print the given message in my error channel
async def report_error(message):
	global ERROR_CHANNEL
	global ME
	channel = bot.get_channel(ERROR_CHANNEL)
	await channel.send("{0}, an error has occured:\n{1}".format(bot.get_user(ME).mention, message))

# Testing the reporting
@bot.command()
async def report_test(ctx, *args):
	await report_error(' '.join(args))

# force leave voice
@bot.command()
async def leave(ctx):
	voice_channel = bot.voice_clients
	for x in voice_channel:
		await x.disconnect()

####################################################################

# Repeats the argument given
@bot.command()
async def echo(ctx, *args):
	await ctx.send(' '.join(args))

# Says hi
@bot.command()
async def hello(ctx):
	await ctx.send("Hello, {0}".format(ctx.author.mention))

# Randomly* selects between given arguments
@bot.command()
async def choose(ctx, *args):
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

# WIP? i was gonna check all the messages in channels or something
@bot.command()
async def collect(ctx, *args):
	#ch = bot.get_channel(764531995861712946)
	print("working...")

	count = 0
	#async for message in ch.history(limit=100):
	#	count += 1
	print(count)
	
	
	print("done")

######################## EXAMPLES ############################## 

@bot.command()
async def test_args(ctx, *args):
	await ctx.send('{} arguments: {}'.format(len(args), ', '.join(args)))

@bot.command()
async def embed_full(ctx, arg):
	embedVar = discord.Embed(title=arg, color=0x00ff00, url='https://discord.js.org/', description="Some description here")
	embedVar.add_field(name="Field1", value="hi", inline=True)
	embedVar.add_field(name="Field2", value="hi2", inline=True)
	str = "https://i.imgur.com/wSTFkRM.png"
	embedVar.set_image(url='https://i.imgur.com/wSTFkRM.png')
	embedVar.set_image(url="https://media0.giphy.com/media/W5C9c8nqoaDJWh34i6/giphy.gif")
	embedVar.set_thumbnail(url=str)
	embedVar.set_author(name="Some author", url='https://discord.js.org/', icon_url="https://i.imgur.com/wSTFkRM.png")
	embedVar.set_footer(text='Some footer text here', icon_url='https://discord.js.org/')
	await ctx.send(embed=embedVar)

@bot.command()
async def embed(ctx, arg):
	embedVar = discord.Embed(title=arg, color=0x0000ff, description="Some decription here <@!250522471227195393>")
	embedVar.set_image(url='https://i.imgur.com/wSTFkRM.png')
	await ctx.send(embed=embedVar)

# pulling images from imgur
@bot.command()
async def image2(ctx):
	async with ctx.typing():
		async with aiohttp.ClientSession() as session:
			async with session.get("https://i.imgur.com/KIdt2hYb.png") as resp:
				if resp.status != 200:
					return await ctx.send('Could not download file...')
				data = io.BytesIO(await resp.read())
				await ctx.send(file=discord.File(data, 'cool_image.png'))

# helper functions that don't await can function as normal
def add(a, b):
	return a + b



# async def status_task():
# 	while True:
# 		await asyncio.sleep(10)
# 		#print('beep')

#'''
@bot.event
async def on_message(message):
	if bot.user.mentioned_in(message):
		if("count" in message.content):
			ctx = await bot.get_context(message)
			await count(ctx)
		await message.channel.send("hello!")

	await bot.process_commands(message)
	#'''

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

	data.read()

bot.run(TOKEN)

