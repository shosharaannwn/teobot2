import os

# google sheet file identifier
google_sheet="1BLIA28zqbCDtin1VhUIB3hCE9swBugn-_6qcaNBpXfw"
#faq_sheet="14A36tKh2zXiqSRbBNT2aUC6I9sqWXXkJtLvqth-3yos"

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

# Indexes into the FAQ sheet for the announcements
#faq_imp=3
#faq_rep=2
#faq_topic=6
