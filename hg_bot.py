# LIBRARIES
from enum import Enum
from enum import IntEnum
import discord
import random
import re
import io
import aiohttp
import os
import math
from PIL import Image


#		CLASSES

# List of all participating champions
class Champions:
	roster = []
	num = 0		# oh yeah this exists
	
	def clear_roster(self):
		self.roster.clear()
		self.num = 0
	
	def add_champion(self, new_champ):
		self.roster.append(new_champ)
		self.num += 1
	
	def clear(self):
		self.roster.clear()
		self.num = 0
	
	def about(self):
		print("\nNumber of champions: " + str(self.num))
		for x in self.roster:
			x.about()
		print()
	
	def get_count_alive(self):
		count = 0
		for x in self.roster:
			if(x.status == Status.ALIVE):
				count += 1
		return count

	# Return a list of champions who are alive
	def get_list_alive(self):
		out = []
		for x in self.roster:
			if(x.status == Status.ALIVE):
				out.append(x)
		return out
	
	# Return a list of champions who are dead
	def get_list_dead(self):
		out = []
		for x in self.roster:
			if(x.status == Status.DEAD):
				out.append(x)
		return out

# Single champion object
class Champion:
	def __init__(self, name, image, gender, status):
		self.name = name
		self.image_link = str(image + "s.png")			# NOTE discord.py does NOT like the b, l, t, m, etc extensions on imgur
		self.gender = gender
		self.status = status
		self.thumbnail = None
	def about(self):
		print("\n" + self.name + "\n\t" + self.image_link + 
		    "\n\t" + self.gender.name + "\n\t" + self.status.name)
	def set_status(self, status):
		self.status = status
	def set_status_dead(self):
		self.status = Status.DEAD
	def set_thumbnail(self, data):
		self.thumbnail = data

# Collected lists of all events
class Events:
	events_structure = [[[] for j in range(5)] for i in range(2)]
	# structure of all events in game
	# events_structure[Is_Fatal][EventType] has list of events matching appropraite Is_Fatal and EventType

	def about(self):
		lens = []
		for x in self.events_structure[0]:
			lens.append(len(x))
		print("Harmless:")

		print("# of BloodbathEvents: " + str(lens[0]))
		print("# of DayEvents: "       + str(lens[1]))
		print("# of NightEvents: "     + str(lens[2]))
		print("# of FeastEvents: "     + str(lens[3]))
		print("# of ArenaEvents: "     + str(lens[4]))
		print()

		lens.clear()
		for x in self.events_structure[1]:
			lens.append(len(x))
		print("Fatal")
		print("# of BloodbathEvents: " + str(lens[0]))
		print("# of DayEvents: "       + str(lens[1]))
		print("# of NightEvents: "     + str(lens[2]))
		print("# of FeastEvents: "     + str(lens[3]))
		print("# of ArenaEvents: "     + str(lens[4]))
		print()
	
	def get_type_list(self, type, fatal):
		return self.events_structure[fatal][type]
	
	def get_random_event(self, max_champs, type, fatal, kill_limit):
		type_events = self.get_type_list(type, fatal)
		possible_events = []
		#print(str(max_champs) + ", " + str(fatal) + ", " + str(kill_limit))
		for x in type_events:
			if(x.numChampions <= max_champs):
				if(x.get_count_killed() <= kill_limit):
					possible_events.append(x)
		idx = int(random.random() * len(possible_events)-1)
		return possible_events[idx]
	
	def add_event(self, new_event, type, fatal):
		# error checking?
		self.events_structure[fatal][type].append(new_event)
	
	def clear(self):
		for x in self.events_structure[0]:
			x.clear()
		for x in self.events_structure[1]:
			x.clear()

