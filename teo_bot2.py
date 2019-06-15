#!/usr/bin/python3

import discord
import time
import datetime
import re
import asyncio
import sys
import aioschedule as scheduler

client=discord.Client()

#cron_sched= Scheduler()

# 
schedule = []
# Message, Day (M,T,W,Th,F,S,Su|daily), Time list (HH:MM,HH:MM or "hourly")

async def print_message(message):
    sys.stdout.write("Message :"+message+"\n")

def print_error(error):
    sys.stdout.write("Error :"+error+"\n")

def read_schedule():
    lines=[]
    lines.append(["Message 1", "W,Th", "hourly"])
    lines.append(["Message 2", "Th,F", "10:30,19:02,19:03,19:04,19:05,19:06,19:07,19:08,19:09,19:10"])
    lines.append(["Message 3", "daily", "19:22,19:23,19:24,19:25,19:26,19:27,19:28,19:29,19:30,19:31"])
    for i in range(len(lines)):
        schedstr=re.sub("\s+","",lines[i][1])
        days=[0,0,0,0,0,0,0] # Initialized array of 0s for booleans representing days of the week
        if not (re.match("daily|[ MondayTuesWhrFiS,]+", lines[i][1], re.IGNORECASE)):
            err="Eternal Bot Scheduling Error: Day String "+lines[i][1]+" associated with message "+lines[i][0]+"is invalid"
            raise ValueError(err)
        if not (re.match("hourly|[ 0-9:,]+", lines[i][2], re.IGNORECASE)):
            err="Eternal Bot Scheduling Error: Hour String "+lines[i][2]+" associated with message "+lines[i][0]+"is invalid"
            raise ValueError(err)
        if (re.match("daily", lines[i][1], re.IGNORECASE)):
            days=[1,1,1,1,1,1,1] # Initialize all days to true
        else:
            for j in re.split(",", schedstr):
                if (re.match("M|monday|Mon", j, re.IGNORECASE)):
                    days[0]=1
                elif (re.match("T|tuesday|Tues", j, re.IGNORECASE)):
                    days[1]=1
                elif (re.match("W|wednesday|wed", j, re.IGNORECASE)):
                    days[2]=1
                elif (re.match("Th|thursday|Thurs", j, re.IGNORECASE)):
                    days[3]=1
                elif (re.match("F|friday|fri", j, re.IGNORECASE)):
                    days[4]=1
                elif (re.match("s|saturday|sat", j, re.IGNORECASE)):
                    days[5]=1
                elif (re.match("su|sunday|sun", j, re.IGNORECASE)):
                    days[6]=1
                else:
                    err="Eternal Bot Scheduling Error: Day String "+lines[1]+" associated with message "+lines[0]+"contains an invalid day of the week"
                    raise ValueError(err)
        schedstr=re.sub("\s+","",lines[i][2])
        hours=[] # Hours is arbitrary length
        if (re.match("hourly", schedstr, re.IGNORECASE)):
            schedstr="00:00,01:00,02:00,03:00,04:00,05:00,06:00,07:00,08:00,09:00,10:00,11:00,12:00,13:00,14:00,15:00,16:00,17:00,18:00,19:00,20:00,21:00,22:00,23:00" # Set a string that makes it easy to handle hourly case like other cases
        for j in re.split(",", schedstr):
            if not (re.match("(([0-9]:)|([0-1][0-9]:)|(2[0-3]:))|[0-5][0-9]", j, re.IGNORECASE)):
                err="Eternal Bot Scheduling Error: Hour "+j+" associated with message "+lines[i][0]+"is invalid"
                raise ValueError(err)
            else:
                hours.append(j)
        schedule.append({"message": lines[i][0], "days": days, "hours": hours})

def schedule_messages():
    sched_arr={}
    for i in range(len(schedule)):
        for d in range(7):
            if (schedule[i]["days"][d]==1):
                for h in schedule[i]["hours"]:
                    namestr=str(i)+"_"+str(d)+"_"+h
                    scheduler.every(d).weekday.at(h).do(print_message, schedule[i]["message"])
#    for i in sched_arr:
 #       cron_sched.add_job(sched_arr[i])


def clear_schedule():
#    for i in list(sched_arr):
 #       xxchron_sched.del_job(i)
    scheduler.clear()

async def update_scheduler():
    while True:
        sys.stdout.write("Second loop actually ran!!\n")
#   await cron_sched.start()
        now=datetime.datetime.now()
        if (now.hour==19 and now.minute==29):
            sys.stdout.write("Clearing schedule...\n")
            clear_schedule()
        await asyncio.sleep(60)

read_schedule()
schedule_messages()

cron=asyncio.ensure_future(scheduler.run_pending())
update=asyncio.ensure_future(update_scheduler())
loop=asyncio.get_event_loop()
loop.run_forever()


