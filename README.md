# Discord-Hunger-Games
Discord Bot that runs a mock Hunger Games competition between custom champions.  

Based on the hunger games simulator http://brantsteele.net/hungergames/reaping.php

Traditionally, between 24 and 48 champions are entered into the games.  
An **event** is a notable occurance that consists of 1 or more champions.  
A **round** is a number of events such that every champion has participated.  
Rounds alternate between day and night (and sometimes special events) until one champion remains, who is declared the winner.

When 8 champions are remaining, users can begin supporting champions they want to win by adding discord reactions to events with that champion.  
Sponsorships will slightly decrease the chances that said champions next event is fatal.  

# Files
### badbot.py
Contains most of the discord interface. All user commands are handled in this file, then passed on to hg_bot.  
Users must enter their own discord bot token at the top of this file.  
See user commands below.

### hg_bot.py
Contains the work for the hunger games simulation. 

### cast_in.txt
Contains the list of cast members that will be imported when the games begin.  
Each line must be formatted as follows (tab separated):

#### Name  Link  Gender

**Name** is the nickname for the entry displayed during events.  
**Link** is an imgur link to the picture that will represent the entry.  
**Gender** is a number used to change the events to match the entries gender. FEMALE = 0, MALE = 1, NEUTRAL = 2

### events_in.txt
Contains a list of events that occur between small numbers of entries.  
Some events are fatal, some are not.   

Events are sorted by the period in which they take place:  
**Bloodbath**: Champions entering the game at the start  
**Day**  
**Night**  
**Feast**: Special event on day 5  

Each line must be formatted as follows (tab separated columns):

#### Type	NumChampions	Killers		Killed	Text

**Type** is the period in which this event takes place, as described above  
**NumChampions** is the number of champions that participate in this event  
**Killers** is a comma separated list of champions who kill during this event, or "None"  
**Killed** is a comma separated list of champions who are killed during this event or "None"  
**Text** is the displayed text that describes the event.  

Instead of hardcoding names, "Text" requires champions to be referred to by number like so: (Player1)  
The same is true of pronouns: (they1), (them2), etc.  

Examples:  
Bloodbath&nbsp;&nbsp;&nbsp;2&nbsp;&nbsp;&nbsp;None&nbsp;&nbsp;&nbsp;None&nbsp;&nbsp;&nbsp;(Player1) and (Player2) fight for a bag. (Player1) gives up and retreats.  
Feast&nbsp;&nbsp;&nbsp;2&nbsp;&nbsp;&nbsp;Player2&nbsp;&nbsp;&nbsp;Player1&nbsp;&nbsp;&nbsp;(Player1) is slashed by (Player2) as (they1) was reaching for a weapon. (they1) eventually bleeds out.  
Night&nbsp;&nbsp;&nbsp;1&nbsp;&nbsp;&nbsp;None&nbsp;&nbsp;&nbsp;Player1&nbsp;&nbsp;&nbsp;(Player1) dies from hunger.  
Night&nbsp;&nbsp;&nbsp;2&nbsp;&nbsp;&nbsp;Player1&nbsp;&nbsp;&nbsp;Player2&nbsp;&nbsp;&nbsp;(Player1) sets an explosive off, killing (Player2).  

### External Libraries
discord.py  
Pillow  


# Usage
The following are the commands users will type to order the bot.  
The default command prefix is '$'.

### $start
Performs setup work, including importing from the cast and events files, downloading the champions images, and preping data structures.

### $advance \<n>
Displays n number of events, or 1 event if no argument is provided.     
![Events](https://i.imgur.com/joTBpN8.png "Events")  
If n exceeds the number of events left in the current round, only the events left will be displayed.  

### $run \<n>
Automatically starts a game and runs it to completion. If a numerical argument is specified, that many games will be run.  
Mostly for debugging. 

### $alive
Prints a gallery of champions who are still alive  
![Alive](https://i.imgur.com/7yNsJ2S.png "Alive")  
### $dead
Prints a gallery of champions who have died  
![Dead](https://i.imgur.com/DPiRBVy.png "Dead")  

