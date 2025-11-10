import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL
import os
import imageio_ffmpeg as ffmpeg

ffmpeg_path = ffmpeg.get_ffmpeg_exe()
print("FFmpeg path:", ffmpeg_path)

# Intents necesarios
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------------------
# EVENTO DE BIENVENIDA
# ----------------------------
@bot.event
async def on_member_join(member):
    channel_id = 1437186906780860560  # Reemplaza con la ID de tu canal
    channel = bot.get_channel(channel_id)
    if channel:
        embed = discord.Embed(
            title="🎉 ¡𝓑𝓘𝓔𝓝𝓥𝓔𝓝𝓘𝓓𝓞 𝓐 𝓛𝓞𝓢 𝓒𝓗𝓐𝓒𝓐𝓛𝓘𝓣𝓞𝓢! 🎉",
            description=f"𝕄𝕌𝕐 𝔹𝕌𝔼ℕ𝔸𝕊 {member.mention}, 𝔹𝕀𝔼ℕ𝕍𝔼ℕ𝕀𝔻𝕆 𝔸 **{member.guild.name}** 𝕃𝔼𝔼 𝕃𝔸𝕊 ℕ𝕆ℝ𝕄𝔸𝕊 𝕐 𝕍𝔼ℝ𝕀𝔽Íℂ𝔸𝕋𝔼 𝔼ℕ <#1436710363881275402> 👋",
            color=discord.Color.red()
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/1436710363881275405/1437200246424862893/anime-banner-gif-file-2065kb-kmtu01zw6scfqjwu.gif?ex=69126088&is=69110f08&hm=82a0a1335b3067c8ee5e45ea78e0b7eadd7aebe0b0000c85e7d72100d17a466f&")
        embed.set_thumbnail(url=member.display_avatar.url)
        await channel.send(embed=embed)

# ----------------------------
# COMANDO DE MÚSICA
# ----------------------------
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await channel.connect()
            await ctx.send(f"✅ Me he unido al canal: {channel.name}")
        else:
            await ctx.send("Ya estoy en un canal de voz.")
    else:
        await ctx.send("❌ Debes estar en un canal de voz primero.")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Me he desconectado del canal de voz.")
    else:
        await ctx.send("❌ No estoy conectado a ningún canal de voz.")

@bot.command()
async def play(ctx, url: str):
    if ctx.author.voice is None:
        await ctx.send("❌ Debes estar en un canal de voz primero.")
        return

    channel = ctx.author.voice.channel

    # Conectarse al canal
    if ctx.voice_client is None:
        vc = await channel.connect()
    else:
        vc = ctx.voice_client

    # Opciones de yt-dlp
    ydl_opts = {
    'format': 'bestaudio',
    'cookiefile': 'cookies.txt',  # Exportadas desde tu navegador
}

    # Extraer audio con manejo de errores
    try:
        from yt_dlp import YoutubeDL
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
    except Exception as e:
        await ctx.send(f"❌ No se pudo reproducir el video: {e}")
        return

    # Reproducir el audio
    if vc.is_playing():
        vc.stop()
    vc.play(discord.FFmpegPCMAudio(audio_url), after=lambda e: print(f"Fin de la canción: {e}"))
    await ctx.send(f"▶️ Reproduciendo: {info['title']}")

# ----------------------------
# COMANDOS DE MODERACIÓN
# ----------------------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"👢 {member} ha sido expulsado. Motivo: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"🔨 {member} ha sido baneado. Motivo: {reason}")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def limpiar(ctx, cantidad: int):
    deleted = await ctx.channel.purge(limit=cantidad)
    await ctx.send(f"🧹 Se han borrado {len(deleted)} mensajes.", delete_after=5)

# ----------------------------
# COMANDO DE AVISO
# ----------------------------
@bot.command()
@commands.has_permissions(administrator=True)
async def aviso(ctx, *, mensaje):
    # Borra el último mensaje de aviso enviado por el bot
    async for msg in ctx.channel.history(limit=100):
        if msg.author == bot.user and msg.embeds:
            await msg.delete()
            break

    embed = discord.Embed(
        title="📢 Aviso del Staff",
        description=mensaje,
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

# ----------------------------
# INICIAR BOT
# ----------------------------
bot.run(os.getenv("DISCORD_TOKEN"))