# Single event object		
class Event:
	def __init__(self, type, numChampions, killers, killed, text):
		self.type = type
		self.numChampions = numChampions
		self.killers = killers
		self.killed = killed
		self.raw_text = text

	def about(self):
		print("\n" + self.raw_text)
		print(self.type.name + " \t" + str(self.numChampions) + " \t", end = " ")
		print("\nkillers: ", end = " ")
		for x in self.killers:
			print(x, end = " ")
		print("\nkilled: ", end = " ")
		for x in self.killed:
			print(x, end = " ")
		print()

	def get_final_text(self, players):
		out = self.raw_text
		
		# replace stuff like (Player1), (pro2), etc
		m = re.search(r"(\([\w\/]*\d\))", out)				# \([\w\/]*\d\)
		count = 0
		while(m):
			reg = m[0]
			
			char_num = int(reg[-2])
			type = reg[1:-2]
			
			# his / her / their
			# he / she / they
			# him / her / them
			# himself / herself / themselves
			
			replace = "ERROR"
			g = players[char_num - 1].gender
			# why doesn't python have switch cases
			if(type == "Player"):
				replace = players[char_num - 1].name
				replace = "\"" + replace + "\""			# replace with bold or something later
			elif(type == "them"):
				options = ["her", "him", "them"]
				replace = options[g]
			elif(type == "they"):
				options = ["she", "he", "they"]
				replace = options[g]
			elif(type == "their"):
				options = ["her", "his", "their"]
				replace = options[g]
			elif(type == "themselves"):
				options = ["herself", "himself", "themselves"]
				replace = options[g]
			
			out = out.replace(reg, replace)
			m = re.search(r'(\([\w\/]*\d\))', out)
					
			
			# infinite loop catch
			count += 1
			if(count >= 10):
				break
		return out
	
	def get_count_killed(self):
		return len(self.killed)

	async def print_event(self, event_champs):
		global context
		global params

		msg = self.get_final_text(event_champs)
		print(msg)
		color = 0x00ff00
		if(len(self.killed) > 0):
			color = 0xff0000
		
		line = str(params.get_fatal_chance()) + "    " + msg + "\n"
		record(line)

		await send_event_image(event_champs, msg, color)

# Collection of statistics
class Stats:
	elapsed_turns = 0
	elapsed_events = 0

	def increment_turn(self):
		self.elapsed_turns += 1
	
	def increment_event(self):
		self.elapsed_events += 1

	def about(self):
		global params
		global champions
		print("Elapsed Turns: " + str(self.elapsed_turns))
		print("Elapsed Events: " + str(self.elapsed_events))
		print("Fatal Chance: " + str(params.get_fatal_chance()))

		filename = "stats.csv"
		path = os.path.dirname(__file__)
		path = os.path.join(path, filename)

		f = open(path, 'a')
		line = "{0}, {1}, {2}, {3}\n".format(champions.num, self.elapsed_turns, self.elapsed_events, params.get_fatal_chance())
		f.write(line)
		f.close()
	
	def clear(self):
		self.elapsed_events = 0
		self.elapsed_turns = 0

# Collection of Reaction data structures
class Reactions:
	champions = []
	users = []
	reactions = [[0 for i in range(20)] for j in range(8)]
	totals = []

	def fill_champions(self, champs):
		self.champions.clear()
		for x in champs:
			self.champions.append(x.name)
		while(len(self.champions) < 8):
			self.champions.append(None)
	
	def add_reaction(self, champ, user):
		idx = -1
		
		# get index of user
		try:
			idx = self.users.index(user.id)
		except:
			self.users.append(user.id)
			idx = len(self.users) - 1
		idx_u = idx

		idx_c = self.get_champ_idx(champ)

		# increment the count for this message / user combo, but not higher than 3
		count = self.reactions[idx_c][idx_u]
		if(count < 3):
			self.reactions[idx_c][idx_u] = self.reactions[idx_c][idx_u] + 1
	
	def about(self):
		count = 0
		print()
		for x in self.reactions:
			for y in x:
				print(str(y) + ' ', end=' ')
			print(self.champions[count])
			count += 1
		print("\nPrevious round totals:")
		for x in self.totals:
			print(x, end=' ')
		print()
		
	def get_fatal_chance(self, champ):
		global params
		SPONSOR_WEIGHT = 0.5
		print(champ.name)

		# two aspects to this
		# (1) FATAL_CHANCE
		# (2) Support

		# 0% support keeps FATAL_CHANCE
		# 100% support reduces fatal chance to 0
		# this is before taking into account sponsor weight

		# how strong the sponsorship is. 1 is maximum (full aid), 0 is minimum (no aid)
		sponsor = 0
		c = self.get_champ_idx(champ)
		if(sum(self.totals) != 0):
			sponsor = self.totals[c] / 3*len(self.users)	# sponsorships given / sponsorships possible
		
		last = params.get_fatal_chance() * (1-sponsor*SPONSOR_WEIGHT)

		print(last)
		return last
	
	# called at the start of a round, this compiles the reactions into totals that affect the next set of events
	def update_count(self):
		self.totals.clear()
		for x in range(len(self.reactions)):
			self.totals.append(sum(self.reactions[x]))
		for x in range(8):
			for y in range(len(self.reactions[x])):
				self.reactions[x][y] = 0

	def get_champ_idx(self, champ):
		try:
			idx = self.champions.index(champ.name)
			return idx
		except:
			print("error, champion " + champ.name + " is not in final 8")
			return -1

