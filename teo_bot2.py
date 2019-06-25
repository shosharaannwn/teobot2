#!/usr/bin/python3

import discord
import time
import datetime
import re
import asyncio
import sys
import aioschedule as schedule
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os.path

################

####SET THESE VARIABLES FOR YOUR SERVER INSTALLATION

bot_token="NTg4NTExOTMyNjgwNjM0Mzgx.XQ6kNw.054mJRu_0CHDlLD7UBDJI2k3qyU"  # Discord bot authorization token
log_channel_name="log" # Discord channel for error messages
update_channel_name="update" # Discord channel on which to listen for forced updates
guild_name="TEO_Bot_Test" # Guild name (Discord server)
msg_channel_name="teo_bot" # Discord channel on which to send announcements
google_sheet_token="1DhBuh1NyOXb2T_eBNbV4QsE0vazk1JsWmnECvUSSF_E"
token_path="token.pickle"
json_creds_file="credentials.json"


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
google_scopes=['https://www.googleapis.com/auth/drive.metadata.readonly', 'https://www.googleapis.com/auth/spreadsheets.readonly']
google_sheet=google_sheet_token
bot=None  # Discord bot 
last_mtime=None # Google sheet last modified time


# Reads a google sheet and sets the scheduler accordingly
def read_sheet():
    creds = None
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(json_creds_file, google_scopes)
            creds=flow.run_local_server()
        with open(token_path, 'wb') as token:
            pickle.dump(creds,token)
    
    google_sheets = build('sheets', 'v4', credentials=creds)
    google_drive = build('drive', 'v3', credentials=creds)

    mtime = google_drive.files().get(fileId=google_sheet, fields="modifiedTime").execute()['modifiedTime']
#    if last_mtime is None:
 #       last_mtime=cur_mtime
    print(f'mtime = {mtime}', file=sys.stdout)

    result = google_sheets.spreadsheets().values().get(spreadsheetId=google_sheet,range="A2:C").execute()
    lines = result.get('values', [])
    return lines
#  for row in values:
 #       print ('%s, %s, %s' % (row[0], row[1], row[2]))
        


# Prints message "message" using Bot bot
async def print_message(message, bot):
    now=datetime.datetime.now()
    message=re.sub("\{\$TIME\}", now.strftime("%I:%M %p %Z"), message)
    message=re.sub("\{\$DATE\}", now.strftime("%A %B %d, %Y"), message)
    await bot.send(message)
    sys.stdout.write("Message :"+message+"\n")
    

def print_error(error):
    sys.stdout.write("Error :"+error+"\n")


class ScheduleParseError(Exception):
    pass

def normalize_day(day):
    day = day.lower()
    try:
        return day_abbrevs[day]
    except IndexError:
        raise ScheduleParseError(f"Eternal Bot Scheduling Error: Day String {day} associated with message {message} is invalid")
    
    
def read_schedule():
    lines=read_sheet()
    #now=datetime.datetime.now()
    #lines.append(["FOOO", "daily", f"{now.hour}:{now.minute+1},{now.hour}:{now.minute+2},{now.hour}:{now.minute+3},{now.hour}:{now.minute+4},{now.hour}:{now.minute+5}"])

    for line in lines:
        print("In lines loop\n")
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
#                print (f"Scheduled message {message} for {day} at {time}")
                getattr(schedule.every(), day).at(time).do(print_message, message, bot)
                


# Event loop to listen for manual update request or to check for updates once a day
async def update_scheduler(bot):
    while True:
        sys.stdout.write("Second loop actually ran!!\n")
        now=datetime.datetime.now()
        if (now.minute==0 and now.hour==0):
            sys.stdout.write("Clearing schedule...\n")
            schedule.clear()
        await asyncio.sleep(10)
    

# Discord Bot sublcass
class Bot:

    async def find_guild(self):
        print('foo')
        await self.client.wait_until_ready()
        print('bar')
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
        self.log_channel = asyncio.ensure_future(self.find_channel(log_channel_name))
        self.update_channel = asyncio.ensure_future(self.find_channel(update_channel_name))
        self.msg_channel = asyncio.ensure_future(self.find_channel(msg_channel_name))

    def __init__(self):
        self.client = discord.Client()


# Async function to run the schedule (required for asyncio to work properly)
async def run_schedule():
    while True:
        await schedule.run_pending()



loop = asyncio.get_event_loop()

bot = Bot()
loop.create_task(bot.start())

read_schedule()
loop.create_task(update_scheduler(bot))
loop.create_task(run_schedule())

loop.run_forever()



