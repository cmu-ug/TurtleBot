import os
from discord.ext import commands
from config import *

DATA_DIR = "data/"
STATIC_DATA_DIR = "data_static/"

def command_prefix(bot, message):
    return "&" if os.environ["ENV"] == "PROD" else "?"

def is_admin(user):
    return (user.id in ADMINS)

# Decorator for admin commands
def admin_only():
    async def predicate(ctx):
        return is_admin(ctx.author)
    return commands.check(predicate)


log_channel = None

async def log(bot, msg, embed=None):
    print(msg)
