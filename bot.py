import discord
from discord.ext import commands
import os
import asyncio
import time

import threading

from cogs import util, fun, cmu, poll, andrewid, malloc, help

from config import DENY_LIST

from utils import command_prefix

# We should probably use slash commands eventually but they still aren't
# totally stable on mobile even as of mid 2024
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=command_prefix, help_command=None, intents=intents)

@bot.check_once
def verify(ctx):
    try:
        return (ctx.message.guild.id, ctx.message.channel.id) not in DENY_LIST
    except:
        pass

    return True

# Set up cogs for the bot
async def setup_bot():
    await bot.add_cog(util.Util(bot))
    await bot.add_cog(fun.Fun(bot))
    await bot.add_cog(cmu.CMU(bot))
    await bot.add_cog(poll.Poll(bot))
    await bot.add_cog(andrewid.AndrewId(bot))
    await bot.add_cog(malloc.Malloc(bot))
    await bot.add_cog(help.Help(bot))

# Log joined servers
def log_thread():
    time.sleep(5)

    async def log_func():
        for server in bot.guilds:
            print(server.id, server.name)

    eventloop.run_until_complete(log_func())
    eventloop.close()

eventloop = asyncio.get_event_loop()
eventloop.run_until_complete(setup_bot())
threading.Thread(target=log_thread).start()
print("Starting bot")
bot.run(os.environ["BOT_TOKEN"])
