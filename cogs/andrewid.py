import discord
from discord.ext import tasks, commands
import pickle
import string
import asyncio
import random
import requests
import time
import json
import os
import smtplib
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from utils import log, admin_only
from utils import is_admin, DATA_DIR

users = {}

def load_users():
    global users
    try:
        with open(DATA_DIR+"users.pkl", "rb") as f:
            users = pickle.load(f)
    except:
        users = {}

def save_users():
    global users
    with open(DATA_DIR+"users.pkl", "wb+") as f:
        pickle.dump(users, f, protocol=pickle.HIGHEST_PROTOCOL)

class AndrewId(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        load_users()

    @commands.command()
    @admin_only()
    async def reset_registration(self, ctx, userid: int=None):
        await ctx.channel.send(json.dumps(users[userid]))
        users.pop(userid)
        save_users()

    @commands.command()
    @admin_only()
    async def is_verified(self, ctx, user: discord.User=None):
        if ctx.guild is None:
            await ctx.channel.send(json.dumps(users[user.id]))
        else:
            await ctx.channel.send("User is verified" if (user.id in users and users[user.id]["verified"]) else "User is not verified")

    @commands.command()
    async def joinserver(self, ctx):
        if ctx.guild is None:
            await ctx.channel.send("Please use the `&joinserver` command inside a verification-enabled server instead of in direct messages")
        else:
            if ctx.message.author.id in users and users[ctx.message.author.id]["verified"]:
                verification_role = {
                    372225746770329611: ("cmuwu verified", "Success!"), # Turtwig
                    761315297461665833: ("Verified", "Please head to <#761338601971122187> to set your school and year and get access to the server, and feel free to introduce yourself in <#761330921668345856>"), # General CMU
                    804134098117328946: ("cmu verified", "Please make sure to check out <#811388425445310566> on your way in!"), # Hillel
                    826525175855317043: ("Verified", "Please head over to <#826525176325865523> to get access to your school and degree-specific channels"), # CMU F21 Grads
                    729957048900648980: ("Verified", "Welcome! You've been given access to the rest of the server!"), # CMU Qatar
                    851866008641863751: ("Verified", "Welcome!"), # MechE masters
                    894955855479447572: ("Member", "You now have access to the rest of the server! Please visit <#895747026376073237> to assign yourself additional roles."), # CMUsic Majors
                }
                if ctx.guild.id in verification_role.keys():
                    verif_role, verif_msg = verification_role[ctx.guild.id]
                    role = discord.utils.get(ctx.guild.roles, name=verif_role)
                    await discord.Member.add_roles(ctx.message.author, role)
                    await ctx.channel.send("Thank you for verifying yourself! {}".format(verif_msg))
                else:
                    await ctx.channel.send("Thank you for verifying yourself! This server does not support automatic role assignment, please ping a server admin (see the sidebar for admin list) to get access to the server.")

            else:
                await ctx.channel.send("You are not verified. Please DM the bot with `&register \"andrew id\"` (for example, `&register hbovik`) to verify yourself, or ping a server admin if there is an issue.")

    @commands.command()
    async def registeralum(self, ctx, andrew_id: str=None):
        await self.register(ctx, andrew_id, domain="alumni")

    @commands.command()
    async def register(self, ctx, andrew_id: str=None, domain: str="andrew"):
        if domain not in ["andrew", "alumni"]:
            await ctx.channel.send("Invalid command")
            return

        discord_id = ctx.message.author.id

        if domain != "alumni":
            if discord_id in users:
                if users[discord_id]["verified"]:
                    await ctx.channel.send("You are already verified.")
                    await self.joinserver(ctx)
                else:
                    await ctx.channel.send("You have already requested verification. Please contact <@347518645695414282> if you do not recieve an email within one hour of making your request. Please check your SPAM folder as well (you may need to click 'not spam'), it may have ended up there.")
                return

        if andrew_id is None:
            await ctx.channel.send("Usage: &register \"andrew id\" (for example, `&register hbovik`)")
            return

        if "@" in andrew_id:
            if "alumni" in andrew_id.split("@")[1]:
                domain = "alumni"

            andrew_id = andrew_id.split("@")[0]

        if len(andrew_id) > 10 or len(andrew_id) < 2 or (not andrew_id.lower().isalnum()):
            await ctx.channel.send("Invalid Andrew ID")
            return

        # TODO-someday: might be nice to bring back the finger integration here
        # to verify the andrew ID's validity

        email = andrew_id + "@"+str(domain)+".cmu.edu"
        code = random.randint(10**9, 10**10 - 1)
        discord_name = str(ctx.message.author)

        print(f"Starting verification for {discord_id}, {discord_name}, {andrew_id}")

        try:
            server = smtplib.SMTP("email-smtp.us-east-1.amazonaws.com", 587)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(os.environ.get("SMTP_USER"), os.environ.get("SMTP_PASS"))
            server.sendmail("verification@turtlebot.anishs.net", email, f"Subject: CMU Discord Verification Code\n\nYour verification code that you have reequested for the CMU discord chat is {code}. To verify yourself, please DM TurtleBot with:\n\n&verify {code} \n\nIf you have recieved this email in error, please ignore it.")
            await ctx.channel.send("An email has been sent to your CMU email ({}). Please DM the bot `&verify <code>` with the code you were emailed. If you are an alum and no longer have access to your andrew.cmu.edu account, please DM the bot `&registeralum {}` If you do not get an email, check your SPAM folder as well (you may need to click 'not spam') in case it has ended up there.".format(email, andrew_id))

            users[discord_id] = {
                "andrew_id": andrew_id,
                "email": email,
                "discord_name": discord_name,
                "discord_id": discord_id,
                "code": code,
                "verified": False,
                "request_time": int(time.time()),
                "verify_time": 0
            }
            save_users()

        except Exception as e:
            print(e)
            await ctx.channel.send("Email failed. Please try again later")


    @commands.command()
    async def verify(self, ctx, code: str=None):
        if code is None:
            await ctx.channel.send("Usage: verify <code>")
            return

        if ctx.message.author.id not in users:
            await ctx.channel.send("Please use &register to register your andrew ID")
            return

        if users[ctx.message.author.id]["code"] != int(code):
            await ctx.channel.send("Invalid code")
            return

        users[ctx.message.author.id]["verified"] = True
        users[ctx.message.author.id]["verify_time"] = int(time.time())
        user = users[ctx.message.author.id]

        await ctx.channel.send("Thank you for verifying your andrew ID! Please go back to the server and run `&joinserver` (inside the server) to get access.")

        print(f"Verified {user['discord_id']}, {user['discord_name']} as {user['andrew_id']}")
        await log(self.bot, f"Verified {user['discord_id']}, {user['discord_name']} as {user['andrew_id']}")

        save_users()

