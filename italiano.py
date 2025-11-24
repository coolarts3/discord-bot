import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True
bot = commands.Bot(command_prefix="?", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 Bot 2 conectado como {bot.user}")

@bot.command()
async def hola(ctx):
    await ctx.send("👋 Hola, soy el segundo bot.")

import os
bot.run(os.getenv("DISCORD_TOKEN2"))
