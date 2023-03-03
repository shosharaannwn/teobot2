TEOBOT 
=======

TEOBOT reads a spreadsheet of announcements from a google sheet and then makes those announcements in Discord at the scheduled times.


Setup
----

In order to set up TEOBOT you will need:

* `./credentials.json`, a google App API credentials file.
* `./bot_token`, a discord bot api token
* `./teo_bot_config.py`:
  * `google_sheet` the google file id for the spreadsheet containing the announcements.
  * `log_channel_name` the name of the channel log messages should go to
  * `log_channel_guild_name` the guild name for `log_channel_name`
  * `msg_channel_name` the name of the channel announcement messages should go to
  * `guild_name` the guild for `msg_channel_name`


### `credentials.json`

See Google's documentation [here](https://developers.google.com/drive/api/v3/quickstart/python) and [here](https://developers.google.com/sheets/api/quickstart/python).

Make sure to click "Enable the ... API" for each of those pages.

### `bot_token`

I don't know where to get this.  Discord or something.

### `gogle_sheet`

It's the google sheet file id.

The sheet for TEO is at <https://docs.google.com/spreadsheets/d/1BLIA28zqbCDtin1VhUIB3hCE9swBugn-_6qcaNBpXfw/edit#gid=0>, so the token is
`1BLIA28zqbCDtin1VhUIB3hCE9swBugn-_6qcaNBpXfw`

### docker

Once you have those files in place, just do this to build and run the bot

```
# cd /path/to/teobot
# docker-compose build
# docker-compose up -d
```

If you look in the logs, you'll see it's stuck because it needs to do an OAuth clickthrough before it can access the google APIs.  Use this command to go through the clickthrough interactively.   Once you complete that you should see in the logs that the bot is up and running.

```
# docker-compose exec teobot /teo_bot2.py --flow
```

Monitoring
----------

To see the logs, use either this

```
# cd /path/to/teobot
# docker-compose logs
```

Or this (container name may be different for you, use `docker ps`)

```
# docker logs teobot2_teobot_1 
```


