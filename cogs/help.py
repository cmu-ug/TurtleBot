import discord
from discord.ext import commands
import re

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        p = "&"
        await ctx.channel.send(f"""
```
Andrew ID:
    {p}register <andrew id> - Register your Andrew ID with the bot to verify yourself.
    {p}is_verified <@user> - Check if a user has verified their Andrew ID

CMU General:
    {p}finger <andrew id> - Look up a user in the CMU directory
    {p}carnegie - My heart is in the work!
    {p}nom - Show on-campus dining locations & hours (alternatively, "{p}nom open" to see only currently-open locations)

CMU Classes:
    {p}syllabus <course id> - CMU course syllabus lookup
    {p}course <course id> - CMU course info lookup
    {p}unlocks <course id> - See all the courses that the given course is a prereq for
    {p}fce <course id 1> <course id 2> ... - Get the average hours/week for one or more courses

Fun:
    {p}consume <@user> - Nom nom nom
    {p}strangle <@user> - SCREM
    {p}pfp <@user> - Get the image from the mentioned user's profile picture
    {p}emote <emote> - Get the image from the given custom emote
    {p}hug <@user> - Hugs!
    {p}love <emoji> - Love!
    {p}regex <word 1> <word 2> - Parsing HTML with regex copypasta
    {p}steal <message id> - Copy the emotes and reactions from the message with the given ID
```
""".strip())

        await ctx.channel.send(f"""
```
Poll:
    {p}poll "question" "response 1" "response 2" ... - Create poll
    {p}pollmulti "question" "response 1" "response 2" ... - Create poll allowing multiple responses
    {p}pollanon "question" "response 1" "response 2" ... - Create poll with anonymous responses
    {p}deletepoll <poll number> - Delete a past poll

Util:
    {p}bestpokemon - Self-explanatory
    {p}roleinfo <role(s)> - Get a list of users with given role or roles
        - example usage: {p}roleinfo ("role1" and "role2") or not "role3"
    {p}rolecount <role(s)> - Get the number of users with given role or roles
```
""".strip())

