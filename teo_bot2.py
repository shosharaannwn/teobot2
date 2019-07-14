#!/usr/bin/python3

import os
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--logfile", "-l")
parser.add_argument("--flow", action='store_true', help="just do OAuth flow and then exit")
args = parser.parse_args()

if args.logfile:
    logfile = open(args.logfile, 'a')
    sys.stdout = logfile
    sys.stderr = logfile

if sys.platform == 'darwin':
    # this is so ctypes will load the right libcrypto
    dyld_library_path = os.environ.get('DYLD_LIBRARY_PATH', '').split(':')
    dyld_library_path += [os.path.join(sys.prefix, 'lib')]
    os.environ['DYLD_LIBRARY_PATH'] = ':'.join(dyld_library_path)

import discord
import time
import datetime
import re
import asyncio
import aioschedule as schedule
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import getpass


################

####SET THESE VARIABLES FOR YOUR SERVER INSTALLATION

# Discord bot authorization token
for fn in ('bot_token', '/var/run/secrets/bot_token'):
    if os.path.exists(fn):
        with open(fn, 'r') as f:
            bot_token = f.read().strip()
        break
else:
    raise Exception("couldn't find bot_token")

# google sheet file identifier
for fn in ('google_sheet_token', '/var/run/secrets/google_sheet_token'):
    if os.path.exists(fn):
        with open(fn, 'r') as f:
            google_sheet_token = f.read().strip()
        break
else:
    raise Exception("couldn't find google_sheet_token")

# google app credentials.json file
for fn in ('credentials.json', '/var/run/secrets/google_sheet_credentials'):
    if os.path.exists(fn):
        json_creds_file = fn
        break
else:
    raise Exception("couldn't find google_sheet_credentials")    

#google app clickthrough authorization
if os.path.isdir('/var/google_sheet_pickle'):
    token_path="/var/google_sheet_pickle/pickle"
else:
    token_path="pickle"

log_channel_name="log" # Discord channel for error messages
update_channel_name="update" # Discord channel on which to listen for forced updates
guild_name="The Eternal Order" # Guild name (Discord server)
msg_channel_name="the-eternal-order"

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
google_sheet=google_sheet_token
bot=None  # Discord bot 
last_mtime=None # Global for google sheet last modified time
last_update=None # Global for scheduler last update day

class FlowEOF(Exception):
    pass

class FlowNotAllowed(Exception):
    pass

# Reads a google sheet and sets the scheduler accordingly
def read_sheet(allow_flow=False, update_mtime=True):
    global last_mtime
    creds = None
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
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
                              "try: docker-compose exec teobot /teo_bot2.py --flow") from e
        with open(token_path, 'wb') as token:
            pickle.dump(creds,token)
    
    google_sheets = build('sheets', 'v4', credentials=creds)
    google_drive = build('drive', 'v3', credentials=creds)

    mtime = google_drive.files().get(fileId=google_sheet, fields="modifiedTime").execute()['modifiedTime']

    if not update_mtime:
        print(f'read the sheet, mtime = {mtime}')
        return

    if ((last_mtime is None) or (last_mtime != mtime)):
        last_mtime=mtime
        print(f'Set new sheet modification time as {mtime}')
    else:
        return None # Don't need to read the sheet and update the scheduler
    result = google_sheets.spreadsheets().values().get(spreadsheetId=google_sheet,range="A2:C").execute()
    lines = result.get('values', [])
    return lines



# Prints message "message" using Bot bot
async def print_message(message, bot):
    now=datetime.datetime.now()
    message=re.sub("\{\$TIME\}", now.strftime("%I:%M %p %Z"), message)
    message=re.sub("\{\$DATE\}", now.strftime("%A %B %d, %Y"), message)
    await bot.send(message)
    print(f"Message : {message}\n")
    

def print_error(error):
    print(f"Error : {error}\n")


class ScheduleParseError(Exception):
    pass

def normalize_day(day):
    day = day.lower()
    try:
        return day_abbrevs[day]
    except IndexError:
        raise ScheduleParseError(f"Eternal Bot Scheduling Error: Day String {day} associated with message {message} is invalid")
    
def read_schedule():
    global last_update
    lines=read_sheet()
    if lines is None:
        return # Nothing to do, no need to update scheduler.
    schedule.clear() # Clear scheduler
    #now=datetime.datetime.now()
    #lines.append(["FOOO", "daily", f"{now.hour}:{now.minute+1},{now.hour}:{now.minute+2},{now.hour}:{now.minute+3},{now.hour}:{now.minute+4},{now.hour}:{now.minute+5}"])

    for line in lines:
        message, days, times = line
        days=re.sub("\s","", days)
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
            if not (re.match("(([0-9]:)|([0-1][0-9]:)|(2[0-3]:))|[0-5][0-9]", time, re.IGNORECASE)):
                raise ScheduleParseError(f"Eternal Bot Scheduling Error: Hour {time} associated with message {message} is invalid")

        for day in days:
            print(times)
            for time in times:
                print(f"Scheduled message {message} for {day} at {time}")
                getattr(schedule.every(), day).at(time).do(print_message, message, bot)
                
        last_update=datetime.datetime.now().strftime("%D")


# Event loop to listen for manual update request or to check for updates once a day
async def run_schedule(bot):
    global last_update
    while True:
        await schedule.run_pending()
        now=datetime.datetime.now().strftime('%D')
        if ((last_update is None) or (last_update != now)):
            last_update = now
            print(f"Updating sheet for day {last_update}\n")
            read_schedule()
        await asyncio.sleep(1)    

# Discord Bot sublcass
class Bot:

    async def find_guild(self):
        await self.client.wait_until_ready()
        for guild in self.client.guilds:
            if guild.name==guild_name:
                print("found guild!", guild)
                return guild
        else:
            sys.stdout.write("Invalid guild name "+guild_name+"\n")
            sys.exit(1)

    async def send(self, message):
        sys.stdout.write("In bot send for Message :"+message+"\n")
        channel=await self.msg_channel
        await channel.send(message)

    async def find_channel(self, name):
        guild = await self.guild
        for channel in guild.channels:
            if channel.name == name:
                print("found channel!", name, channel)
                return channel
        else:
            print("didn't find channel!", name)
            return None

    async def start(self):
        asyncio.create_task(self.client.start(bot_token))
        self.guild = asyncio.ensure_future(self.find_guild())
        #self.log_channel = asyncio.ensure_future(self.find_channel(log_channel_name))
        #self.update_channel = asyncio.ensure_future(self.find_channel(update_channel_name))
        self.msg_channel = asyncio.ensure_future(self.find_channel(msg_channel_name))

    def __init__(self):
        self.client = discord.Client()

async def flusher():
    while True:
        sys.stdout.flush()
        await asyncio.sleep(1)

def main():
    print("running as uid", os.getuid(), "i.e.", getpass.getuser())
    
    if args.flow:
        read_sheet(allow_flow=True, update_mtime=False)
        sys.exit(0)

    try:
        read_sheet(allow_flow=True, update_mtime=False)
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
                read_sheet(update_mtime=False)
            except FlowNotAllowed:
                pass
            else:
                break

    loop = asyncio.get_event_loop()
    bot = Bot()
    loop.create_task(bot.start())
    loop.create_task(run_schedule(bot))
    loop.create_task(flusher())
    loop.run_forever()

main()
