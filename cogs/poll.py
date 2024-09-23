import discord
from discord.ext import tasks, commands
import pickle
import string
import asyncio

"""
Format:
{
    server: {
        polls: {
            pollId: {
                channel: channelId,
                message: messageId,
                question: <question>,
                responses: {A: <opt>, B: <opt>},
                user_responses: {userId: response(s)},
                anon: True/False,
                multi: True/False,
                requester: name,
                requester_id: userId
            },
        },
        channel: channelId or 0
    }
}
"""
poll_history = {}

LOWERCASE = string.ascii_lowercase

def load_history():
    global poll_history
    try:
        with open("data/poll_history.pkl", "rb") as f:
            poll_history = pickle.load(f)
    except:
        poll_history = {}

def save_history():
    global poll_history
    with open("data/poll_history.pkl", "wb+") as f:
        pickle.dump(poll_history, f, protocol=pickle.HIGHEST_PROTOCOL)

def get_poll_by_message(server_id, message_id):
    server = poll_history[server_id]["polls"]
    for poll_id in server:
        if server[poll_id]["message"] == message_id:
            return poll_id

    return None

def get_emoji(letter):
    return str(chr(0x0001F1E6 + LOWERCASE.index(letter)))

def get_letter(emoji):
    if emoji is None:
        return None
    try:
        if isinstance(emoji, str):
            unicode = ord(emoji[0]) - 0x0001F1E6
            if unicode >= 0 and unicode < 26:
                return LOWERCASE[unicode]
        else:
            name = emoji.name
            if len(name) == 1:
                unicode = ord(name[0]) - 0x0001F1E6
                if unicode >= 0 and unicode < 26:
                    return LOWERCASE[unicode]
    except:
        pass

    return None

"""
    Check if the server is in the database and add it if not
"""
def check_server(ctx):
    if ctx.message.guild.id not in poll_history:
        poll_history[ctx.message.guild.id] = {"polls": {}, "channel": 0}