# Collection of settings, parameters, etc
class Params:
	fatal_chance = 0.3

	def get_fatal_chance(self):
		return self.fatal_chance
	
	# called at the start of new turns
	def update_fatal_chance(self):
		global champions
		global current_type
				
		x = champions.get_count_alive()
		
		# y(x) = 0.1*log2(x/10+1)+0.2
		self.fatal_chance = 0.1*math.log2(x/10+1)+0.2

		# y(x) = x/200 + 0.2
		self.fatal_chance = x/200 + 0.15

		# add day / night bias
		if(current_type is EventType.Day):
			self.fatal_chance += 0.05
		if(current_type is EventType.Night):
			self.fatal_chance -= 0.05
		
		# apply floor to value
		self.fatal_chance = max(0.2, self.fatal_chance)



#		ENUMS

class Gender(IntEnum):
	NEUTRAL = 2
	MALE    = 1
	FEMALE  = 0
	
class Status(Enum):
	ALIVE = 0
	DEAD = 1

class EventType(IntEnum):
	Bloodbath = 0
	Day = 1
	Night = 2
	Feast = 3
	Arena = 4
	
	def __str__(self):
		return self.name

#		GLOBALS

champions = Champions()
events = Events()
stats = Stats()
reactions = Reactions()
params = Params()

# Progress
game_over = False
endgame = False
current_turn = 0
current_event = 0
imported = False

# Lists
newly_dead = []
acting_champions = []

# Other?
current_type = EventType.Bloodbath
context = None
import_limit = 24		# for testing, arbitrarily limit the number of champions to import OLD
# should some of this go into a class? YES!

#		PREP FUNCTIONS

# import and other start of game setup
async def prep_game(ctx):
	global context
	global newly_dead
	global current_turn
	global current_event
	global game_over
	global stats
	global imported
	global endgame
	
	# champions and events should be filled at this point
	# setup variables that need it
	newly_dead.clear()
	current_turn = 0
	current_event = 0
	game_over = False
	endgame = False
	stats.clear()

	context = ctx
	if(not imported):
		await import_all()
		imported = True
	else:
		print("resetting current cast")
		for x in champions.roster:
			x.set_status(Status.ALIVE)
	await send_gallery(0)

# perform all import / download functions
async def import_all():
	global champions
	global events

	#champions = None
	champions = Champions()
	events = Events()

	import_list_of_champions()
	import_list_of_events()
	await download_images(champions.roster)

	events.about()

