import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="?", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    
# --- Evento cuando el bot está listo ---
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

# --- Comando para unirse al canal de voz ---
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"Me he unido al canal: {channel.name}")
    else:
        await ctx.send("❌ Debes estar en un canal de voz primero.")

# --- Comando para reproducir música desde URL de YouTube ---
@bot.command()
async def play(ctx, url: str):
    if ctx.voice_client is None:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
        else:
            await ctx.send("❌ Debes estar en un canal de voz primero.")
            return

    vc = ctx.voice_client

    # Usa FFmpeg para reproducir la URL
    vc.stop()
    vc.play(discord.FFmpegPCMAudio(source=url), after=lambda e: print(f'Fin de la canción: {e}'))
    await ctx.send(f"▶️ Reproduciendo: {url}")

# --- Comando para desconectarse ---
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Me he desconectado del canal de voz.")
    else:
        await ctx.send("❌ No estoy conectado a ningún canal de voz.")

# --- Mensaje de bienvenida ---
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="bienvenida")  # Cambia el nombre al canal que quieras
    if channel:
        embed = discord.Embed(
            title="🎉 ¡Bienvenido!",
            description=f"Hola {member.mention}, bienvenido a **{member.guild.name}** 👋",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=member.avatar.url)  # Foto de perfil del usuario
        await channel.send(embed=embed)

# --- Comando de aviso ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def aviso(ctx, *, mensaje):
    embed = discord.Embed(
        title="📢 Aviso del Staff",
        description=mensaje,
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

# --- Moderación ---
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No especificado"):
    await member.kick(reason=reason)
    await ctx.send(f"👢 {member} ha sido expulsado. Motivo: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No especificado"):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member} ha sido baneado. Motivo: {reason}")

# --- Ejecutar bot ---
import os
bot.run(os.getenv("DISCORD_TOKEN"))



