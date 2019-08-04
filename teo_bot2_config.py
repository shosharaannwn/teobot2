import os

# google sheet file identifier
google_sheet="1BLIA28zqbCDtin1VhUIB3hCE9swBugn-_6qcaNBpXfw"

# Discord bot authorization token
for fn in ('bot_token', '/var/run/secrets/bot_token'):
    if os.path.exists(fn):
        with open(fn, 'r') as f:
            bot_token = f.read().strip()
        break
else:
    raise Exception("couldn't find bot_token")

# google app credentials.json file
for fn in ('credentials.json', '/var/run/secrets/google_sheet_credentials'):
    if os.path.exists(fn):
        json_creds_file = fn
        break
else:
    raise Exception("couldn't find google_sheet_credentials")    

#google app clickthrough authorization
token_path="/var/google_sheet_pickle/pickle"

# Discord channel and guild for error messages
log_channel_guild_name = "TEO_Bot_Test" 
log_channel_name="prod_admin" 

# Discord channel and guild for announcements
guild_name="The Eternal Order" 
msg_channel_name="the-eternal-order"
