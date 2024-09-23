import discord
from discord.ext import commands
import re
import numpy as np
import urllib.request
import imutils
import random
import cv2
import os
import time
import sys
from PIL import Image, ImageDraw, ImageOps
import asyncio
from math import ceil, sqrt
import requests

with open("data_static/regex_copypasta.txt", "r+") as f:
    regex_copypasta = f.readlines()

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def quant(self, ctx, user: discord.Member=None):
        if user is not None:
            await ctx.channel.send("heeyyy {} :meowaww:  so like 👉 👈 do u know 💭 how hard :tiredghost: it is to join quant 🔢  club and poker ♦️ club ?? i love hs olys ✍️ and im trying 😤 to do an additional ✝️  in cs 💻  and compfi :pleading: and i wanna go 🏃 to jane street 🎏 and get sponsored 💸  by citadel 🏛️ ".format(user.display_name.replace("@", "@ ")))
        else:
            await ctx.channel.send("heeyyy kt :meowaww:  so like 👉 👈 do u know 💭 how hard :tiredghost: it is to join quant 🔢  club and poker ♦️ club ?? i love hs olys ✍️ and im trying 😤 to do an additional ✝️  in cs 💻  and compfi :pleading: and i wanna go 🏃 to jane street 🎏 and get sponsored 💸  by citadel 🏛️ ")

    @commands.command()
    async def eat(self, ctx, user: discord.Member=None):
        if user is not None:
            await ctx.channel.send("Nom nom nom **{}**".format(user.display_name.replace("@", "@ ")))

        if user == self.bot.user:
            await ctx.message.add_reaction(chr(0x1F622))

    @commands.command()
    async def consume(self, ctx, user: discord.Member=None):
        await self.eat(ctx, user)

    last_xandervibes = 0

    @commands.command()
    async def nishyvibes(self, ctx):
        await ctx.channel.send("<:bnyabnyabnya:1189851810815545354>")

    @commands.command()
    async def xandervibes(self, ctx):
        if ctx.message.author.id == 188844646296846336:
            await ctx.channel.send("Xander you're a catgirl")
        else:
            if (random.randint(1, 5) == 2) or (time.time() - self.last_xandervibes > 50):
                await ctx.channel.send("The xander catgirl vibes are immaculate today")
            else:
                await ctx.channel.send("The xander vibes are immaculate today")

        self.last_xandervibes = time.time()


    @commands.command()
    async def cknsjme(self, ctx, user: discord.Member=None):
        if user is not None:
            if ctx.message.author.id == 399746540849070093:
                await ctx.channel.send("Nyom Nyom Nyom **{}**".format(user.display_name.replace("@", " ")))
            else:
                await ctx.channel.send("Schlorp schlorp schlorp **{}**".format(user.display_name.replace("@", " ")))

        if ctx.message.author.id == 294205236975894528:
            await ctx.channel.send("https://tenor.com/view/food-coma-food-eat-starving-kirby-gif-4698182")

        if user == self.bot.user:
            await ctx.message.add_reaction(chr(0x1F622))

    @commands.command()
    async def walk(self, ctx):
        if random.randint(0, 100) < 40:
            await ctx.channel.send("https://tenor.com/view/turtle-cute-walking-so-cute-gif-16891144")
        else:
            await ctx.channel.send("meow meow")

    @commands.command()
    async def strangle(self, ctx, *flags):
        await ctx.channel.send("https://tenor.com/view/bart-simpson-strangle-gif-10314540")

    @commands.command()
    async def excellent(self, ctx, *flags):
        await ctx.channel.send("https://tenor.com/view/the-simpsons-evil-laugh-excellent-scheming-gif-4120925")

    @commands.command()
    async def hug(self, ctx):
        try:
            is_meowo = any(["meowo" in role.name for role in ctx.author.roles])
        except:
            is_meowo = False

        link = "https://tenor.com/view/hug-peachcat-cat-cute-gif-13985247" if (is_meowo) else "https://tenor.com/view/milk-and-mocha-hug-cute-kawaii-love-gif-12535134"
        await ctx.channel.send(link)

    @commands.command()
    async def burn(self, ctx, msg):
        try:
            emote = re.findall(r'<:\w*:\d*>', msg)[0]
        except:
            if ord(msg[0]) > 255:
                emote = msg[0]
            else:
                await ctx.channel.send("Invalid emoji")
                return

        fire = chr(0x1F525)

        await ctx.channel.send(f"{3 * fire}\n{fire}{emote}{fire}\n{3 * fire}")

    @commands.command()
    async def love(self, ctx, msg: str = ".."):
        try:
            emote = re.findall(r'<:\w*:\d*>', msg)[0]
        except:
            if ord(msg[0]) > 255:
                emote = msg[0]
            else:
                print("WAO")
                await ctx.channel.send(chr(0x2764))
                return

        heart = chr(0x2764)

        await ctx.channel.send(f"{3 * heart}\n{heart}{emote}{heart}\n{3 * heart}")

    @commands.command()
    async def pfp(self, ctx, user: discord.Member=None, size: int = 128):
        if user is not None:
            avatar = str(user.avatar.with_size(size).with_format("png").url)
            await ctx.channel.send(avatar)

    """
        Return the link to the png of the given emote
    """
    @commands.command()
    async def emote(self, ctx, emote):
        try:
            emotes = re.findall(r'<:\w*:\d*>', emote)
            aemotes = re.findall(r'<a:\w*:\d*>', emote)

            for emote in emotes:
                emote_id = emote.split(":")[2].replace(">", "")
                await ctx.channel.send("https://cdn.discordapp.com/emojis/{}.png".format(emote_id))

            for emote in aemotes:
                emote_id = emote.split(":")[2].replace(">", "")
                await ctx.channel.send("https://cdn.discordapp.com/emojis/{}.gif".format(emote_id))

        except:
            await ctx.channel.send("Invalid emote")

    """
        Return the link to the png of all emotes from the given message
    """
    @commands.command()
    async def stealm(self, ctx, message_id: int = 0):
        dm = await ctx.author.create_dm()
        try:
            message = await ctx.channel.fetch_message(message_id)
            emote = message.content

            emotes = re.findall(r'<:\w*:\d*>', emote)
            aemotes = re.findall(r'<a:\w*:\d*>', emote)

            already_sent = []

            for emote in emotes:
                emote_id = emote.split(":")[2].replace(">", "")
                if emote_id not in already_sent:
                    await dm.send("https://cdn.discordapp.com/emojis/{}.png".format(emote_id))
                    already_sent.append(emote_id)

            for emote in aemotes:
                emote_id = emote.split(":")[2].replace(">", "")
                if emote_id not in already_sent:
                    await dm.send("https://cdn.discordapp.com/emojis/{}.gif".format(emote_id))
                    already_sent.append(emote_id)

        except:
            print("Stealm error", sys.exc_info()[0])
            await ctx.channel.send("Invalid")

    """
        Return the link to the png of all reaction emotes from the given message
    """
    @commands.command()
    async def stealr(self, ctx, message_id: int = 0):
        dm = await ctx.author.create_dm()
        try:
            message = await ctx.channel.fetch_message(message_id)

            reactions = [r.emoji for r in message.reactions]

            already_sent = []

            for e in reactions:
                try:
                    emote_id = e.id
                    anim = e.animated
                    if emote_id not in already_sent:
                        if anim:
                            await dm.send("https://cdn.discordapp.com/emojis/{}.gif".format(emote_id))
                        else:
                            await dm.send("https://cdn.discordapp.com/emojis/{}.png".format(emote_id))
                        already_sent.append(emote_id)
                except:
                    pass

        except:
            await ctx.channel.send("Invalid")

    async def steals(self, ctx, message_id: int = 0):
        dm = await ctx.author.create_dm()
        try:
            message = await ctx.channel.fetch_message(message_id)

            stickers = [s.image for s in message.stickers]

            print(stickers[0])

        except:
            await ctx.channel.send("Invalid")


    # stealm + stealr
    @commands.command()
    async def steal(self, ctx, message_id: int = 0):
        if message_id == 0:
            if ctx.message.reference is not None:
                message_id = ctx.message.reference.message_id
            else:
                await ctx.channel.send("Usage: `&steal <message id>` (or alternatively, reply to a message with `&steal` without having to specify an id)")
                return

        await self.stealm(ctx, message_id)
        await self.stealr(ctx, message_id)

    # alias for steal
    @commands.command()
    async def borrow(self, ctx, message_id: int = 0):
        await self.steal(ctx, message_id)

    @commands.command()
    async def regex(self, ctx, html: str = "HTML", regex: str = "regex"):
        print("regex", html, regex)
        requester = str(ctx.message.author)

        embed1 = discord.Embed(colour=discord.Colour(0xA6192E), description=regex_copypasta[0].replace("HTML", html).replace("regex", regex).replace("Regex", regex[0].upper() + (regex[1:] if (len(regex) > 1) else "")).replace("regular expression", regex))
        embed1.set_footer(text=f"Requested by {requester}")

        embed2 = discord.Embed(colour=discord.Colour(0xA6192E), description=regex_copypasta[1].replace("HTML", html).replace("regex", regex).replace("Regex", regex[0].upper() + (regex[1:] if (len(regex) > 1) else "")).replace("regular expression", regex))
        embed2.set_footer(text=f"Requested by {requester}")

        await ctx.channel.send(embed=embed1)
        await asyncio.sleep(1)
        await ctx.channel.send(embed=embed2)

