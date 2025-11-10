import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- Evento cuando el bot está listo ---
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

# --- Mensaje de bienvenida ---
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="bienvenidas")  # Cambia el nombre al canal que quieras
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


