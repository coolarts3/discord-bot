import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import imageio_ffmpeg as ffmpeg
import pytz  # Para manejar zona horaria

SPOTIFY_CLIENT_ID = "1e5de19a89e2457aa31ddf0f2cad11b6"
SPOTIFY_CLIENT_SECRET = "d5c34f121bf4417a8071516e5447cdbf"

# Configuración de Spotify
spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

intents = discord.Intents.default()
intents.messages = True
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Define tu zona horaria
TZ = pytz.timezone("Europe/Madrid")

def dentro_de_horario():
    ahora = datetime.now(TZ).time()
    hora_inicio = time(7, 0)   # 07:00 AM
    hora_fin = time(0, 0)      # Medianoche
    # Si la hora actual está entre medianoche y 07:00 → fuera de servicio
    if ahora >= hora_inicio or ahora < hora_fin:
        return True  # Activo
    else:
        return False  # Inactivo

import os
print("Ruta absoluta:", os.path.abspath('cookies.txt'))
print("¿Existe el archivo?", os.path.exists('cookies.txt'))

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
async def play(ctx, *, query):
    ydl_opts = {
        'format': 'bestaudio',
        'cookiefile': 'cookies.txt',  # tu archivo de cookies
    }
    """Busca la canción en Spotify y la reproduce en Discord"""
    # Buscar la canción en Spotify
    results = spotify.search(q=query, type="track", limit=1)
    if not results['tracks']['items']:
        await ctx.send("No encontré la canción en Spotify.")
        return

    track = results['tracks']['items'][0]
    song_name = track['name']
    artist = track['artists'][0]['name']
    await ctx.send(f"Buscando y reproduciendo: {song_name} de {artist}")

    # Buscar la misma canción en YouTube
    search_query = f"{song_name} {artist} audio"
    ydl_opts = {'format': 'bestaudio', 'noplaylist': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{search_query}", download=False)['entries'][0]
        url = info['url']

    # Conectarse al canal de voz y reproducir
    if ctx.author.voice:
        voice_channel = ctx.author.voice.channel
        vc = await voice_channel.connect()
        vc.play(discord.FFmpegPCMAudio(url, executable=FFMPEG_PATH))
    else:
        await ctx.send("Necesitas estar en un canal de voz para reproducir música.")

# Comando para desconectarse
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Me he desconectado del canal de voz.")
    else:
        await ctx.send("No estoy conectado a ningún canal de voz.")
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


















