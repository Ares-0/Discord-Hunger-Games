# LIBRARIES
from enum import Enum
from enum import IntEnum
import discord
import random
import re
import io
import aiohttp
import os
import json
import math
import configparser
from datetime import datetime as time
from PIL import Image
from pathlib import Path

io_dir = Path(os.path.abspath(__file__)).parent / "../io"

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
	KIMI = 4
	TITANS = 5
	PUBLIC = 6
	
	def __str__(self):
		return self.name
	
	# bloodbath and night (0 and 2) always becomes day
	# feast and special (3+) always become night
	# day can become night, feast, or special
	def next(self):
		next_type = [EventType.Day, EventType.Night, EventType.Day, EventType.Night, EventType.Night, EventType.Night, EventType.Night]
		return next_type[self]

	def title(self, day):
		title = [
			"Bloodbath",
			f"DAY {day}",
			f"NIGHT {day}",
			"Return to the Cornocopia",
			"KIMI NO SEI",
			"On that day",
			"Results Thread"
		]
		return title[self]

	def subtitle(self):
		sub = [
			"As the images stand on their podiums, the horn sounds. Some prepare to hate minorities and women, others get ready to destroy people with FACTS and LOGIC, and some prepare to meme.",
			"",
			"",
			"The cornucopia is replenished with baits, hot takes, shit taste, dank memes, and memoirs from the jurors' families.",
			"KIMI NO SEI KIMI NO SEI KIMI NO SEI KIMI NO SEI KIMI NO SEI KIMI NO SEI KIMI NO SEI",
			"On that day, mankind received a grim reminder. The Colossal Titan appears, shattering the dome and letting loose a horde of Titans.",
			"The public is released upon the arena, furious about their favorite shows being snubbed."
		]
		return sub[self]

#		CLASSES

# List of all participating champions
class Champions:
	"""I kind of want this to just be a list of the champions
	and any functions that go along with managing that list.
	External factors like where the champs are loaded from and how
	can remain with the Game object"""
	roster = []
	
	def __len__(self):
		return len(self.roster)

	def reset(self):
		for champ in self.roster:
			champ.set_status(Status.ALIVE)

	def clear_roster(self):
		self.roster.clear()
	
	def add_champion(self, new_champ):
		self.roster.append(new_champ)
	
	def clear(self):
		self.roster.clear()
	
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

		# NOTE discord.py does NOT like the l, t, m, etc extensions on imgur. s seems ok?
		self.image_link = str(image + "b.png")		# b.png
		#self.image_link = str(image + ".gifv")
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
	events_structure = [[[] for j in range(len(EventType))] for i in range(2)]
	# structure of all events in game
	# events_structure[Is_Fatal][EventType][events] is list of events matching appropriate Is_Fatal and EventType

	def about(self):
		# this is a bad name for this function
		print("\nHarmless")
		for t in EventType:
			print('# of ' + t.name + ' Events: ' + str(len(self.events_structure[0][t])))

		print("\nFatal")
		for t in EventType:
			print('# of ' + t.name + ' Events: ' + str(len(self.events_structure[1][t])))
		print()
	
	def get_type_list(self, type, fatal):
		return self.events_structure[fatal][type]
	
	def get_random_event(self, max_champs, type, fatal, kill_limit):
		type_events = self.get_type_list(type, fatal)
		possible_events = []
		for x in type_events:
			if(x.numChampions <= max_champs):
				if(x.get_count_killed() <= kill_limit):
					possible_events.append(x)
		if(len(possible_events) == 0):
			print("error, no possible events")
		return random.choice(possible_events)
	
	def add_event(self, new_event):
		self.events_structure[new_event.fatal][new_event.type].append(new_event)
	
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
		self.fatal = len(self.killed) > 0

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
		if(self.numChampions != len(players)):
			print("ERROR length mismatch")
		
		out = self.raw_text

		# replace stuff like (Player1), (pro2), etc
		m = re.search(r"(\([\w\/]*\d\))", out)				# \([\w\/]*\d\)
		count = 0
		while(m):
			reg = m[0]

			char_num = int(reg[-2])
			type = reg[1:-2]
			
			# his / her / their
			# his / hers/ theirs
			# he / she / they
			# him / her / them
			# himself / herself / themselves
			
			replace = "ERROR GR01"						# this still pops up EXTREMELY rarely. Like actually 1 in 10k
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
			elif(type == "theirs"):
				options = ["hers", "his", "theirs"]
				replace = options[g]
			elif(type == "themselves"):
				options = ["herself", "himself", "themselves"]
				replace = options[g]
			
			out = out.replace(reg, replace)
			m = re.search(r'(\([\w\/]*\d\))', out)
					
			
			# infinite loop catch
			count += 1
			if(count >= 10):
				print("error, infinite loop in regex")
				break
		return out
	
	def get_count_killed(self):
		return len(self.killed)