# get list of champions from file
def import_list_of_champions():
	global champions
	global import_limit
	imported = 0
	filename = "hg_files/cast_in.txt"
	path = os.path.dirname(__file__)
	path = os.path.join(path, filename)

	f = open(path, "r")
	
	print("Importing champions...")
	line = f.readline()	# eat first line
	line = f.readline() # get #entries value
	entries = int(line[:-1])
	line = f.readline()
	while(len(line) > 1):
		#work
		x = line.split("\t")
		
		# if the .png is there, remove it. Later operations require it to not be there
		link = x[1]
		if(x[1][-4:] == ".png"):
			link = link[:-4]

		new_champ = Champion(x[0].strip(), link, Gender(int(x[2])), Status(0))
		champions.add_champion(new_champ)
		imported += 1
		
		# prep next iteration
		#if(imported >= import_limit):	OLD
		if(imported >= entries):
			break
		line = f.readline()
	
	f.close()

# get and sort events from file
def import_list_of_events():
	import_limit = 1000
	imported = 0
	
	filename = "hg_files/events_in.txt"
	path = os.path.dirname(__file__)
	path = os.path.join(path, filename)

	f = open(path, "r", encoding="utf8")
	
	print("Importing events...")
	line = f.readline() # eat first line
	line = f.readline()
	while(len(line) > 0):
		#print(line)
		# ignore lines that start with "~". For dev sanity
		if(line.startswith('~')):
			line = f.readline()
			continue
			
		x = line.split("\t")
		while("" in x): 
			x.remove("")
		
		# TODO: add events with multiple types to multiple lists
		type = EventType.Day
		for t in EventType:
			if(x[0] in t.name):
				type = t
				break
		numChampions = int(x[1])
		if(x[2] == "na" or x[2] == "None"):
			killers = []
		else:
			killers = x[2].split(", ")
		if(x[3] == "na" or x[3] == "None"):
			killed = []
		else:
			killed = x[3].split(", ")
		text = x[4].strip()
		new_event = Event(type, numChampions, killers, killed, text)
		
		fatal = (len(killed) > 0)
		events.add_event(new_event, type, fatal)

		line = f.readline()
		imported += 1
		if(imported >= import_limit):
			break
	f.close()

# download thumbnails for each champion and store them for future use
async def download_images(champs_list):
	global context
	print("Downloading images...")
	async with aiohttp.ClientSession() as session:
		for x in champs_list:
			async with session.get(x.image_link) as resp:
				if resp.status != 200:
					return await context.send('Could not download file...')
				data = io.BytesIO(await resp.read())
				x.set_thumbnail(data)
	#for x in champs_list:
	#	await context.send(file=discord.File(x.thumbnail, x.name + '.png'))

#		PROGRESS FUNCTIONS

# advance by N events, showing turn starts and ends if need be
async def advance_n(n):
	global acting_champions
	global current_event
	global current_turn
	global current_type
	global game_over
	global endgame
	global reactions

	if(game_over):
		return

	# add check to make sure the game has been initialized (imported stuff etc)
	# CANT EVEN SEND A MESSAGE TO YELL AT USER UNTIL THEY DO $START LMAO
	if(champions.num < 1):
		await send_embed("Error, no champions", None, 0xff0000)
		return


	# If start of turn, do some setup
	if(current_event == 0):			# maybe move to another function
		global stats
		global params
		stats.increment_turn()
		acting_champions = champions.get_list_alive()
		random.shuffle(acting_champions)
		reactions.update_count()
		
		# In final 8, start accepting emotes as sponsorship
		if(not endgame and len(acting_champions) <= 8):
			# print message
			endgame = True
			print("final 8")
			record("final 8")
			await send_gallery(3, "Final {0}".format(len(acting_champions)), "From now on, react to events to offer your sponsorship to these champions.")
			reactions.fill_champions(acting_champions)
			return		# prompt for another 'advance n'

		if(endgame):
			reactions.about()

		# decide round type
		if(current_turn == 0):
			current_type = EventType.Bloodbath
			text = "Bloodbath"
			print(text)
			record("\n" + text+ "\n")
			await send_embed(text, None, 0x0000ff)
		else:
			current_type = EventType((current_turn+1)%2 + 1)		# alternate day and night with day being first
			text = str(current_type).upper() + " " + str(int((current_turn+1)/2)) 
			print(text)
			record("\n" + text+ "\n")
			await send_embed(text, None, 0x0000ff)
		
		# TODO
		# Add cornocopia event on day 4(?) and random big events throughout

		params.update_fatal_chance()
	
	# advance up to as many turns as the user requested
	advanced = 0
	while(len(acting_champions) > 0 and advanced < n):
		# make sure that the last event on the last remaining champion is not fatal
		await run_event(acting_champions, current_type)
		advanced += 1
		current_event += 1
	
	# check if game is over
	await check_for_winner()

	# if this turn is over, set up next turn
	if(len(acting_champions) == 0 and game_over is False):	
		current_event = 0
		text = str(current_type) + " Over"
		print(text)
		await send_embed(text, None, 0x0000ff)
		
		# announce dead at end of night and at end of bloodbath
		if(current_type is EventType.Night or current_type is EventType.Bloodbath):
			await send_newly_dead()
		
		current_turn += 1

