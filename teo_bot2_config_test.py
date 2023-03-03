import os

# google sheet file identifier
google_sheet="1DhBuh1NyOXb2T_eBNbV4QsE0vazk1JsWmnECvUSSF_E"

# Discord bot authorization token
for fn in ('bot_token', 'bot_token'):
    if os.path.exists(fn):
        with open(fn, 'r') as f:
            bot_token = f.read().strip()
        break
else:
    raise Exception("couldn't find bot_token")

# google app credentials.json file
for fn in ('credentials.json', 'google_sheet_credentials'):
    if os.path.exists(fn):
        json_creds_file = fn
        break
else:
    raise Exception("couldn't find google_sheet_credentials")    

#google app clickthrough authorization
token_path="pickle"

# Discord channel and guild for error messages
log_channel_guild_name = "TEO_Bot_Test" 
log_channel_name="prod_admin" 

# Discord channel and guild for announcements
guild_name="TEO_Bot_Test" 
msg_channel_name="teo_bot"
#help_channel_name="teobot_help"

