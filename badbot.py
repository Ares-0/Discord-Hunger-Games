# Work with Python 3.6
import discord
from discord.ext import commands
import random
import asyncio
import io
import aiohttp
import badbot_info # this file is local to my computer and has my token and username. Manually enter yours below.

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
GM = badbot_info.GM

bot = commands.Bot(command_prefix='~')
context = None

####################### STORED DATA ################################
GW_LINK = None

class Data:
	GW_link = None
	test = "abc"
	test2 = 123

	# these temp measures aren't going to scale at all.
	def write(self):
		members = [attr for attr in dir(self) if not callable(getattr(self, attr)) and not attr.startswith("__")]
		print(members)
		print(data)

		f = open("data", "w")
		for x in members:
			name = x
			num = getattr(self, name)
			line = name + "," + str(num) + "\n"
			f.write(line)
		f.close()
		pass

	def read(self):
		f = open("data", "r")
		line = f.readline()
		while(len(line) > 1):
			x = line.split(",")
			setattr(self, x[0], x[1][:-1])
			line = f.readline()
		f.close()
		pass

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
	await context.message.delete()

@bot.command()
async def start(ctx):
	global context
	if(not await check_channel(ctx) or not await check_gm(ctx)):
		return
	
	context = ctx
	async with ctx.typing():
		await prep_game(ctx)
	
	await context.message.delete()

@bot.command()
async def quit(ctx):
	if(not await check_channel(ctx) or not await check_gm(ctx)):
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
	print("batch done")
	await ctx.send("batch done, {0}".format(ctx.author.mention))

@bot.event
async def on_reaction_add(reaction, user):
	if(user == bot.user):		# if bot is reacting, ignore
		return

	if(reaction.message.author.id != bot.user.id):	# if message isn't bot message, ignore
		return
	
	if(reaction.message.channel.id in HG_CHANNEL):		# if message is in HG channel
		process_reaction(reaction.message.embeds[0].title, user)

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


#####################################################################

@bot.command()
async def source(ctx):
	await ctx.send("https://github.com/Ares-0/Discord-Hunger-Games")

@bot.command()
async def echo(ctx, *args):
	await ctx.send(' '.join(args))

@bot.command()
async def hello(ctx):
	await ctx.send("Hello, {0}".format(ctx.author.mention))

@bot.command()
async def gw(ctx, *args):
	global data
	if(len(args) < 1):
		if(data.GW_link is None):
			await ctx.send("No link saved")
		else:
			await ctx.send(data.GW_link)
	else:
		data.GW_link = args[0]
		data.write()

@bot.command()
async def choose(ctx, *args):
	arg = ' '.join(args)
	x = arg.split(',')
	result = x[random.randint(0, len(x)-1)]

	winner = ""
	for y in x:
		if("freohr" in y):
			winner = y
			break
	
	if(random.random() < 0.5):
		result = winner
	await ctx.send(result)

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

# helper functions that don't await can function as normally
def add(a, b):
	return a + b



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
	await bot.change_presence(activity=discord.Game(name="ping ARES if weird things happen"))
	#client.loop.create_task(status_task())

	data.read()

bot.run(TOKEN)

