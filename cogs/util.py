import discord
from utils import admin_only
from discord.ext import commands as cmds
import re
import string
import boolean # BOOLEANPY - https://github.com/pauleve/boolean.py

algebra = boolean.BooleanAlgebra()

class Util(cmds.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cmds.command()
    async def ping(self, ctx):
        await ctx.channel.send("Pong!")

    @cmds.command()
    async def bestpokemon(self, ctx):
        await ctx.channel.send("Turtwig is the best pokemon!")

    @cmds.command()
    async def worstpokemon(self, ctx):
        await ctx.channel.send(ctx.author.mention)

    @cmds.command()
    async def invite(self, ctx):
        await ctx.channel.send("https://discordapp.com/oauth2/authorize?client_id=707371467750244404&scope=bot&permissions=8")

    @cmds.command()
    async def nick(self, ctx):
        newname = ctx.message.content.replace("&nick ", "")
        await ctx.message.author.edit(nick=newname)

    @cmds.command()
    @admin_only()
    async def listservers(self, ctx):
        out = ""
        for guild in self.bot.guilds:
            out += f"{guild.id} {guild.name}\n"

        await ctx.channel.send("```"+out+"```")

    @cmds.command()
    async def rolecount(self, ctx):
        await self.roleinfo(ctx, all_verbose=False)

    @cmds.command()
    async def roleinfo_all(self, ctx):
        await self.roleinfo(ctx, show_all=True)

    @cmds.command()
    async def roleinfo2_all(self, ctx):
        await self.roleinfo(ctx, show_all=True, mentions=True)

    @cmds.command()
    async def roleinfo2(self, ctx):
        await self.roleinfo(ctx, mentions=True)

    @cmds.command()
    async def roleinfo(self, ctx, **kwargs):
        message_content = ctx.message.content.strip()

        # Remove the first token and strip the rest
        role_name = " ".join(message_content.split(" ")[1:]).strip()

        # If role_name is empty, ask the user to specify a role
        if not role_name:
            await ctx.channel.send("Please specify a role")
            return

        print(role_name)

        role_map = {}
        role_identifiers = []

        if '"' not in role_name:
            role_name = '"' + role_name + '"'

        role_data = ""
        within_quotes = False
        role_accumulator = ""

        show_all = kwargs.get("show_all", False)
        mentions_enabled = kwargs.get("mentions", False)

        role_presence_map = {}

        role_counter = 0
        for char in role_name:
            if within_quotes:
                if char == '"':
                    role_id = "role{:04x}".format(role_counter)
                    role_data += role_id
                    role_counter += 1
                    if role_accumulator.lower() not in role_map:
                        role_map[role_accumulator.lower()] = []
                    role_map[role_accumulator.lower()].append(role_id)
                    role_presence_map[role_accumulator.lower()] = 0
                    role_identifiers.append(role_id)
                    within_quotes = False
                else:
                    role_accumulator += char
            else:
                if char == '"':
                    within_quotes = True
                    role_accumulator = ""
                else:
                    role_data += char

        if within_quotes:
            await ctx.channel.send("Unclosed quote")

        role_expression = algebra.parse(role_data)

        members_matching_role = []
        async for guild_member in ctx.guild.fetch_members(limit=None):
            member_role_data = role_data
            for role in guild_member.roles:
                role_name_lower = str(role).lower()
                if role_name_lower in role_map:
                    for role_id in role_map[role_name_lower]:
                        role_presence_map[role_name_lower] = 1
                        member_role_data = member_role_data.replace(role_id, "TRUE")

            for role_id in role_identifiers:
                member_role_data = member_role_data.replace(role_id, "FALSE")

            if repr(algebra.parse(member_role_data).simplify()).strip() == "TRUE":
                members_matching_role.append(guild_member)

        if not members_matching_role:
            await ctx.channel.send("No users found")

        invalid_roles = [role for role, present in role_presence_map.items() if not present]

        valid_characters = set(string.ascii_letters + string.digits + " _")
        if invalid_roles:
            for invalid_role in invalid_roles:
                # Clean up invalid roles by only keeping valid characters
                cleaned_role = ''.join(c for c in invalid_role if c in valid_characters)
                await ctx.channel.send(f"Warning: Nobody in server has role {cleaned_role.replace('@', '')}")

        total_members = len(members_matching_role)

        overflow_warning = False
        members_processed = 0
        members_first_batch = 0
        if kwargs.get("all_verbose", True):
            is_first_batch = True
            while members_matching_role:
                message_chunk = ""
                while len(message_chunk) < 1800 and members_matching_role:
                    if mentions_enabled:
                        message_chunk += members_matching_role[0].mention + "   "
                    else:
                        member = members_matching_role[0]
                        message_chunk += f"**{member.display_name}** ({member})\n"
                    members_matching_role = members_matching_role[1:]
                    members_processed += 1

                if is_first_batch:
                    embed = discord.Embed(
                        title=f"__**{role_name.replace('@', '').replace('`', '')}**__",
                        description=f"{total_members} members\n{message_chunk}"
                    )
                else:
                    embed = discord.Embed(
                        title="",
                        description=message_chunk
                    )

                if is_first_batch or show_all:
                    await ctx.channel.send(embed=embed)
                    members_first_batch = members_processed
                elif not overflow_warning:
                    overflow_warning = members_first_batch
                is_first_batch = False
        else:
            embed = discord.Embed(
                title=f"__**{role_name.replace('@', '').replace('`', '')}**__",
                description=f"{total_members} members"
            )
            await ctx.channel.send(embed=embed)

        if overflow_warning:
            await ctx.channel.send(f"Only showing first {overflow_warning} of {total_members} results. "
                                   "Please use `&roleinfo_all` or `&roleinfo2_all` to see all results "
                                   "(Warning, output may span a lot of messages. Please only use it in bot-command channels)")