# Collection of statistics
class Stats:
	elapsed_turns = 0
	elapsed_events = 0

	def increment_turn(self):
		self.elapsed_turns += 1

	def increment_event(self):
		self.elapsed_events += 1

	def about(self):
		print("Elapsed Turns: " + str(self.elapsed_turns))
		print("Elapsed Events: " + str(self.elapsed_events))
		
		# I need to rethink this data collecting
		# print("Fatal Chance: " + str(params.get_fatal_chance())) # useless metric now

		# with open(io_dir / "stats.csv", 'a') as f:
		# 	line = "{0}, {1}, {2}, {3}\n".format(champions.num, self.elapsed_turns, self.elapsed_events, params.get_fatal_chance())
		# 	f.write(line)
		pass

	def clear(self):
		self.elapsed_events = 0
		self.elapsed_turns = 0

# Collection of Reaction data structures
class Reactions:
	champions = []
	users = []
	reactions = [[0 for i in range(20)] for j in range(8)]
	totals = []
	limit = 2

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
		if(count < self.limit):
			self.reactions[idx_c][idx_u] = self.reactions[idx_c][idx_u] + 1
		return sum(self.reactions[idx_c])	# return the total number of support

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

	def get_fatal_chance(self, champ, base_chance):
		SPONSOR_WEIGHT = 0.2	# 0.35 chosen by survey
		print(champ.name)

		# two aspects to this
		# (1) FATAL_CHANCE
		# (2) Support

		# 0% support keeps FATAL_CHANCE
		# 100% support reduces fatal chance to 0
		# this is before taking into account sponsor weight

		# how strong the sponsorship is. 1 is maximum (full aid), 0 is minimum (no aid)
		sponsor = 0		# initial value
		c = self.get_champ_idx(champ)
		if(sum(self.totals) != 0):
			sponsor = self.totals[c] / self.limit*len(self.users)	# sponsorships given / sponsorships possible (aka users*limit)
			sponsor = max(0, min(1, sponsor))		# keep sponsor in bounds plz
		
		last = base_chance * (1-sponsor*SPONSOR_WEIGHT)

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
	def __init__(self):
		self.fatal_chance = 0.3
		self.FeastDay = 3			# day of the feast event, and start of the rise in death rate
		self.SPONSORSHIP = True		# is sponsorship turned on?
		self.VERBOSE = True			# if true, send messages to discord. If false, just print to logs
		self.EVENTS_IN = ""			# input file for events
		self.load_ini()

	def load_ini(self):
		config = configparser.ConfigParser()
		config.read(io_dir / 'HG.ini')
		self.FeastDay = int(config['Settings']['FeastDay'])
		self.SPONSORSHIP = config['Settings'].getboolean('SPONSORSHIP')
		self.VERBOSE = config['Settings'].getboolean('VERBOSE')
		self.EVENTS_IN = config['Settings']['EVENTS_IN']

	def get_fatal_chance(self):
		return self.fatal_chance
	
	def update_fatal_chance(self, chance):
		self.fatal_chance = chance

