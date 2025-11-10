import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import asyncio
import imageio_ffmpeg as ffmpeg

SPOTIFY_CLIENT_ID = "1e5de19a89e2457aa31ddf0f2cad11b6"
SPOTIFY_CLIENT_SECRET = "d5c34f121bf4417a8071516e5447cdbf"

# Configuración de Spotify
spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

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
# Menú de selección de roles
# ----------------------------
class RoleSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="💻 PC", description="Jugador de PC", value="PC"),
            discord.SelectOption(label="🎮 PlayStation", description="Jugador de PlayStation", value="PlayStation"),
            discord.SelectOption(label="🕹️ Xbox", description="Jugador de Xbox", value="Xbox"),
        ]
        super().__init__(placeholder="Elige tu plataforma 🎮", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        role_name = self.values[0]
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=role_name)

        if not role:
            await interaction.response.send_message(f"❌ No se encontró el rol **{role_name}**.", ephemeral=True)
            return

        # Quitar roles anteriores
        for r_name in ["PC", "PlayStation", "Xbox"]:
            r = discord.utils.get(interaction.user.roles, name=r_name)
            if r and r != role:
                await interaction.user.remove_roles(r)

        # Asignar el rol seleccionado
        await interaction.user.add_roles(role)
        await interaction.response.send_message(f"✅ Rol **{role_name}** asignado correctamente.", ephemeral=True)

        # Borrar el canal temporal
        await interaction.channel.delete(reason="Usuario terminó de seleccionar su rol")

class RoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleSelect())

# ----------------------------
# Crear canal temporal automáticamente
# ----------------------------
@bot.event
async def on_member_join(member):
    guild = member.guild

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    try:
        temp_channel = await guild.create_text_channel(
            name=f"roles-{member.name}",
            overwrites=overwrites,
            reason="Canal temporal de selección de roles"
        )
    except discord.Forbidden:
        print(f"❌ No tengo permisos para crear el canal en {guild.name}")
        return
    except discord.HTTPException as e:
        print(f"❌ Error creando canal: {e}")
        return

    embed = discord.Embed(
        title="🎮 Selección de Roles",
        description="¡Bienvenido! Elige tu plataforma en el menú de abajo para obtener tu rol.",
        color=discord.Color.blue()
    )
    await temp_channel.send(embed=embed, view=RoleView())

# ----------------------------
# CREAR CANAL DE VOZ PARTIDA
# ----------------------------
CANAL_PERMITIDO_ID = 1437551679770857542  # cambia por el tuyo

# 🎮 Crear partida (solo en un canal específico)
@bot.command()
async def crearpartida(ctx):
    if ctx.channel.id != CANAL_PERMITIDO_ID:
        await ctx.send(f"❌ Este comando solo se puede usar en <#{CANAL_PERMITIDO_ID}>.", delete_after=5)
        return

    # 🧹 Borrar mensaje del comando
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    guild = ctx.guild
    categoria = discord.utils.get(guild.categories, name="𝓟𝓐𝓡𝓣𝓘𝓓𝓐𝓢 🖱️")

    # Crear canales temporales
    voice_channel = await guild.create_voice_channel(
        name=f"🎮│Partida de {ctx.author.name}",
        category=categoria,
        user_limit=5
    )
    text_channel = await guild.create_text_channel(
        name=f"💬│chat-{ctx.author.name}",
        category=categoria
    )

    # Permisos personalizados
    await voice_channel.set_permissions(ctx.author, connect=True, manage_channels=True)
    await text_channel.set_permissions(ctx.author, send_messages=True, read_messages=True)

    await ctx.send(
        f"✅ {ctx.author.mention}, se han creado tus canales temporales:\n"
        f"🎧 {voice_channel.mention}\n💬 {text_channel.mention}"
    )

    # Autoeliminar cuando quede vacío
    while True:
        await asyncio.sleep(10)
        if len(voice_channel.members) == 0:
            await text_channel.delete()
            await voice_channel.delete()
            print(f"🗑️ Canales de {ctx.author.name} eliminados automáticamente.")
            break
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
    """Busca la canción en Spotify y la reproduce en Discord"""

    # Configuración de yt-dlp (cookies + formato + opciones)
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'cookiefile': './cookies.txt',  # asegúrate de que esté en la raíz del proyecto
        'noplaylist': True,
        'source_address': '0.0.0.0'
    }

    # Buscar la canción en Spotify
    results = spotify.search(q=query, type="track", limit=1)
    if not results['tracks']['items']:
        await ctx.send("No encontré la canción en Spotify.")
        return

    track = results['tracks']['items'][0]
    song_name = track['name']
    artist = track['artists'][0]['name']
    await ctx.send(f"🎶 Buscando y reproduciendo: **{song_name}** de **{artist}**")

    # Buscar la misma canción en YouTube
    search_query = f"{song_name} {artist} audio"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_results = ydl.extract_info(f"ytsearch:{search_query}", download=False)
        info = search_results['entries'][0]
        url = info['url']

    # Conectarse al canal de voz y reproducir
    if ctx.author.voice:
        voice_channel = ctx.author.voice.channel
        vc = await voice_channel.connect()
        vc.play(discord.FFmpegPCMAudio(url, executable=ffmpeg_path))
    else:
        await ctx.send("⚠️ Necesitas estar en un canal de voz para reproducir música.")

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


























