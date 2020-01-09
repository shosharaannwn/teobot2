#!/usr/bin/python3

import os
import sys
import argparse
import traceback
import time
import datetime
import re
import asyncio
import json
import pickle
import getpass
import importlib
from collections import defaultdict

import discord
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import aioschedule as schedule

################

parser = argparse.ArgumentParser()
parser.add_argument("--logfile", "-l")
parser.add_argument("--flow", action='store_true', help="just do OAuth flow and then exit")
parser.add_argument("--test", action="store_false", help="Write on test server with test channels")
parser.add_argument("--config", "-c", required=True)

args = parser.parse_args()

if args.logfile:
    logfile = open(args.logfile, 'a')
    sys.stdout = logfile
    sys.stderr = logfile
    sys.stdin  = open(os.devnull, 'r')

config_mod = importlib.import_module(re.sub(r'.py$', '', args.config))

faq_sheet = config_mod.faq_sheet
faq_imp = config_mod.faq_imp
faq_rep = config_mod.faq_rep
faq_topic = config_mod.faq_topic

bot_token = config_mod.bot_token  # discord bot token
google_sheet = config_mod.google_sheet # google sheet file id
json_creds_file = config_mod.json_creds_file # google app api token
token_path = config_mod.token_path  # google OAuth user access token 

log_channel_guild_name = getattr(config_mod, 'log_channel_guild_name', None)
log_channel_name = getattr(config_mod, 'log_channel_name', None) # Discord channel for error messages
help_channel_name = getattr(config_mod, 'help_channel_name', None)

guild_name = config_mod.guild_name # Guild name (Discord server)
msg_channel_name = config_mod.msg_channel_name 

################


# Acceptable days

day_abbrevs = {
    'm'  : 'monday',
    't'  : 'tuesday',
    'w'  : 'wednesday',
    'th' : 'thursday',
    'f'  : 'friday',
    's'  : 'saturday',
    'su' : 'sunday',
    'monday' : 'monday',
    'tuesday' : 'tuesday',
    'wednesday' : 'wednesday',
    'thursday' : 'thursday',
    'friday' : 'friday',
    'saturday' : 'saturday',
    'sunday' : 'sunday',
    'mon' : 'monday',
    'tues' : 'tuesday',
    'tue' : 'tuesday',    
    'wed' : 'wednesday',
    'thurs' : 'thursday',
    'thur' : 'thursday',
    'thu' : 'thursday',        
    'fri' : 'friday',
    'sat' : 'saturday',
    'sun' : 'sunday',
    'skip' : 'skip',
}

day_names =  [
    'monday',
    'tuesday',
    'wednesday',
    'thursday',
    'friday',
    'saturday',
    'sunday',
]


# Global state variables
google_scopes=['https://www.googleapis.com/auth/drive.metadata.readonly',
               'https://www.googleapis.com/auth/spreadsheets.readonly']
               



class FlowEOF(Exception):
    pass

class FlowNotAllowed(Exception):
    pass

class SheetReader:

    def __init__ (self, sheet, range):
        self.sheet=sheet
        self.range=range
        self.last_mtime=None
    
    # Reads a google sheet and sets the scheduler accordingly
    def read_sheet(self, allow_flow=False, use_mtime=True, update_mtime=None):
        if update_mtime is None:
            update_mtime = use_mtime
        creds = None
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
            if not os.access(token_path, os.W_OK):
                raise Exception(f"I don't have access to write file {token_path}")
        else:
            dirname = os.path.dirname(token_path)
            if dirname == '':
                dirname = '.'
            if not os.access(dirname, os.W_OK):
                raise Exception(f"I don't have access to create file at {token_path}")
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("refreshing creds")
                creds.refresh(Request())
            else:
                if not allow_flow:
                    raise FlowNotAllowed("credentials are invalid, restart the bot and go through the OAuth flow again")
                print("doing OAuth flow")
                flow = InstalledAppFlow.from_client_secrets_file(json_creds_file, google_scopes)
                try:
                    creds=flow.run_console()                
                except EOFError as e:
                    raise FlowEOF("EOFError while doing OAuth flow.  You need to do this part interactively.\n"
                                  f"try: docker-compose exec teobot /teo_bot2.py --config {args.config} --flow") from e
            with open(token_path, 'wb') as token:
                pickle.dump(creds,token)
        
        google_sheets = build('sheets', 'v4', credentials=creds)
        google_drive = build('drive', 'v3', credentials=creds)

        mtime = google_drive.files().get(fileId=self.sheet, fields="modifiedTime").execute()['modifiedTime']
        print(f'Read the sheet, mtime = {mtime}')

        if use_mtime:
            if self.last_mtime == mtime:
                print(f'Modification time did not change')
                return None # Don't need to read the sheet and update the scheduler

        if update_mtime:
            self.last_mtime=mtime
            print(f'Set new sheet modification time as {mtime}')

        result = google_sheets.spreadsheets().values().get(spreadsheetId=self.sheet,range=self.range).execute()
        lines = result.get('values', [])
        return lines

