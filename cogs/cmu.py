import discord
from discord.ext import commands
from discord import Embed
import json
import random
import requests
from utils import log
import asyncio
import math
import socket
import re
import string
import pytz

# For stats feature
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import dateutil.parser
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from dateutil import tz
import urllib.request
from utils import admin_only, STATIC_DATA_DIR

with open(STATIC_DATA_DIR+"f22_courses.json", "r") as f:
    fall_courses = json.load(f)

with open(STATIC_DATA_DIR+"s23_courses.json", "r") as f:
    spring_courses = json.load(f)

with open(STATIC_DATA_DIR+"postreqs.json", "r") as f:
    postreqs = json.load(f)

with open(STATIC_DATA_DIR+"postreqs-verbose.json", "r") as f:
    postreqs_verbose = json.load(f)

EARLY_FCE_YEAR = 2018
fce_data = pd.read_csv(STATIC_DATA_DIR+"fce_data.csv")
fce_data = np.array(fce_data)[:, :13]
fce_data = np.array([row for row in fce_data if row[1] != "Summer" and int(row[0]) >= EARLY_FCE_YEAR])

# load the CMU syllabus registry data
try:
    with open(STATIC_DATA_DIR+"CMUsyllabi.json") as file:
        syllabi = json.load(file)
except:
    syllabi = {}

SERVER_2024 = 648743792010067979
SERVER_2025 = 781338501068357642

# {(server, src channel): (dst channel)
SCHED_CHANNEL = 707680154100564059
SCHED_CHANNEL_25 = 865776399364784168
SCHED_CHANNEL_26 = 992863306085843054
SCHED_CHANNEL_27 = 1125518714968744036
SCHED_CHANNELS = [SCHED_CHANNEL, SCHED_CHANNEL_25, SCHED_CHANNEL_26, SCHED_CHANNEL_27]
PIN_PAIRS = {
    (372225746770329611, 699889431183622174): 434922196293386252, # Turtwig, #cmuwu, #spam
    (648743792010067979, 690674110346428487): 719050057143418950, # CMU24, #maskshots, #maskshots-pins
    (648743792010067979, 955591259014185020): 988212831415586856, # CMU24, #horizonshots, #horizonshots-pins
    (648743792010067979, 690670433577730080): 719026869722415199, # CMU24, #fine-art, #art-pins
    (648743792010067979, SCHED_CHANNEL): 737372106643210260,  # CMU24, #schedules, #schedules-pins

    (781338501068357642, SCHED_CHANNEL_25): 867957729602449448,  # CMU25, #schedules, #schedules-pins
    (781338501068357642, 794847588347281419): 867957688942882866,  # CMU25, #mugshots, #mugshots-pins
    (781338501068357642, 837834786868297748): 867957760715816970,  # CMU25, #art, #art-pins

    (913583105397383179, SCHED_CHANNEL_26): 1002003296988442746,  # CMU26, #schedules, #schedules-pins
    (1046470793057542194, SCHED_CHANNEL_27): 1134628586414952458,  # CMU27, #schedules, #schedules-pins
}

recent_pins = []

# @zaxioms#2718
def isNowInTimePeriod(startTime, endTime, nowTime):
    if startTime < endTime:
        return nowTime >= startTime and nowTime <= endTime
    else:
        return nowTime >= startTime or nowTime <= endTime

def is_valid_course(msg):
    """
    Helper function that identifies if a string is a valid CMU course
    """
    if len(msg) == 5 and msg.isdigit():
        return True
    if len(msg) == 6 and (msg[:2] + msg[3:]).isdigit() and msg[2] == '-':
        return True
    return False

recent_counts = []
reported_messages = []


