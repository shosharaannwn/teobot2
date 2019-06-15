#!/usr/bin/python3

import discord
import time
import datetime
import re
import asyncio
import sys
import aioschedule as schedule
import json

g_message_printed = False

client=discord.Client()

async def print_message(message):
    global g_message_printed
    g_message_printed = True
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
    lines=[]
    # lines.append(["Message 1", "W,Th", "hourly"])
    # lines.append(["Message 2", "Th,F", "10:30,19:02,19:03,19:04,19:05,19:06,19:07,19:08,19:09,19:10"])
    # lines.append(["Message 3", "daily", "19:22,19:23,19:24,19:25,19:26,19:27,19:28,19:29,19:30,19:31"])

    now=datetime.datetime.now()
    lines.append(["FOOO", "daily", f"{now.hour}:{now.minute+1},{now.hour}:{now.minute+2},{now.hour}:{now.minute+3},{now.hour}:{now.minute+4},{now.hour}:{now.minute+5}"])

    for line in lines:
        message, days, times = line

        if days.strip().lower() == 'daily':
            days = set(day_names)
        else:
            days = set(map(normalize_day, days.strip().split(',')))
        
        hours=[] # Hours is arbitrary length
        times = times.strip()
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
                getattr(schedule.every(), day).at(time).do(print_message, message)
                

        

# def schedule_messages():
#     sched_arr={}
#     for i in range(len(schedule)):
#         for d in range(7):
#             if (schedule[i]["days"][d]==1):
#                 for h in schedule[i]["hours"]:
#                     namestr=str(i)+"_"+str(d)+"_"+h
#                     scheduler.every(d).weekday.at(h).do(print_message, schedule[i]["message"])
#    for i in sched_arr:
 #       cron_sched.add_job(sched_arr[i])


# def clear_schedule():
# #    for i in list(sched_arr):
#  #       xxchron_sched.del_job(i)
#     scheduler.clear()

async def update_scheduler():
    while True:
        sys.stdout.write("Second loop actually ran!!\n")
        if g_message_printed:
            sys.stdout.write("Clearing schedule...\n")
            schedule.clear()
        await asyncio.sleep(10)
    
loop = asyncio.get_event_loop()

read_schedule()

loop.create_task(update_scheduler())

while True:
    loop.run_until_complete(schedule.run_pending())
    time.sleep(0.1)
    


# schedule_messages()
# cron=asyncio.ensure_future(scheduler.run_pending())
# update=asyncio.ensure_future(update_scheduler())
# loop=asyncio.get_event_loop()
# loop.run_forever()

    
#print(json.dumps(schedule, indent=True))


