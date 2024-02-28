import os

# google sheet file identifier
google_sheet="1DhBuh1NyOXb2T_eBNbV4QsE0vazk1JsWmnECvUSSF_E"

# Discord bot authorization token
for fn in ('bot_token', '/run/secrets/bot_token'):
    if os.path.exists(fn):
        with open(fn, 'r') as f:
            bot_token = f.read().strip()
        break
else:
    raise Exception("couldn't find bot_token")

# google app credentials.json file
for fn in ('credentials.json', '/run/secrets/google_sheet_credentials'):
    if os.path.exists(fn):
        json_creds_file = fn
        break
else:
    raise Exception("couldn't find google_sheet_credentials")

#google app clickthrough authorization
if json_creds_file == 'credentials.json':
    token_path="google_token.json"
else:
    token_path="/var/google_token.json"

# Discord channel and guild for error messages
log_channel_guild_name = "TEO_Bot_Test"
log_channel_name="admin"

# Discord channel and guild for announcements
guild_name="TEO_Bot_Test"
msg_channel_name="announcements"

