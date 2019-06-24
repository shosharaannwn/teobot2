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

# SET THESE VARIABLES FOR YOUR SERVER INSTALLATION

bot_token="NTg4NTExOTMyNjgwNjM0Mzgx.XQ6kNw.054mJRu_0CHDlLD7UBDJI2k3qyU"  # Discord bot authorization token
log_channel_name="log" # Discord channel for error messages
update_channel_name="update" # Discord channel on which to listen for forced updates
guild_name="TEO_Bot_Test" # Guild name (Discord server)
msg_channel_name="teo_bot" # Discord channel on which to send announcements
google_sheet_token="1DhBuh1NyOXb2T_eBNbV4QsE0vazk1JsWmnECvUSSF_E"

google_scopes=['https://www.googleapis.com/auth/drive.metadata.readonly', 'https://www.googleapis.com/auth/spreadsheets.readonly']
google_sheet=google_sheet_token

bot=None

# g_message_printed = False

# client=discord.Client()
# sys.stdout.write("wtf")

# client.run(bot_token)

# def get_channel(guild, name=""):  # Input is a discord Guild object and a string
#     for channel in guild.channels:
#     	if channel.name == name:
#     		return channel
#     return None

# guild=None

# # import pdb; pdb.set_trace()

# print(client.guilds)

# for g in client.guilds:
#     if g.name==guild_name:
#     	guild=g
#     	break
# if guild==None:
#     sys.stdout.write("Invalid guild name "+guild_name+"\n")
#     sys.exit(1)

# log_channel=get_channel(guild, log_channel_name)
# update_channel=get_channel(guild, update_channel_name)
# msg_channel=get_channel(guild, msg_channel_name)

def read_sheet():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', google_scopes)
            creds=flow.run_local_server()
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds,token)
    
    google_sheets = build('sheets', 'v4', credentials=creds)
    google_drive = build('drive', 'v3', credentials=creds)

    mtime = google_drive.files().get(fileId=google_sheet, fields="modifiedTime").execute()['modifiedTime']
    print(f'mtime = {mtime}', file=sys.stdout)

    result = google_sheets.spreadsheets().values().get(spreadsheetId=google_sheet,range="A2:C").execute()
    lines = result.get('values', [])
    return lines
#  for row in values:
 #       print ('%s, %s, %s' % (row[0], row[1], row[2]))
        
def print_message(message, bot):
#    global g_message_printed
#    g_message_printed = True
     asyncio.create_task(bot.send(message))
     sys.stdout.write("Message :"+message+"\n")
    

def print_error(error):
    sys.stdout.write("Error :"+error+"\n")


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
    # lines.append(["Message 1", "W,Th", "hourly"])
    # lines.append(["Message 2", "Th,F", "10:30,19:02,19:03,19:04,19:05,19:06,19:07,19:08,19:09,19:10"])
    # lines.append(["Message 3", "daily", "19:22,19:23,19:24,19:25,19:26,19:27,19:28,19:29,19:30,19:31"])

    #now=datetime.datetime.now()
    #lines.append(["FOOO", "daily", f"{now.hour}:{now.minute+1},{now.hour}:{now.minute+2},{now.hour}:{now.minute+3},{now.hour}:{now.minute+4},{now.hour}:{now.minute+5}"])

    for line in lines:
        print("In lines loop\n")
        message, days, times = line

        if days.strip().lower() == 'daily':
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
                print (f"Scheduled message {message} for {day} at {time}")
                getattr(schedule.every(), day).at(time).do(print_message, message)
                

        

# def schedule_messages():
 #    sched_arr={}
  #   for i in range(len(schedule)):
   #      for d in range(7):
    #         if (schedule[i]["days"][d]==1):
     #            for h in schedule[i]["hours"]:
      #               namestr=str(i)+"_"+str(d)+"_"+h
       #              scheduler.every(d).weekday.at(h).do(print_message, schedule[i]["message"])
#    for i in sched_arr:
 #       cron_sched.add_job(sched_arr[i])


# def clear_schedule():
# #    for i in list(sched_arr):
#  #       xxchron_sched.del_job(i)
#     scheduler.clear()

async def update_scheduler():
    while True:
        sys.stdout.write("Second loop actually ran!!\n")
        now=datetime.datetime.now()
        if (now.minute==0 and now.hour==0):
            sys.stdout.write("Clearing schedule...\n")
            schedule.clear()
        await asyncio.sleep(10)
    





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

    async def send(message):
    #    global g_message_printed
    #    g_message_printed = True
        await self.msg_channel.send(message)
        sys.stdout.write("In bot send for Message :"+message+"\n")

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


loop = asyncio.get_event_loop()

#read_sheet()
read_schedule()
loop.create_task(update_scheduler())

bot = Bot()
loop.create_task(bot.start())
loop.run_forever()

# while True:
#     loop.run_until_complete(schedule.run_pending())
#     time.sleep(0.1)
    


# schedule_messages()
# cron=asyncio.ensure_future(scheduler.run_pending())
# update=asyncio.ensure_future(update_scheduler())
# loop=asyncio.get_event_loop()
# loop.run_forever()

    
#print(json.dumps(schedule, indent=True))