faq_reader=SheetReader(faq_sheet, "A2:G")
announcement_reader=SheetReader(google_sheet, "A2:C")

class ScheduleParseError(Exception):
    pass

def normalize_day(day):
    day = day.lower()
    try:
        return day_abbrevs[day]
    except KeyError:
        raise ScheduleParseError(f"Day String invalid")
    

# Discord Bot class
class Bot:

    async def read_faq(self, user_initiated=False):
        table=defaultdict(list)
        if user_initiated:
            lines = faq_reader.read_sheet(use_mtime=False, update_mtime=True)
        else:
            lines = faq_reader.read_sheet()
        if lines is None:
            if user_initiated:
                await self.send_log("FAQ sheet is unchanged")
            return # Nothing to do, no need to update scheduler.
        for i,line in enumerate(lines):
            if len(line) < 7:
                continue # This is expected in the sheet. Incorrectly formatted lines are simply ignored.
            topic_str=line[faq_topic].strip()
            topics=re.split(r",|;", line[faq_topic])
            if len(topics) < 1:
                continue # Skipping blank lines
            text=""
            if not (line[faq_imp].strip()==""):
                text=f"**[Repupblic]** {line[faq_rep]} \n**[Imperial]** {line[faq_imp]}"
            else:
                text=line[faq_rep]
            for t in topics:
                print(f"Adding text {text} to topic {t}")
                table[t.strip().lower()].append(text)
        self.faq_table=table
        
                    
    async def read_schedule(self, user_initiated=False):
        if user_initiated:
            lines = announcement_reader.read_sheet(use_mtime=False, update_mtime=True)
        else:
            lines = announcement_reader.read_sheet()
        if lines is None:
            if user_initiated:
                await self.send_log("Announcement sheet is unchanged")
            return # Nothing to do, no need to update scheduler.
        schedule.clear() # Clear scheduler

        for i,line in enumerate(lines):
            try:
                print(f"Line: {i+2}  {line}")
                if len(line) < 3:
                    raise ScheduleParseError(f"Row does not have enough columns")
                message, days, times = line[:3]
                days=re.sub("\s","", days)
                if days.lower() == 'skip':
                    continue;
                if days.lower() == 'daily':
                    days = set(day_names)
                else:
                    days = set(map(normalize_day, days.strip().split(',')))
                times=re.sub("\s","",times)
                if (re.match("hourly", times, re.IGNORECASE)):
                    times = [f'{h}:00' for h in range(24)]
                else:
                    times = times.split(",")
                for time in times:
                    m = re.match(r'(\d+):(\d+)$', time)
                    if not m:
                        raise ScheduleParseError(f"Time is invalid")
                    hours,minutes = map(int, m.groups())
                    if hours > 23 or minutes > 59:
                        raise ScheduleParseError(f"Time is invalid")
                for day in days:
                    for time in times:
                        print(f"Scheduled message {message} for {day} at {time}")
                        getattr(schedule.every(), day).at(time).do(self.print_message, message)
            except ScheduleParseError as e:
                message = f'Eternal Bot Scheduling Error: Row {i+2}: {e.args[0]}'
                #traceback.print_exc()
                print(message)
                await self.send_log(message)

        await self.send_log("Schedule updated.")

    async def find_guild(self, name):
        await self.client.wait_until_ready()
        for guild in self.client.guilds:
            if guild.name==name:
                print("found guild!", guild)
                return guild
        else:
            sys.stdout.write("Invalid guild name "+name+"\n")
            sys.exit(1)

    async def send(self, message):
        print ("Sending Message:", message)
        channel=await self.msg_channel
        await channel.send(message)

    async def send_log(self, message):
        print ("Sending Log Message:", message)
        if self.log_channel is None:
            return
        channel=await self.log_channel
        await channel.send(message)
        
    async def send_faq(self, message):
        print ("Sending FAQ Message:", message)
        if self.help_channel is None:
            return
        channel=await self.help_channel
        await channel.send(message)

    # Prints message "message" using Bot bot
    async def print_message(self, message):
        now=datetime.datetime.now()
        message=re.sub("\{\$TIME\}", now.strftime("%I:%M %p %Z"), message)
        message=re.sub("\{\$DATE\}", now.strftime("%A %B %d, %Y"), message)
        await self.send(message)


    async def find_channel(self, guild_future, name):
        guild = await guild_future
        for channel in guild.channels:
            if channel.name == name:
                print("found channel!", name, channel)
                return channel
        else:
            print("didn't find channel!", name)
            return None

    async def start(self):

        self.guild = asyncio.ensure_future(self.find_guild(guild_name))
        self.msg_channel = asyncio.ensure_future(self.find_channel(self.guild, msg_channel_name))
        
        if help_channel_name is not None:
            self.help_channel = asyncio.ensure_future(self.find_channel(self.guild, help_channel_name))
        
        if log_channel_name is not None:
            if log_channel_guild_name is None:
                self.log_guild = self.guild
            else:
                self.log_guild = asyncio.ensure_future(self.find_guild(log_channel_guild_name))
            self.log_channel = asyncio.ensure_future(self.find_channel(self.log_guild, log_channel_name))
        else:
            self.log_channel=None

        @self.client.event
        async def on_message(message):
            if self.log_channel is None:
                return
            if message.author == self.client.user:
                return
            log_channel = await self.log_channel
            help_channel = await self.help_channel
            if (message.channel == help_channel and self.client.user in message.mentions):
                print(f"got a message! {message.content}")
                try:
                    content = re.sub(r'\<\@\d+\>', '', message.content)
                    content = content.strip()
                    content = content.lower()
                    print(f"what the fuck {content}")
                    if content in self.faq_table:
                        print (f"message is a valid topic!")
                        start=0
                        for message in self.faq_table[content]:
                            if start != 0:
                                await self.send_faq("-----------------------------------\n")
                            start=start+1
                            await self.send_faq(f"{message}\n")
                    else:
                        topics=", ".join(self.faq_table.keys())
                        print (f"... message isn't a valid topic")
                        await self.send_faq(f"Hi, I'm The Eternal Bot! You're asking for something outside of my expertise!! Or you're just saying hi!\n\nHere are the topics I can respond to!\n\n**[Available Topics]**: {topics}")
                except:
                    print(f":(")
                    print(traceback.format_exc())
            if not (message.channel == log_channel and self.client.user in message.mentions): 
                return
            print("got command:", repr(message.content))
            content = re.sub(r'\<\@\d+\>', '', message.content)

            if content.lower().strip()=="update":
                print("updating schedule.")
                self.last_update = datetime.datetime.now()
                await self.read_schedule(user_initiated=True)
                await self.read_faq(user_initiated=True)

            elif content.lower().strip()=="dance":
                dance = ["We can dance if we want to",
                         "We can leave your friends behind",
                         "Cause your friends don't dance and if they don't dance",
                         "Well they're are no friends of mine",
                         "I say, we can go where we want to...",
                         "to a place where they will never find",
                         "And we can act like we come from out of this world",
                         "Leave the real one far behind,",
                         "And we can dance"]
                for lyric in dance:
                    await self.send_log("🎶" + lyric + "🎶")
                    await asyncio.sleep(2)

            elif content.lower().strip()=="sheet":

                await self.send_log(f"https://docs.google.com/spreadsheets/d/{google_sheet}")

            elif content.lower().strip()=="status":

                jobs = iter(sorted(schedule.default_scheduler.jobs, key=lambda job: job.next_run))
                next_job = next(jobs, None)
                await self.send_log(f"Next announcement is at {next_job.next_run}\n" +
                                    f"Text is: {next_job.job_func.args[0]}")


            elif 'help' in content.lower() or '?' in content:
                await self.send_log(f"I'm {self.client.user.name}!  I read messages from a google sheet and announce them at the scheduled times.\n" +
                                    f'Say "<@{self.client.user.id}> help" to see this message\n' +
                                    f'Say "<@{self.client.user.id}> status" to see current bot status\n' +
                                    f'Say "<@{self.client.user.id}> sheet" to get a link to the google sheet\n' +
                                    f'Say "<@{self.client.user.id}> update" and I will read it again\n')
            else:
                await self.send_log(f"Sorry, I don't understand that.  Say \"<@{self.client.user.id}> help\" for instructions.")


        await self.client.start(bot_token)

    # check for updates every four hours
    async def run_schedule(self):
        while True:
            await schedule.run_pending()
            now=datetime.datetime.now()
            if ((self.last_update is None) or ((now - self.last_update) > datetime.timedelta(hours=1))):
                self.last_update = now
                print(f"Updating sheet at {now}\n")
                await self.read_schedule()
                await self.read_faq()
            await asyncio.sleep(1)    

    def __init__(self):
        self.client = discord.Client()
        self.last_update = None

async def flusher():
    while True:
        sys.stdout.flush()
        await asyncio.sleep(1)

def main():
    #print("running as uid", os.getuid(), "i.e.", getpass.getuser())
    
    if args.flow:
        announcement_reader.read_sheet(allow_flow=True, use_mtime=False)
        sys.exit(0)

    try:
        announcement_reader.read_sheet(allow_flow=True, use_mtime=False)
        sys.stdout.flush()
    except FlowEOF as e:
        print()
        print(e)
        sys.stdout.flush()
        while True:
            time.sleep(10)
            print('Trying again...')
            sys.stdout.flush()
            try:
                read_sheet(use_mtime=False)
            except FlowNotAllowed:
                pass
            else:
                break

    loop = asyncio.get_event_loop()
    bot = Bot()

    run_tasks = asyncio.gather(
        loop.create_task(bot.start()),
        loop.create_task(flusher()),
        loop.create_task(bot.run_schedule()))
    loop.run_until_complete(run_tasks)
    run_tasks.result()
    raise Exception("infinite loop returned??")


main()