# An instance of a single game
class Game:
	def __init__(self, context):
		self.context = context

		self.imported = False # likely able to remove

		self.champions = Champions()
		self.events = Events()
		self.stats = Stats()
		self.reactions = Reactions()
		self.params = Params()

		self.params.load_ini()
		print("setting up new game")
		self.import_champions()
		self.import_events()
		self.start = time.now()

	def reset(self):
		"""
		Set settings to default
		Do not delete existing events or champions or settings
		"""
		print("resetting")
		self.game_over = False
		self.endgame = False
		self.current_day = 0
		self.current_event = 0
		self.current_type = EventType.Bloodbath
		self.newly_dead = []
		self.acting_champions = []

		self.stats.clear()
		# probably reactions too, will cover later
		self.champions.reset()

	# PREP FUNCTIONS
	async def prep_game(self):
		self.reset()
		await self.download_images(self.champions.roster)
		await self.send_gallery("all")

	def import_champions(self):
		imported = 0
		self.champions.clear()

		f = open(io_dir / "cast_in.txt", "r")
		
		print("Importing champions...")
		line = f.readline()	# eat first line
		line = f.readline() # get #entries value				# TODO Throw error if this seems wrong
		entries = int(line[:-1])
		line = f.readline()
		#print(line)
		while(len(line) > 1):
			print(line, end="")
			# ignore lines that start with "~". For dev sanity
			if(line.startswith('~')):
				line = f.readline()
				continue

			# Parse line
			x = self.check_champion_line(line.strip())
			if x is None:
				print(f"Skipping erroneous line: \"{line.strip()}\"")
				line = f.readline()
				continue

			# Add new champ
			new_champ = Champion(x["name"], x["link"], Gender(x["gender"]), Status(0))
			self.champions.add_champion(new_champ)
			imported += 1

			# prep next iteration
			if(imported >= entries):
				break
			line = f.readline()

		f.close()

	def check_champion_line(self, line: str):
		"""Parse and error check a single line in a champion file"""

		x = line.split("\t")
		while("" in x): 
			x.remove("")
		
		if len(x) != 3:
			return None

		# if the .png is there, remove it. Later operations require it to not be there
		link = x[1]
		if(x[1][-4:] == ".png"):
			link = link[:-4]
		
		try:
			g = int(x[2])
		except ValueError:
			return None

		return {
			"name": x[0].strip(),
			"link": x[1],
			"gender": g
		}

	def check_list_of_champions(self, filename: str = "cast_in.txt"):
		f = open(io_dir / filename, "r")
		error_count = 0
		error_str = ""

		# Ignore first line
		try:
			line = f.readline()
		except UnicodeDecodeError:
			return -1, "Unicode error in input file"

		# Check num line
		line = f.readline()
		try:
			int(line)
		except ValueError:
			error_count += 1
			str = f"Error: second line should contain number of entries. Instead: \"{line.strip()}\""
			print(str)
			error_str += ("\n" + str)

		# Check champion lines
		line = f.readline()
		while(len(line) > 1):
			# comment lines are fine
			if(line.startswith('~')):
				line = f.readline()
				continue
			
			x = self.check_champion_line(line.strip())
			if x is None:
				error_count += 1
				str = f"Error: champion line format incorrect. Line: \"{line.strip()}\""
				print(str)
				error_str += (f"\n\"{line.strip()}\"")
			
			line = f.readline()

		# return result
		print(f"Errors on {-1*error_count} lines")
		return -1*error_count, error_str

	def import_events(self):
		# I dont want to totally kill this structure
		# But I cant explain why
		if "json" in self.params.EVENTS_IN:
			self.import_json_of_events()
		else:
			pass
		self.events.about()

	def import_json_of_events(self):
		imported = 0
		events_in = {}
		# use this for occasional unit testing
		dummy_champs = []
		for x in range(10):
			dummy_champs.append(Champion(f"Champ{x}", "", Gender(0), Status(0)))

		print("Importing events from .json...")
		with open(io_dir / "events.json", "r") as f:
			try:
				events_in = json.load(f)
			except Exception as e:
				print(f"error reading file: {e}")
				return

		for type_str in events_in.keys():		# Day, night, etc
			for result in events_in[type_str].keys():		# fatal, nonfatal
				for numChampions in events_in[type_str][result]:	# 1, 2, 3 etc
					for e in events_in[type_str][result][numChampions]:
						# get proper EventType from string
						type = EventType.Day
						for t in EventType:
							if(type_str in t.name):
								type = t
								break
						new_event: Event = Event(type, int(numChampions), e["Killers"], e["Killed"], e["Text"])
						# print(new_event.get_final_text(dummy_champs)) # use this to check how events come out
						self.events.add_event(new_event)
						imported += 1
		print(f"Imported {imported} events")

	async def download_images(self, champs_list):
		print("Downloading images...")
		async with aiohttp.ClientSession() as session:
			count = 0
			for x in champs_list:
				# to do: get image from imgur or local from computer?
				print(x.name)
				async with session.get(x.image_link) as resp:
					if resp.status != 200:
						return await self.context.send('Could not download file...')
					data = io.BytesIO(await resp.read())
					x.set_thumbnail(data)
					count += 1
			print(f"Downloaded {count} images")

	# PROGRESS FUNCTIONS
	async def advance_n(self, n):
		"""advance by N events, showing turn starts and ends if need be"""
		if(self.game_over):
			return

		# add check to make sure the game has been initialized (imported stuff etc)
		# CANT EVEN SEND A MESSAGE TO YELL AT USER UNTIL THEY DO $START LMAO
		if len(self.champions) < 1:
			await self.send_embed("Error, no champions", "", "", 0xff0000)
			return

		# If start of turn, do some setup
		if self.current_event == 0:			# maybe move to another function

			self.stats.increment_turn()
			self.acting_champions = self.champions.get_list_alive()
			random.shuffle(self.acting_champions)
			self.reactions.update_count()

			# In final 8, start accepting emotes as sponsorship
			if(self.params.SPONSORSHIP and not self.endgame and len(self.acting_champions) <= 8):
				# print message
				self.endgame = True
				print("final 8")
				self.record("\nfinal 8")
				await self.send_gallery("other", "Final {0}".format(len(self.acting_champions)), "From now on, react to events to offer your sponsorship to these champions.")
				self.reactions.fill_champions(self.acting_champions)
				return		# prompt for another 'advance n'

			if(self.endgame):
				self.reactions.about()

			# decide round type

			# special cases
			# first type is bloodbath
			if(self.current_day == 0):
				self.current_type = EventType.Bloodbath
			# feast on feastday
			elif (self.current_type is EventType.Day and self.current_day is self.params.FeastDay):
				self.current_type = EventType.Feast
			# possibly select a special round
			elif (self.current_type is EventType.Day):
				# first, if there will be a special round
				if(random.random() < 0.85):
					self.current_type = EventType.Night
				# then what special round it is
				else:
					# get list of special rounds
					arena = []
					for t in EventType:
						if(t > EventType.Feast):
							arena.append(t)
					self.current_type = arena[int(random.random()*len(arena))]	# select from list
			else:
				# normal next cases
				self.current_type = self.current_type.next()

			text = self.current_type.title(self.current_day)
			subtitle = self.current_type.subtitle()
			print(text)
			left = self.champions.get_count_alive()
			self.record("\n" + text + "  " + str(left) + " alive\n")

			# depends on if I want this after ~ready or ~advance
			#if(self.current_type is EventType.Bloodbath):
			#	await send_gallery(0)

			if(self.params.VERBOSE):
				await self.send_embed(text, subtitle, "", 0x0000ff)

			self.params.update_fatal_chance(self.get_fatal_chance())

			# maybe always have new turn be its own prompt
			self.current_event += 1
			return

		# advance up to as many turns as the user requested
		advanced = 0
		while(len(self.acting_champions) > 0 and advanced < n):
			# make sure that the last event on the last remaining champion is not fatal
			await self.run_event(self.acting_champions, self.current_type)
			advanced += 1
			self.current_event += 1

		print("done advancing")
		# check if game is over
		await self.check_for_winner()

		# if this turn is over, set up next turn
		if(len(self.acting_champions) == 0 and self.game_over is False):	
			self.current_event = 0

			# possibly move this to just night / bloodbath
			text = str(self.current_type) + " Over"
			print(text)
			if(self.params.VERBOSE):
				await self.send_embed(text, "", "", 0x0000ff)

			# announce dead at end of night and at end of bloodbath. Also, increment day
			if(self.current_type is EventType.Night or self.current_type is EventType.Bloodbath):
				self.current_day += 1
				await self.send_newly_dead()

	async def run_event(self, acting_list, type):
		"""setup and run a single event featuring 1 or more champions"""
		self.stats.increment_event()	
		
		# Get fatal chance of this event
		num_alive = self.champions.get_count_alive()
		
		base_chance = self.params.get_fatal_chance()
		if(self.params.SPONSORSHIP and num_alive <= 8): # TODO: parameterize this
			chance = self.reactions.get_fatal_chance(acting_list[-1], base_chance)
		else:
			chance = base_chance
		fatal = random.random() < chance

		# Actors in event must not exceed #champs left
		champions_remaining = len(acting_list)
		if(num_alive <= 1):
			fatal = False

		# Diers in event must not equal #champs left
		kill_limit = champions_remaining
		if(num_alive == champions_remaining):
			kill_limit -= 1

		# select an event from the appropriate list
		this_event = self.events.get_random_event(champions_remaining, type, fatal, kill_limit)

		# pull champions
		event_champs = []
		for x in range(0, this_event.numChampions):
			event_champs.append(acting_list.pop())

		# mark 'killed' as dead (has to happen before display for ease)
		for x in this_event.killed:
			dead = event_champs[int(x[6:])-1] # get N from "PlayerN"
			dead.set_status_dead()
			self.newly_dead.append(dead)

		# display event
		await self.print_event(this_event, event_champs)

	# STATUS FUNCTIONS
	def get_fatal_chance(self):
		# always calculating the chance based on those alive is handy
		x = self.champions.get_count_alive()
		
		# y(x) = 0.1*log2(x/10+1)+0.2
		#self.fatal_chance = 0.1*math.log2(x/10+1)+0.2

		# y(x) = x/b + c # b lower, fatal chance higher
		# y(x) = x/200 + 0.2
		fatal_chance = x/250 + 0.15

		# add day / night bias
		bias = 0.04 #* random.random()
		if(self.current_type is EventType.Day):
			fatal_chance += bias
		if(self.current_type is EventType.Night):
			fatal_chance -= bias
		
		# apply floor to value
		fatal_chance = max(0.25, fatal_chance)

		# increase as rounds continue past the feast
		if(self.current_day > self.params.FeastDay):
			fatal_chance += 0.04*(self.stats.elapsed_turns - self.params.FeastDay*2+1)
		
		# forget all that actually if it's a special round
		if(self.current_type > EventType.Feast):
			fatal_chance = 0.45

		print(fatal_chance)
		return fatal_chance

	async def check_for_winner(self):
		"""Check if one champion is left, and announce if so"""
		alive = self.champions.get_list_alive()
		if(len(alive) > 1):
			return False
		else:
			self.game_over = True
			if(len(alive) < 1):
				print("Error, no one survived")
				await self.context.send("No winners, {0}".format(self.context.author.mention))
				return True
			winner = alive[0]
			text = "The winner is: " + winner.name
			print(text)
			
			line = str(self.params.get_fatal_chance()) + "    " + text + "\n"
			self.record(line)
			
			link = winner.image_link
			link = link[:-5] + link[-4:] # chop out the 'b' modifier to get full image
			print(link)
			await self.send_embed(text, "", link, 0x0000ff)		# image is compressed as shit but it's fine
			if(os.path.exists("final.png")): # move to cleanup function?
				os.remove("final.png")
			
			# prep stats and stuff
			self.stats.about()
			return True
	
	def check_over(self):
		return self.game_over

	# MESSAGE FUNCTIONS
	async def print_event(self, event: Event, event_champs):
		msg = event.get_final_text(event_champs) + "\n"
		print(msg)
		color = 0x00ff00
		if(len(event.killed) > 0):
			color = 0xff0000

		# this seems like a lot of repeat code
		base_chance = self.params.get_fatal_chance()
		line = f"{base_chance:.3f}"
		if(self.params.SPONSORSHIP and self.endgame):
			adjusted_chance = self.reactions.get_fatal_chance(event_champs[0], base_chance)
			line = line + f" ({adjusted_chance:.3f}) "
		line = line + "    " + msg
		self.record(line)

		if(self.params.VERBOSE):
			await self.send_event_image(event_champs, msg, color)

	async def send_embed(self, title, subtitle, image_url, rgb):
		"""create and send a simple embed"""
		if(self.context is None):
			print("No context yet")
			return

		if(rgb is None):
			e_color = 0x00ff00
		else:
			e_color = rgb
		embedVar = discord.Embed(title=title, color=e_color, description=subtitle)

		if(image_url is not None):
			#embedVar.set_image(url='https://i.imgur.com/wSTFkRM.png')
			embedVar.set_image(url=image_url)
		
		await self.context.send(embed=embedVar)

	async def send_newly_dead(self):
		"""send newly dead embed"""
		if(self.context is None):
			print("Error, no context yet")
			return
		
		num = len(self.newly_dead)
		e_title = f"{num} pictures have been removed due to violating r/anime's rules"			# TODO: we can have a few of these
		print(e_title)
		self.record(e_title + "\n")
		embedVar = discord.Embed(title=e_title, color=0x0000ff)
		if(num > 0):
			embedVar.set_footer(text='Press \'f\' to pay respects')

		if(num > 0):
			im = Image.open(self.newly_dead[0].thumbnail)
			thumb_x, thumb_y = im.size[0], im.size[1]
			COLS = 4

			COLS = min(COLS, num)	# if less have died than there are columns, don't need the extras
			final_x = thumb_x*COLS + 4*(COLS-1)
			final_y = (thumb_y+4)*(int(((num-1) / COLS))+1)
			im_final = Image.new("RGBA", (final_x, final_y))
			i = 0
			for x in self.newly_dead:
				im = Image.open(x.thumbnail)
				im = im.convert('LA')
				x = (thumb_x+4)*int(i%COLS)
				y = (thumb_y+4)*int(i/COLS)
				im_final.paste(im, (x, y))
				im.close()
				i += 1
			im_final.save("final.png")
			file=discord.File("final.png", filename="final.png")
			embedVar.set_image(url="attachment://final.png")
			if(self.params.VERBOSE):
				await self.context.send(file=file,embed=embedVar)
		else:
			if(self.params.VERBOSE):
				await self.context.send(embed=embedVar)

		self.newly_dead.clear()

	async def send_event_image(self, event_champs, msg, color):
		"""combine and send the thumbnails of every champion involved in an event
		(horizontal stitch)"""
		if(self.context is None):
			print("Error, no context yet")
			return
		
		im = Image.open(event_champs[0].thumbnail)
		x, y = im.size[0], im.size[1]
		num = len(event_champs)
		im_final = Image.new("RGBA", (x*num + 4*(num-1), y))
		i = 0
		for c in event_champs:
			im = Image.open(c.thumbnail)
			if(c.status == Status.DEAD):
				im = im.convert('LA')
			im_final.paste(im, ((x+4)*i, 0))
			im.close()
			i += 1
		im_final.save("final.png")
		
		embedVar = discord.Embed(title=msg[-256:], color=color)
		if(self.endgame):
			embedVar.set_footer(text='React to support living champions')
		file=discord.File("final.png", filename="final.png")
		embedVar.set_image(url="attachment://final.png")
		await self.context.send(file=file,embed=embedVar)

	async def send_gallery(self, mode, *args):
		if(self.context is None):
			print("Error, no context yet") # raise exception
			return

		# no point continuing if we're not even sending the message
		if(not self.params.VERBOSE):
			return

		# Defaults
		e_title = "If you see this, there was an error"
		champs = []
		des = ""

		# Grab the appropriate champions
		if(mode == "all"):
			e_title = "Welcome to the Hunger Games!"
			champs = self.champions.roster
			des = f"{len(champs)} Entries!"
		elif(mode == "alive"):
			e_title = "Remaining Champions"
			champs = self.champions.get_list_alive()
		elif(mode == "dead"):
			e_title = "Passed Champions"
			champs = self.champions.get_list_dead()
		elif(mode == "other"):
			e_title = args[0]
			champs = self.champions.get_list_alive()
			des = args[1]
		else:
			print("Error") # raise exception
		
		embedVar = discord.Embed(title=e_title, color=0x00ff00, description=des)

		num = len(champs)
		# i can probably get clever with this and make it so different sized games have different number of COLS
		COLS = 6
		im = Image.open(champs[0].thumbnail) # TODO: breaks if list len == 0
		thumb_x, thumb_y = im.size[0], im.size[1]

		COLS = min(COLS, num)	# if less have died than there are columns, don't need the extras
		final_x = thumb_x*COLS + 4*(COLS-1)
		final_y = (thumb_y+4)*(int(((num-1) / COLS))+1)
		im_final = Image.new("RGBA", (final_x, final_y))
		i = 0
		for x in champs:
			im = Image.open(x.thumbnail)
			if(x.status == Status.DEAD):
				im = im.convert('LA')
			x = (thumb_x+4)*int(i%COLS)
			y = (thumb_y+4)*int(i/COLS)
			im_final.paste(im, (x, y))
			im.close()
			i += 1
		im_final.save("final.png")
		file=discord.File("final.png", filename="final.png")
		embedVar.set_image(url="attachment://final.png")
		
		#if(VERBOSE): # multilevel verbosity
		await self.context.send(file=file,embed=embedVar)

	def record(self, line):
		"""append line to current game record"""
		with open(io_dir / "record.txt", 'a') as f:
			f.write(line)

	# REACTIONS
	def process_reaction(self, message_title, user):
		if(not self.params.SPONSORSHIP):		# not sponsoring, move on
			return -1
		if(not self.endgame):			# if not in final 8, move on
			return -1

		msg = message_title
		out = 0
		alive = self.champions.get_list_alive()
		print("react!")

		names = re.search(r"\"[^\"]*\"", msg)	# v1: 	"\"\w*\""		v2: "\".*\""
		while(names):
			x = names[0]
			print(x)
			for y in alive:
				n = x.strip("\"")
				if y.name == n:
					out = self.reactions.add_reaction(y, user)
					break
			msg = msg.replace(x, " ")
			names = re.search(r"\"[^\"]*\"", msg)
		self.reactions.about()
		return out		# return amount of support on msg