class CMU(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    pin_lock = asyncio.Lock()

    num_cmu_messages = 0
    num_cmuwu_messages = 0

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, data):
        if data.user_id == self.bot.user.id:
            return

        """
            meowo ping (when cat2 reacted to a message, forward it to everyone with meowo ping role)
        """
        if data.guild_id is not None and (data.emoji.name == chr(0x1F408) or (len(data.emoji.name) > 0 and data.emoji.name[0] == chr(0x1F408))):
            server = self.bot.get_guild(data.guild_id)
            role = [role for role in server.roles if "meowoping" in role.name.lower().replace(" ", "")]

            if len(role) > 0:
                role = role[0]

                m_str = chr(0x1F408) + f" meow meow https://ptb.discordapp.com/channels/{data.guild_id}/{data.channel_id}/{data.message_id}"

                channel = self.bot.get_guild(data.guild_id).get_channel(data.channel_id)
                message = await channel.fetch_message(data.message_id)

                bot_reacted = False

                for reaction in message.reactions:
                    users = [user async for user in reaction.users()]

                    for user in users:
                        if user.id == self.bot.user.id:
                            bot_reacted = True
                            break

                if not bot_reacted:
                    for member in role.members:
                        if member.id not in [347518645695414282]:
                            dm = await member.create_dm()
                            await dm.send(m_str)


                await message.add_reaction(chr(0x1F408))


        """
            "Pinboard" style message forwarding
            (when pin reaction is received, replicate the message into the associated pinboard channel)
        """
        async with self.pin_lock:
            if (data.emoji.name == chr(0x1F4CD)) or (data.emoji.name == "googlePin"):
                if (data.guild_id, data.channel_id) in PIN_PAIRS:

                    is_schedule = data.channel_id in SCHED_CHANNELS
                    dst_channel_id = PIN_PAIRS[(data.guild_id, data.channel_id)]

                    channel = self.bot.get_guild(data.guild_id).get_channel(data.channel_id)
                    message = await channel.fetch_message(data.message_id)

                    bot_reacted = False

                    if data.message_id in recent_pins:
                        bot_reacted = True
                    else:
                        recent_pins.append(data.message_id)

                    context_url = message.jump_url
                    #print("ATTACHMENTS ", message.attachments, message.embeds)

                    user = self.bot.get_guild(data.guild_id).get_member(data.user_id)
                    image_user = self.bot.get_guild(data.guild_id).get_member(message.author.id)


                    for reaction in message.reactions:
                        users = [user async for user in reaction.users()]

                        for user in users:
                            if user.id == self.bot.user.id:
                                bot_reacted = True
                                break

                    await message.add_reaction(chr(0x2705))
                    await message.add_reaction(chr(0x1F4CD))

                    if not bot_reacted:
                        dst_channel = self.bot.get_guild(data.guild_id).get_channel(dst_channel_id)

                        attachments = list(message.attachments)

                        for attachment in attachments:
                            url = attachment.url

                            if url is None or url == "":
                                await channel.send("Invalid attachment")
                                break

                            if is_schedule:
                                m_embed = discord.Embed(colour=discord.Colour(0xA6192E))
                                m_embed.set_image(url=url)
                                await dst_channel.send(content=image_user.mention, embed=m_embed)
                            else:
                                m_embed = discord.Embed(colour=discord.Colour(0xA6192E), title="")
                                m_embed.set_image(url=url)
                                m_embed.add_field(name="Image by `{}`".format(str(image_user)), value="[Context]({}) (pinned by `{}`)".format(context_url, str(user)))
                                await dst_channel.send(embed=m_embed)

                        for embed in message.embeds:
                            url = embed.url

                            if url.endswith("png") or url.endswith("jpg") or url.endswith("jpeg") or url.endswith("gif") or url.endswith("bmp") or url.endswith("svg"):
                                pass
                            else:
                                continue

                            if url is None or url == "":
                                await channel.send("Invalid attachment")
                                break

                            if is_schedule:
                                m_embed = discord.Embed(colour=discord.Colour(0xA6192E))
                                m_embed.set_image(url=url)
                                await dst_channel.send(content=image_user.mention, embed=m_embed)
                            else:
                                m_embed = discord.Embed(colour=discord.Colour(0xA6192E))
                                m_embed.set_image(url=url)
                                m_embed.add_field(name="Image by `{}`".format(str(image_user)), value="[Context]({}) (pinned by `{}`)".format(context_url, str(user)))
                                await dst_channel.send(embed=m_embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        global recent_counts

        if message.author == self.bot.user:
            return

        clean_content = re.sub(r"<:\w*:\d*>", "", message.clean_content)

        # hihi
        if message.guild is not None and str(message.guild.id) == "781338501068357642":
            if " hihi" in " " + clean_content + " ":
                await message.channel.send("`.... .. .... ..`")

        if message.guild is None:
            print("DM from {}: {}".format(message.author.name, str(message.content)))

        # "My heart is in the work!" easter egg
        if message.guild is not None:
            announcements_25 = "781341413052252170"
            logs_25 =    "785391612616114177"
            vc_logs_25 = "785401025431076884"
            polls_25 =   "794846703752708096"
            if (message.guild.id == SERVER_2024 or message.guild.id == SERVER_2025 or message.guild.id == 1174113338343559269) and str(message.channel.id) not in ["700916718662582413", "648747532364677129", "692136320109117471", announcements_25, logs_25, vc_logs_25, polls_25, "1176998907667038278", "1174207032979632188", "1176992452377329784", "1175326592080281621", "1177126823717519430", "1177113975482224732"]:
                self.num_cmu_messages += 1
                if random.random() < (1.0 / 7000.0):
                    self.num_cmuwu_messages += 1
                    await message.channel.send("My heart is in the work!")


    @commands.command()
    async def finger2(self, ctx, user: str=None):
        if user is None or len(user) < 2:
            await ctx.channel.send("Usage: finger2 <user>@<domain>")
            return

        username, domain = user.split("@")

        assert "." in domain
        assert domain.replace(".", "").isalnum()
        assert username.isalnum()

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        sock.connect((domain, 79))
        sock.sendall((username+"\n").encode())
        await asyncio.sleep(2)
        out = sock.recv(999999)
        out = out.decode()
        sock.close()

        allowed = string.ascii_letters + string.digits + " \n\r\t" + "!\"#$%&\'()*+,-./:;<=>?@[\\]^_{|}~"
        out = "".join(x if x in allowed else "." for x in out)

        out = "```" + out + "```"

        embed = discord.Embed(
            title=f"__**{user}**__",
            colour=discord.Colour(0xA6192E),
            description=out
        )
        await ctx.channel.send(embed=embed)


    """
        Look up a user in the directory
    """
    @commands.command()
    async def finger(self, ctx, user: str=None):
        if user is None or len(user) < 2:
            await ctx.channel.send("Usage: finger <Andrew ID>")
            return

        if "@" in user:
            await self.finger2(ctx, user)
            return

        if is_valid_course(user):
            await self.course(ctx, user)
            return

        await self.finger2(ctx, user+"@andrew.cmu.edu")

    """
        My heart is in the work!
    """
    @commands.command()
    async def carnegie(self, ctx):
        await ctx.channel.send("My heart is in the work")

    @commands.command()
    async def cmuwu(self, ctx):
        await ctx.channel.send("x1={} x2={}".format(self.num_cmu_messages, self.num_cmuwu_messages))

    """
        Find shills
    """
    @commands.command()
    async def shills(self, ctx, shilltype: str=None, serverid: int=None):
        def is_shill(rolename):
            return (("sellout" in rolename.lower()) or ("shill" in rolename.lower())) and ((shilltype.lower() in rolename.lower()) or (shilltype.lower() == "all"))

        if shilltype is None:
            await ctx.channel.send("Please specify a shill type")
            return

        server = self.bot.get_guild(ctx.guild.id if serverid is None else serverid)
        roles = [role for role in server.roles if is_shill(role.name)]

        for role in roles:
            members = role.members

            embed = discord.Embed(
                title=f"__**{role.name}**__",
                colour=role.colour,
                description="   ".join([m.mention for m in members])
            )

            await ctx.channel.send(embed=embed)

        if len(roles) == 0:
            await ctx.channel.send("No shills found")
            return


    @commands.command()
    @admin_only()
    async def leavevoice(self, ctx):
        for client in self.bot.voice_clients:
            await client.disconnect()

    beepboop_lock = asyncio.Lock()
    @commands.command()
    async def beepboop(self, ctx):
        async with self.beepboop_lock:
            for client in self.bot.voice_clients:
                await client.disconnect()

            """if len(self.bot.voice_clients) > 0:
                await ctx.channel.send("Bot is already in a voice channel")
                await ctx.message.add_reaction(chr(0x274C))
                return"""

            try:
                channel = ctx.message.author.voice.channel
            except:
                channel = None

            if channel is None:
                await ctx.channel.send("Must be in a voice channel to use the beep boop")
                await ctx.message.add_reaction(chr(0x274C))
                return

            await ctx.message.add_reaction(chr(0x1F916))

            voice = await channel.connect()
            voice.play(discord.FFmpegPCMAudio("audio/beepboop2.mp3"))
            while voice.is_playing():
                await asyncio.sleep(1)

            voice.stop()

            await voice.disconnect()


    """
        Look up syllabus in CMU syllabus registry
    """
    @commands.command()
    async def syllabus(self, ctx, courseID, mega=False):
        if is_valid_course(courseID):
            courseID = courseID.replace("-", "")
            courseID_int = str(int(courseID))

            if not (courseID_int in syllabi):
                if mega:
                    await ctx.channel.send("Syllabus not found")
                else:
                    await ctx.channel.send("Course not found or syllabus not available.")
                return

            name, syllabus_array = syllabi[courseID_int]
            sections = ""


            sent_title = False
            for term, section, link in syllabus_array:
                sections += "[{}: {}]({})\n".format(term, section, link)

                if len(sections) > 3700:
                    if sent_title:
                        embed = discord.Embed(
                            colour=discord.Colour(0x319C2C),
                            description="{}".format(sections)
                        )
                    else:
                        embed = discord.Embed(
                            title="__**{}: {}**__".format(courseID[:2] + "-" + courseID[2:], name),
                            colour=discord.Colour(0x319C2C),
                            description="\n**Past Sections:**\n{}".format(sections)
                        )
                        sent_title = True

                    sections = ""
                    await ctx.channel.send(embed=embed)

            if sent_title:
                embed = discord.Embed(
                    colour=discord.Colour(0x319C2C),
                    description="{}".format(sections)
                )
            else:
                embed = discord.Embed(
                    title="__**{}: {}**__".format(courseID[:2] + "-" + courseID[2:], name),
                    colour=discord.Colour(0x319C2C),
                    description="\n**Past Sections:**\n{}".format(sections)
                )

            await ctx.channel.send(embed=embed)
        else:
            await ctx.channel.send("Invalid arguments - please specify the course ID (e.g. \"syllabus 15150)\"")


    """
        Get courses with this course as a prereq
    """
    @commands.command()
    async def unlocks_verbose(self, ctx, courseID):
        await self.unlocks(ctx, courseID, verbose=True)

    """
        Get courses with this course as a prereq
    """
    @commands.command()
    async def unlocks(self, ctx, courseID, verbose=False):
        if is_valid_course(courseID):
            courseID = courseID.replace("-", "")
            courseID_int = str(int(courseID))

            courseID = "{:05d}".format(int(courseID_int))
            courseID = courseID[:2] + "-" + courseID[2:]

            pr = postreqs_verbose if verbose else postreqs

            if courseID in pr:
                first = True
                r = pr[courseID]
                while len("\n".join(r)) > 0:
                    end = len(r)
                    while len("\n".join(r[:end])) > 1800:
                        end -= 1
                        assert end > 1

                    if first:
                        embed = discord.Embed(title="Courses with __**{}**__ as prereq".format(courseID), colour=discord.Colour(0x319C2C), description="(Note: these courses may have other prereqs as well - see &course \"course id\" for more details)\n\n"+ ("\n".join(r[:end])))
                        first = False
                    else:
                        embed = discord.Embed(colour=discord.Colour(0x319C2C), description="\n".join(r[:end]))

                    await ctx.channel.send(embed=embed)
                    r = r[end:]

            else:
                await ctx.channel.send("Invalid course or no follow-up courses found")

        else:
            await ctx.channel.send("Invalid arguments - please specify the course ID (e.g. \"unlocks 15150\")")

    """
        Get all course info at once
    """
    @commands.command()
    async def mega(self, ctx, courseID):
        if is_valid_course(courseID):
            await self.course(ctx, courseID, mega=True)
            await self.fce(ctx, courseID, mega=True)
            await self.syllabus(ctx, courseID, mega=True)
            await self.fce_verbose(ctx, courseID, mega=True)
        else:
            await ctx.channel.send("Invalid arguments - please specify the course ID (e.g. \"mega 15150\")")

    """
        Get course info
    """
    @commands.command()
    async def course(self, ctx, courseID, mega=False):
        if is_valid_course(courseID):
            courseID = courseID.replace("-", "")
            courseID_int = str(int(courseID))

            courseID = "{:05d}".format(int(courseID_int))
            courseID = courseID[:2] + "-" + courseID[2:]

            course_info = None

            if courseID in spring_courses["courses"]:
                course_info = spring_courses["courses"][courseID]

            elif courseID in fall_courses["courses"]:
                course_info = fall_courses["courses"][courseID]

            if course_info is None:
                if mega:
                    await ctx.channel.send("Course description not found")
                else:
                    await ctx.channel.send("Course not found")
                return

            instructors = []
            for l in course_info["lectures"]:
                instructors += [" ".join(x.split(", ")[::-1]) for x in l["instructors"]]

            instructors = list(set(instructors))
            instructors = "; ".join(instructors)

            title = course_info["name"]
            department = course_info["department"]
            units = course_info["units"]
            description = course_info["desc"]
            prereqs = course_info["prereqs"]

            coreqs = ""
            if course_info['coreqs'] != None:
                coreqs = '\n**Coreqs**: {}'.format(course_info['coreqs'])

            embed = discord.Embed(title="__**{}**__ ({} units)".format(title, units), colour=discord.Colour(0x319C2C), description=
            '**{}**\n{}\n\n**Prereqs:** {}{}\n**Instructors:** {}'.format(department, description, prereqs, coreqs, instructors))
            await ctx.channel.send(embed=embed)

        else:
            await ctx.channel.send("Invalid arguments - please specify the course ID (e.g. \"course 15150\")")

    @commands.command()
    async def fce_verbose(self, ctx, course, mega=False):
        await self.fce(ctx, course, mega=mega, is_verbose=True)


    """
        Get course hours-per-week
    """
    @commands.command()
    async def fce(self, ctx, *courses, mega=False, is_verbose=False):
        INTERP_MINIS = [76106, 76107, 76108]

        course_ids = []
        funny_possible = {"RELATIONSHIP": 6.9, "CRUSH": 4.3, "PLATONICCRUSH": 32, "ROMANTICSTUDYBUDDY": -5, "ENE": 25.41, "SIMPING": 72}
        funny = []
        for c in courses:
            if c.upper() in funny_possible:
                funny.append(c.upper())
            elif is_valid_course(c):
                courseID = c.replace("-", "")
                courseID_int = str(int(courseID))

                courseID = "{:05d}".format(int(courseID_int))
                #courseID = courseID[:2] + "-" + courseID[2:]

                if courseID not in course_ids:
                    course_ids.append(courseID)
            else:
                await ctx.channel.send("Invalid arguments - please specify the course IDs (e.g. \"fce 18100\" or \"fce 15122 15151 21241\")")
                return

        allRows = []
        for courseID in course_ids:
            print(courseID)
            year = "invalid"
            semester = "test"
            courseList = []
            sameSemList = []
            for row in fce_data:
                if row[0] != year or row[1] != semester:
                    if len(sameSemList) != 0:
                        courseList.append(sameSemList)
                    sameSemList = []
                    year = row[0]
                    semester = row[1]
                if str(row[4]) == str((courseID)):
                    sameSemList.append(row)
                    print("ROW", row)

            if len(sameSemList) != 0:
                courseList.append(sameSemList)
            allRows.append(courseList)

        numSemesters = 2999
        newRows = [[row for i, sameSemList in enumerate(courseList) for row in sameSemList if i < numSemesters] for courseList in allRows]

        cname = ""

        # adds up the FCE's
        invalid = False
        notfound = []
        totalFCEs = []
        for i, rows in enumerate(newRows):
            totalFCE = 0
            count = 0
            for row in rows:
                if not math.isnan(row[12]):
                    totalFCE += float(row[12])
                    count += 1
            if count == 0:
                notfound.append(course_ids[i])
                invalid = True
                totalFCEs.append(None)
            else:
                totalFCEs.append(np.around(totalFCE / count, 1))

        string = "".join(["**{}** ({}) = **{} hours/week**\n".format(course_ids[i][:2]+"-"+course_ids[i][2:], newRows[i][0][7], totalFCEs[i]) for i in range(len(newRows)) if totalFCEs[i] is not None])

        actual_fces = [x for x in totalFCEs if x is not None]

        for x in funny:
            string += "**{}** = **{} hours/week**\n".format(x, funny_possible[x])
            actual_fces.append(funny_possible[x])

        if is_verbose:
            numsent=0
            if len(notfound) > 0:
                if not mega:
                    await ctx.channel.send("Courses {} not found in database".format(", ".join(notfound)))
                return

            mold = '{0:^%d} | {1:^%d} | {2:^%d} | {3:^%d} | {4:^%d} | {5:^%d} | {6:^%d}\n' % (4, 8, 22, 7, 11, 9, 9)
            docstrings = [mold.format('Year', 'Semester', 'Instructor', '# resp.', 'Total resp.', '% resp.', 'FCE hours')]

            for row in newRows[0]:
                if not math.isnan(row[12]):
                    indices = [0, 1, 6, 10, 9, 11, 12]
                    rowIndices = [row[index] for index in indices]
                    docstrings.append(mold.format(*rowIndices))

            # separates the docstrings into messages
            endstrings = []
            temp = ''
            for docstring in docstrings:
                if len(temp) + len(docstring) <= 1992:
                    temp += docstring
                else:
                    endstrings.append(temp)
                    temp = docstring
            endstrings.append(temp)

            await ctx.channel.send("**{}** ({})".format(course_ids[0][:2]+"-"+course_ids[0][2:], newRows[0][0][7]))
            for s in endstrings:
                if numsent == 2 and ctx.guild is not None:
                    nn = sum(len(x.splitlines()) for x in endstrings[2:])
                    await ctx.channel.send(f"{nn} results truncated. Use this command in a DM with the bot to see all results.")
                    return

                s = s.replace("`", "")
                await ctx.channel.send(f"```{s}```")
                numsent += 1

            return


        if len(actual_fces) > 1:
            interp_str = ""
            if sum([int(x) in INTERP_MINIS for x in course_ids]) == 2:
                mini1, mini2 = [x for x in course_ids if int(x) in INTERP_MINIS]
                interp_str = " (interp minis {} and {} were automatically averaged)".format(mini1[:2]+"-"+mini1[2:], mini2[:2]+"-"+mini2[2:])
                actual_fces = []
                minisum = 0
                for i in range(len(newRows)):
                    if totalFCEs[i] is not None and int(course_ids[i]) not in INTERP_MINIS:
                        actual_fces.append(totalFCEs[i])

                    if int(course_ids[i]) in INTERP_MINIS:
                        minisum += totalFCEs[i]

                actual_fces.append(minisum / 2.0)

            total = np.around(sum(actual_fces), 1)
            if invalid:
                string += "Total FCE = **{} hours / week**{} (excludes {} which {} not found)".format(total, interp_str, ", ".join(notfound), "was" if len(notfound) == 1 else "were")
            else:
                string += "Total FCE = **{} hours / week**{}".format(total, interp_str)

        if len(notfound) > 0:
            if mega:
                await ctx.channel.send("FCEs not found for {}".format(", ".join(notfound)))
                return
            else:
                await ctx.channel.send("Courses {} not found in database".format(", ".join(notfound)))


        await ctx.channel.send(string)

    # zaxioms#2718
    @commands.command()
    async def library(self, ctx, mode="all"):
        mode = mode.lower()
        if mode not in ["all", "open"]:
            await ctx.channel.send("Usage: `&library \"all/open\"`")
            return

        url = "https://cmu.libcal.com/api/1.0/hours/7070,7071,7072?key=f350ce8f5f34fd1cae1ccee509352e59"
        response = urllib.request.urlopen(url)
        libs = json.loads(response.read())
        now = datetime.now(pytz.timezone("America/New_York"))
        date = now.strftime("%Y-%m-%d")
        str_out = ""

        assert len(libs) == 3
        for i in range(3):
            text = ""
            name = ""
            open_ = False
            start = ""
            end = ""

            name = libs[i]["name"]
            if libs[i]["dates"][date]["status"] == "open":
                start = libs[i]["dates"][date]["hours"][0]["from"]
                end = libs[i]["dates"][date]["hours"][0]["to"]

                if isNowInTimePeriod(datetime.strptime(start, "%I:%M%p"),
                                    datetime.strptime(end, "%I:%M%p"),
                                    datetime.strptime(now.strftime("%I:%M%p"), "%I:%M%p")):
                    open_ = True

            if libs[i]["dates"][date]["status"] == "text":
                text = libs[i]["dates"][date]["text"]

            if open_:
                str_out += "+ " +name + " (Today's Hours: " + start + " - " + end + ")"
                str_out += "\n\n"
            elif not open_ and mode == "all" and text == "":
                str_out += "- " + name + " (closed)"
                str_out += "\n\n"

            elif not open_ and mode == "all" and text != "":
                str_out += "- " + name + " (" + text + ")"
                str_out += "\n\n"

        if len(str_out.strip()) < 2:
            await ctx.channel.send("No open libraries")
        else:
            str_out = "```diff\n" + str_out[:-1] + "```"
            await ctx.channel.send(str_out)

    @commands.command()
    async def nom(self, ctx, mode="all", url=None):
        await self.dining(ctx, mode, url)

    @commands.command()
    async def dining(self, ctx, mode="all", url=None):
        mode = mode.lower()
        if mode not in ["all", "verbose", "open", "today"]:
            await ctx.channel.send("Usage: `&dining \"all/verbose/open/today\"`")
            return

        OPEN_ONLY = (mode == "open")
        TODAY_ONLY = (mode == "today")
        INCLUDE_DESC = (mode == "verbose")

        def first_item(x):
            assert len(x) == 1
            return x[0]

        if url is None:
            DINING_URL = "https://apps.studentaffairs.cmu.edu/dining/conceptinfo/?page=listConcepts"
        else:
            DINING_URL = "https://web.archive.org/web/{}/https://apps.studentaffairs.cmu.edu/dining/conceptinfo/?page=listConcepts".format(url)

        html = requests.get(DINING_URL).text
        soup = BeautifulSoup(html, "html.parser")

        cards_div = first_item(soup.body.find_all(**{"class": "conceptCards"}))

        cards = cards_div.find_all(**{"class": "card"})
        print("Locations", len(cards))

        locations = []

        for card in cards:
            title_div = first_item(card.find_all(**{"class": "name"}))
            name = title_div.get_text().strip()
            link = title_div.get("onclick").split("'")[1]

            hours_locations_div = first_item(card.find_all(**{"class": "hoursLocations"}))
            location_div, hours_div, _ = hours_locations_div.find_all("div")
            assert "Location:" in location_div.text
            location_a = first_item(location_div.find_all("a"))
            location = location_a.text.strip()
            location_link = location_a.get("href")

            hours = " ".join(hours_div.text.split())
            hours = hours.replace(" • show week", "")

            description_div = first_item(card.find_all(**{"class": "description"}))
            description = " ".join(description_div.text.split())

            status_div = first_item(card.find_all(**{"class": "status"}))
            status = " ".join(status_div.text.split())

            locations.append({
                "name": name,
                "link": link,
                "location": location,
                "location_link": location_link,
                "hours": hours,
                "description": description,
                "open": "open" in status.lower()
            })

        MAX_LEN = 1600

        out_arr = []
        out = ""
        for loc in locations:
            cur = ""
            if OPEN_ONLY and not loc["open"]:
                continue

            if TODAY_ONLY and "Closed today" in loc['hours']:
                continue

            pre = "+" if loc["open"] else "-"
            hours = loc['hours']
            cur += f"{pre} {loc['name']} ({hours})\n"

            if INCLUDE_DESC: cur += f"{pre}     {loc['description']}\n"
            cur += f"{pre}     {loc['location']}\n"
            cur += "\n"

            if len(out) + len(cur) > MAX_LEN:
                out_arr.append(out.strip())
                out = cur
            else:
                out += cur

        if len(out.strip()) > 0:
            out_arr.append(out.strip())

        # Format as diff to get coloring
        # (+)green / (-)red
        for x in out_arr:
            await ctx.channel.send("```diff\n{}\n```".format(x.replace("`", "")))