# setup and run a single event featuring 1 or more champions
async def run_event(acting_list, type):
	global stats
	global reactions
	global params
	stats.increment_event()	
	
	# Get fatal chance of this event
	num_alive = champions.get_count_alive()
	
	if(num_alive <= 8):
		chance = reactions.get_fatal_chance(acting_list[-1])
	else:
		chance = params.get_fatal_chance()
	fatal = random.random() < chance

	champions_remaining = len(acting_list)	# event must not exceed # of champions left
	if(num_alive <= 1):
		fatal = False

	# don't kill everyone if these are the only champions left
	kill_limit = champions_remaining
	if(num_alive == champions_remaining):
		kill_limit -= 1

	# select an event from the appropriate list
	this_event = events.get_random_event(champions_remaining, type, fatal, kill_limit)
	
	# pull champions
	event_champs = []
	for x in range(0, this_event.numChampions):
		event_champs.append(acting_list.pop())

	# mark 'killed' as dead (has to happen before display for ease)
	for x in this_event.killed:
		dead = event_champs[int(x[6:])-1]
		dead.set_status_dead()
		newly_dead.append(dead)

	# display event
	await this_event.print_event(event_champs)
	
	# TODO
	# give 'killers' a point
	

# Check if one champion is left, and announce if so
async def check_for_winner():
	global champions
	global game_over
	global context

	alive = champions.get_list_alive()
	if(len(alive) > 1):
		return False
	else:
		game_over = True
		if(len(alive) < 1):
			print("Error, no one survived")
			await context.send("No winners, {0}".format(context.author.mention))
			return True
		winner = alive[0]
		text = "The winner is: " + winner.name
		print(text)
		
		line = str(params.get_fatal_chance()) + "    " + text + "\n"
		record(line)
		
		link = winner.image_link
		link = link[:-5] + link[-4:]
		print(link)
		await send_embed(text, link, 0x0000ff)		# image is compressed as shit but it's fine
		
		# prep stats and stuff
		stats.about()
		return True

#		MESSAGE FUNCTIONS

# create and send a simple embed
async def send_embed(arg, image_url, rgb):
	global context
	if(context is None):
		print("No context yet")
		return
	
	if(rgb is None):
		e_color = 0x00ff00
	else:
		e_color = rgb
	embedVar = discord.Embed(title=arg, color=e_color)

	if(image_url is not None):
		#embedVar.set_image(url='https://i.imgur.com/wSTFkRM.png')
		embedVar.set_image(url=image_url)
	
	await context.send(embed=embedVar)

# send newly dead embed (vertical stitch)
async def send_newly_dead():
	global newly_dead
	global context
	if(context is None):
		print("Error, no context yet")
		return
	
	num = len(newly_dead)
	e_title = "{0} pictures have been removed due to violating r/anime's rules".format(num)			# we can have a few of these
	print(e_title)
	record(e_title + "\n")
	embedVar = discord.Embed(title=e_title, color=0x0000ff)

	if(num > 0):
		im_final = Image.new("RGBA", (90, 90*num + 4*(num-1)))
		i = 0
		for x in newly_dead:
			im = Image.open(x.thumbnail)
			im = im.convert('LA')
			im_final.paste(im, (0, 94*i))
			im.close()
			i += 1
		im_final.save("final.png")
		file=discord.File("final.png", filename="final.png")
		embedVar.set_image(url="attachment://final.png")
		await context.send(file=file,embed=embedVar)
	else:
		await context.send(embed=embedVar)

	#await context.send(embed=embedVar)
	#await context.send(file=discord.File("final.png", x.name + '.png'))
	newly_dead.clear()
	