class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        load_history()

        self.update_all.start()

    """
        Check if the server is in the database and add it if not
    """
    def check_server(self, ctx):
        if ctx.message.guild.id not in poll_history:
            poll_history[ctx.message.guild.id] = {"polls": {}, "channel": 0}

    """
        Check and update poll responses for all past polls
    """
    @tasks.loop(seconds=120.0, count=1)
    async def update_all(self):
        print("Updating all")
        for server_id, server in poll_history.items():
            for poll_id, poll in server["polls"].items():
                asyncio.ensure_future(self.update_poll_responses(server_id, poll_id))
                await asyncio.sleep(0.1)


    """
        Wait until bot is ready before starting loop
    """
    @update_all.before_loop
    async def before_update_all(self):
        await self.bot.wait_until_ready()

    """
        Verify that bot response emoji have not been removed.
        Detect user responses and update result tally, updating embed if needed.
    """
    update_responses_lock = asyncio.Lock()

    async def update_poll_responses(self, server_id, poll_id, priority_emoji=None):
        async with self.update_responses_lock:
            poll = poll_history[server_id]["polls"][poll_id]

            # Get the server, channel, and message
            server = self.bot.get_guild(server_id)
            channel_id = poll["channel"]
            channel = server.get_channel(channel_id)
            message = await channel.fetch_message(poll["message"])

            # Ensure bot responses were not removed
            #for letter, response in poll["responses"].items():
            #    asyncio.ensure_future(message.add_reaction(get_emoji(letter)))

            anon = poll["anon"]
            multi = poll["multi"]

            # Check if anything has changed
            changed = False


            if anon:
                for reaction in message.reactions:
                    letter = get_letter(reaction.emoji)
                    if letter not in poll["responses"]:
                        continue

                    users = [user async for user in reaction.users()]

                    for user in users:
                        # Ignore bot reactions
                        if user.bot:
                            continue

                        poll["user_responses"][user.id] = letter
                        await message.remove_reaction(reaction.emoji, user)

            elif multi:
                # Clear responses (automatically handles removed-emojis this way)
                poll["user_responses"] = {}
                for reaction in message.reactions:
                    letter = get_letter(reaction.emoji)
                    if letter not in poll["responses"]:
                        continue

                    users = [user async for user in reaction.users()]

                    for user in users:
                        # Ignore bot reactions
                        if user.bot:
                            continue

                        if user.id not in poll["user_responses"]:
                            poll["user_responses"][user.id] = []

                        poll["user_responses"][user.id].append(letter)

            else: # Single-response poll
                # Clear responses (automatically handles removed-emojis this way)
                poll["user_responses"] = {}
                for reaction in sorted(message.reactions, key=lambda x: 0 if (get_letter(x.emoji) == get_letter(priority_emoji)) else 100):
                    letter = get_letter(reaction.emoji)
                    if letter not in poll["responses"]:
                        continue

                    users = [user async for user in reaction.users()]

                    for user in users:
                        # Ignore bot reactions
                        if user.bot:
                            continue

                        if user.id not in poll["user_responses"]:
                            poll["user_responses"][user.id] = letter
                        else:
                            await message.remove_reaction(reaction.emoji, user)


            poll_history[server_id]["polls"][poll_id] = poll

            await self.update_poll_embed(server_id, poll_id)
            #print("updated")

            save_history()

    """
        Update the embed message for the given poll
    """
    async def update_poll_embed(self, server_id, poll_id):
        poll = poll_history[server_id]["polls"][poll_id]

        # Get the server, channel, and message
        server = self.bot.get_guild(server_id)
        channel_id = poll["channel"]
        channel = server.get_channel(channel_id)
        message = await channel.fetch_message(poll["message"])

        embed = self.create_poll_embed(poll_id, poll)
        await message.edit(embed=embed)


    """
        Create an Embed showing the contents and results of a poll
    """
    def create_poll_embed(self, poll_id, poll):

        # Inform user if poll is anonymous or multi-response
        info = ""

        if poll["anon"]:
            info = "(Your reaction will be deleted but your response will be saved)"
        elif poll["multi"]:
            info = "(Multiple responses are allowed)"

        poll_content = f"{poll['question']}\n{info}\n"

        for letter, response in poll["responses"].items():
            count = 0

            # Tally responses 
            for user_id in poll["user_responses"]:
                r = poll["user_responses"][user_id]

                if poll["multi"] and (letter in r):
                    count += 1
                elif (not poll["multi"]) and (letter == r):
                    count += 1

            poll_content += f"{get_emoji(letter)} {response} ({count})\n"


        embed = discord.Embed(title=f"__**Poll #{poll_id}**__ {'(Anonymous)' if poll['anon'] else ''}",
                              colour=discord.Colour(0xA6192E),
                              description=poll_content)

        embed.set_footer(text=f"Requested by {poll['requester']}")

        return embed

    async def create_poll(self, ctx, args, anon=False, multi=False):
        if len(args) < 3:
            await self.pollhelp(ctx)
            return

        if len(args) > 21:
            await ctx.channel.send("Maximum 20 options are allowed. Please add quotes around each option if it contains spaces.")
            return

        self.check_server(ctx)

        if len(poll_history[ctx.message.guild.id]["polls"].keys()) == 0:
            poll_id = 1
        else:
            poll_id = max(poll_history[ctx.message.guild.id]["polls"].keys()) + 1

        question = args[0]
        responses = [r for r in args[1:]]

        # Add a letter to each response
        responses = [(LOWERCASE[i], r) for i, r in enumerate(responses)]

        channel = ctx.message.guild.get_channel(poll_history[ctx.message.guild.id]["channel"])

        if channel is None:
            channel = ctx.channel

        poll = {
            "question": question,
            "responses": dict(responses),
            "user_responses": {},
            "anon": anon,
            "multi": multi,
            "requester_id": ctx.message.author.id,
            "requester": ctx.message.author.name,
            "channel": channel.id
        }

        embed = self.create_poll_embed(poll_id, poll)

        message = (await channel.send(embed=embed))

        if channel != ctx.channel:
            await ctx.channel.send(f"Created poll #{poll_id} in {channel.mention}")

        poll["message"] = message.id

        for letter, response in responses:
            await message.add_reaction(get_emoji(letter))

        poll_history[ctx.message.guild.id]["polls"][poll_id] = poll

        save_history()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, data):
        if data.user_id == self.bot.user.id:
            return

        poll_id = get_poll_by_message(data.guild_id, data.message_id)

        if poll_id is not None:
            await self.update_poll_responses(data.guild_id, poll_id, priority_emoji=data.emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, data):
        if data.user_id == self.bot.user.id:
            return

        poll_id = get_poll_by_message(data.guild_id, data.message_id)

        if poll_id is not None:
            await self.update_poll_responses(data.guild_id, poll_id)

    @commands.command()
    async def pollhelp(self, ctx):
        info = "`poll \"question\" \"response 1\" \"response 2\" ...` - Create a poll where each user can select only one response.\n\n" +  "`pollmulti \"question\" \"response 1\" \"response 2\" ...` - Create a poll where each user can select multiple responses.\n\n" + "`pollanon \"question\" \"response 1\" \"response 2\" ...` - Create an anonymous poll.\n\n" + "`deletepoll <Poll Number>` - Delete a past poll"

        embed = discord.Embed(title="__**Poll Usage**__",
                              colour=discord.Colour(0xA6192E),
                              description=info)

        await ctx.channel.send(embed=embed)

    @commands.command()
    async def deletepoll(self, ctx, poll_id: int=-1):
        if poll_id == -1:
            await ctx.channel.send("Usage: `deletepoll <Poll Number>`")
            return

        if poll_id not in poll_history[ctx.message.guild.id]["polls"]:
            await ctx.channel.send("Poll does not exist.")
            return

        poll = poll_history[ctx.message.guild.id]["polls"][poll_id]

        if poll["requester_id"] != ctx.message.author.id:
            await ctx.channel.send("Only the creator of a poll may delete it.")
            return

        # Get the server, channel, and message
        server = self.bot.get_guild(ctx.message.guild.id)
        channel_id = poll["channel"]
        channel = server.get_channel(channel_id)
        message = await channel.fetch_message(poll["message"])

        await message.delete()
        await ctx.channel.send(f"Poll #{poll_id} successfully deleted")

    @commands.command()
    async def pkill(self, ctx, sid: int=-1, pid: int=-1):
        if ctx.message.author.id != 347518645695414282:
            await ctx.channel.send("NO PERMS")
            return

        server = sid
        poll_id = pid
        if poll_id == -1:
            return

        if poll_id not in poll_history[server]["polls"]:
            await ctx.channel.send("Poll does not exist.")
            return

        poll = poll_history[server]["polls"][poll_id]

        # Get the server, channel, and message
        server = self.bot.get_guild(server)
        channel_id = poll["channel"]
        channel = server.get_channel(channel_id)
        message = await channel.fetch_message(poll["message"])

        await message.delete()
        await ctx.channel.send(f"Killed #{poll_id}")

    @commands.command()
    async def poll(self, ctx, *args):
        await self.create_poll(ctx, args, anon=False, multi=False)

    @commands.command()
    async def pollmulti(self, ctx, *args):
        await self.create_poll(ctx, args, anon=False, multi=True)

    @commands.command()
    async def pollanon(self, ctx, *args):
        await self.create_poll(ctx, args, anon=True, multi=False)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def pollchannel(self, ctx, channel: discord.TextChannel=None):
        """if channel == None:
            await ctx.channel.send("Usage: pollchannel <#channel>")
            return"""

        self.check_server(ctx)

        if channel is None:
            poll_history[ctx.message.guild.id]["channel"] = 0
            await ctx.channel.send("Reset poll channel (polls will now be sent in the channel they were requested in)")
        else:
            poll_history[ctx.message.guild.id]["channel"] = channel.id
            await ctx.channel.send("Set poll channel to **{}**".format(channel.name))

        save_history()



