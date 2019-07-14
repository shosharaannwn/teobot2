TEOBOT 
=======

TEOBOT reads a spreadheet of announcements from a google sheet and then makes those announcemnts in Discord at the scheduled times.


Setup
----

In order to set up TEOBOT you will need three files:

* `credentials.json`, a google App API credentials file.
* `bot_token`, a discord bot api token
* `google_sheet_token` the google file id for the spreadsheet containing the announcments.


### `credentials.json`

See Google's documentation [here](https://developers.google.com/drive/api/v3/quickstart/python) and [here](https://developers.google.com/sheets/api/quickstart/python).

Make sure to click "Enable the ... API" for each of those pages.

### `bot_token`

I don't know where to get this.  Discord or soemthing.

### `gogle_sheet_token`

This isn't really a secret token, it's just the google sheet file id.

The sheet for TEO is at [https://docs.google.com/spreadsheets/d/1BLIA28zqbCDtin1VhUIB3hCE9swBugn-_6qcaNBpXfw/edit#gid=0](), so the token is
`1BLIA28zqbCDtin1VhUIB3hCE9swBugn-_6qcaNBpXfw`

### docker

Once you have those files in place, just do this to build and run the bot

```
# cd /path/to/teobot
# docker-compose build
# docker-compose up -d
```

If you look in the logs, you'll see it's stuck because it needs to do an OAuth clickthrough before it can access the google APIs.  Use this command to go through the clickthrough interactivly.   Once you complete that you should see in the logs that the bot is up and running.

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