# combine and send the thumbnails of every champion involved in an event (horizontal stitch)
async def send_event_image(event_champs, msg, color):
	global endgame
	global context
	if(context is None):
		print("Error, no context yet")
		return
	
	num = len(event_champs)
	im_final = Image.new("RGBA", (90*num + 4*(num-1), 90))
	i = 0
	for x in event_champs:
		im = Image.open(x.thumbnail)
		if(x.status == Status.DEAD):
			im = im.convert('LA')
		im_final.paste(im, (94*i, 0))
		im.close()
		i += 1
	im_final.save("final.png")
	
	embedVar = discord.Embed(title=msg, color=color)
	if(endgame):
		embedVar.set_footer(text='React to support living champions')
	file=discord.File("final.png", filename="final.png")
	embedVar.set_image(url="attachment://final.png")
	await context.send(file=file,embed=embedVar)

	#await send_embed(msg, None, color)
	#await context.send(file=discord.File("final.png", x.name + '.png'))

# generate and send an image of participating champions (2d stitch)
async def send_gallery(mode, *args):
	# modes: 
	# 0: send all
	# 1: send alive
	# 2: send dead
	
	global context
	if(context is None):
		print("Error, no context yet")
		return

	e_title = "If you see this, there was an error"
	champs = []
	des = ""

	if(mode == 0):
		e_title = "Welcome to the Hunger Games!"
		champs = champions.roster
	elif(mode == 1):
		e_title = "Remaining Champions"
		champs = champions.get_list_alive()
	elif(mode == 2):
		e_title = "Passed Champions"
		champs = champions.get_list_dead()
	elif(mode == 3):
		e_title = args[0]
		champs = champions.get_list_alive()
		des = args[1]
	else:
		print("Error")
	
	embedVar = discord.Embed(title=e_title, color=0x00ff00, description=des)

	num = len(champs)
	# i can probably get clever with this and make it so different sized games have different number of ROWS
	ROWS = 6
	final_x = 90*ROWS + 4*(ROWS-1)
	final_y = 94*(int(((num-1) / ROWS))+1)
	im_final = Image.new("RGBA", (final_x, final_y))
	i = 0
	for x in champs:
		im = Image.open(x.thumbnail)
		if(x.status == Status.DEAD):
			im = im.convert('LA')
		x = 94*int(i%ROWS)
		y = 94*int(i/ROWS)
		im_final.paste(im, (x, y))
		im.close()
		i += 1
	im_final.save("final.png")
	file=discord.File("final.png", filename="final.png")
	embedVar.set_image(url="attachment://final.png")
	
	await context.send(file=file,embed=embedVar)

#		SPONSOR FUNCTIONS

def process_reaction(message, user):
	global reactions
	global champions
	msg = message

	print("react!")
	alive = champions.get_list_alive()
	#print(msg)
	names = re.search(r"\"[^\"]*\"", msg)	# v1: 	"\"\w*\""		v2: "\".*\""
	while(names):
		x = names[0]
		print(x)
		for y in alive:
			n = x.strip("\"")
			if y.name == n:
				reactions.add_reaction(y, user)
				break
		msg = msg.replace(x, " ")
		names = re.search(r"\"[^\"]*\"", msg)
	reactions.about()

#		OTHER

# clear globals
def wipe():
	# .clear() or None?
	global champions
	global events
	global newly_dead
	global acting_champions
	global imported

	champions.clear_roster()
	events.clear()

	newly_dead.clear()
	acting_champions.clear()
	imported = False

# return game_over
def check_over():
	global game_over
	return game_over

# append line to current game record
def record(line):
	f = open("record.txt", "a")
	f.write(line)
	f.close()
