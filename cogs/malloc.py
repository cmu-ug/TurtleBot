# this entire thing was for a single joke fwiw
import discord
from discord.ext import commands
from discord import Embed
import json
import asyncio
import numpy as np
import pickle
import time

try:
    with open("data/malloc.pkl", "rb") as f:
        data = pickle.load(f)
except:
    data = [{"ptr": 0, "size": 8, "allocated": False, "owner": 0}]

def align(size):
    ALIGN_BYTES = 8
    while (size % ALIGN_BYTES) > 0:
        size += 1

    return size

def cleanup_cache():
    global data

    i = 0
    while i < len(data):
        # Combine contiguous sections
        if not data[i]["allocated"]:
            while ((i + 1) < len(data)) and (not data[(i + 1)]["allocated"]):
                data[i]["size"] += data[i+1]["size"]
                data.remove(data[i+1])

        i += 1

    # Verify consistency
    prev_ptr = 0
    for x in data:
        if prev_ptr != x["ptr"]:
            print("something bad happened ", x["ptr"])

        prev_ptr = x["ptr"] + x["size"]

def cachesize():
    global data

    return data[-1]["ptr"] + data[-1]["size"]

def save_cache():
    global data
    with open("data/malloc.pkl", "wb+") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

class Malloc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last = {}

    lock = asyncio.Lock()

    @commands.command()
    async def heapsize(self, ctx):
        await ctx.channel.send("0x{:08X}".format(cachesize()))

    @commands.command()
    async def malloc(self, ctx, size: str = None):
        global data

        if time.time() - self.last.get(ctx.author.id, 0) < 2:
            await ctx.channel.send("You are being rate limited")
            return

        self.last[ctx.author.id] = time.time()

        try:
            size = int(size, 0)
            if size < 1 or size > (16 * 1024 * 1024):
                await ctx.channel.send("Error: Size must be a positive integer less than 16777216 (16MB)")
                return

            if (cachesize() + size) > (2 * 1024 * 1024 * 1024 * 1024 * 1024):
                await ctx.channel.send("Error: Out of memory")
                return

            size = align(size)
        except:
            await ctx.channel.send("Error: Invalid size")
            return

        cleanup_cache()

        # Find place to allocate
        done = False
        m_ptr = 0
        for i, x in enumerate(data):
            if (x["size"] >= size) and (not x["allocated"]):
                if x["size"] > size:
                    data.insert(i + 1, {"allocated": False, "size": x["size"] - size, "ptr": x["ptr"] + size, "owner": 0})

                m_ptr = x["ptr"]
                data[i]["size"] = size
                data[i]["allocated"] = True
                data[i]["owner"] = ctx.author.id
                done = True
                break

        if not done:
            if not data[-1]["allocated"]:
                m_ptr = data[-1]["ptr"]
                data[-1]["size"] = size
                data[-1]["allocated"] = True
                data[-1]["owner"] = ctx.author.id

            else:
                m_ptr = cachesize()
                data.append({"allocated": True, "size": size, "ptr": m_ptr, "owner": ctx.author.id})

        cleanup_cache()
        save_cache()

        await ctx.channel.send("0x{:08X}".format(m_ptr))

    @commands.command()
    async def free(self, ctx, ptr: str = None):
        global data

        try:
            ptr = int(ptr, 0)
        except:
            await ctx.channel.send("Error: Invalid pointer")
            return

        done = False
        for i, x in enumerate(data):
            if x["ptr"] == ptr:
                done = True
                if (x["owner"] == ctx.author.id) or (x["owner"] == 0):
                    await ctx.channel.send("Freed")
                    data[i]["allocated"] = False
                else:
                    await ctx.channel.send("Error: Not your memory")
                break

        if not done:
            await ctx.channel.send("Error: Invalid pointer")

        cleanup_cache()
        save_cache()


