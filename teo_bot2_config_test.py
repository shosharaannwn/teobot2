import os

#google sheet file identifier
google_sheet="1DhBuh1NyOXb2T_eBNbV4QsE0vazk1JsWmnECvUSSF_E"

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

# google OAuth user login file
if os.path.exists("/var/google_sheet_pickle/"):
    token_path = "/var/google_sheet_pickle/pickle"
else:
    token_path="pickle"

log_channel_name="log" # Discord channel for error messages
guild_name="TEO_Bot_Test" # Guild name (Discord server)
msg_channel_name="teo_bot"
