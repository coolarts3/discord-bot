import discord
from discord.ext import tasks
from discord.ext import commands
from discord import FFmpegPCMAudio
from discord.utils import get
from discord.ui import View, Button, Select, Modal, TextInput
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import asyncio
import imageio_ffmpeg as ffmpeg
from datetime import datetime, timedelta
from datetime import timezone

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


CANAL_AVISO_ID = 1437188675225124874  # reemplaza con tu canal
TIEMPO_ESPERA = 5  # minutos
last_activity = None

# -----------------------------
# Detectar actividad
# -----------------------------
@bot.event
async def on_message(message):
    global last_activity
    if message.author.bot:
        return
    last_activity = datetime.utcnow()
    await bot.process_commands(message)

# -----------------------------
# Tarea que envía avisos solo si hubo actividad
# -----------------------------
@tasks.loop(seconds=30)
async def aviso_automatico():
    global last_activity
    if last_activity is None:
        return  # nada de actividad aún
    tiempo_transcurrido = (datetime.utcnow() - last_activity).total_seconds() / 60
    if tiempo_transcurrido <= TIEMPO_ESPERA:  # solo si hubo actividad reciente
        canal = bot.get_channel(CANAL_AVISO_ID)
        if canal:
            try:
                await canal.send("📢 ¡Recuerda usar `!roles` para asignarte tus roles y configurar tu perfil!")
                print(f"[{datetime.utcnow()}] Aviso enviado en {canal.name}")
            except Exception as e:
                print(f"⚠️ Error al enviar aviso: {e}")

# -----------------------------
# Iniciar la tarea al arrancar
# -----------------------------
@bot.event
async def on_ready():
    print(f"🤖 Bot conectado como {bot.user}")

    await publicar_panel_llamadas()

    # Iniciar tu sistema de avisos automático
    if not aviso_automatico.is_running():
        aviso_automatico.start()

    # Iniciar los avisos de actividad en voz
    if not avisos_voz_periodicos.is_running():
        avisos_voz_periodicos.start()

    # Comprobar si ya había gente conectada a voz
    await comprobar_voz_al_iniciar()

@bot.event
async def on_message(message):
    global last_activity

    if message.author.bot:
        return

    last_activity = datetime.utcnow()
    await bot.process_commands(message)

#ELIMINACION DE MENSAJES NO COMANDOS    

@bot.event
async def on_message(message):
    # Ignorar mensajes del bot
    if message.author.bot:
        return

    # Lista de IDs de canales donde solo se permiten comandos
    canales_restringidos = [1437551679770857542, 1437833190076317806]  # reemplaza con tus IDs

    # Solo borrar mensajes que NO sean comandos
    if message.channel.id in canales_restringidos and not message.content.startswith(bot.command_prefix):
        try:
            await message.delete()
        except Exception as e:
            print(f"⚠️ No se pudo eliminar mensaje: {e}")
        return

    # Procesar comandos normalmente
    await bot.process_commands(message)

#CREACION DE PARTIDAS POR ROL

# ID del canal donde se puede usar este comando
LFG_CHANNEL_ID = 1437833190076317806  # Reemplaza con el ID del canal de LFG

@bot.command()
async def lfg(ctx, juego: str = None, jugadores: str = None):
    """Busca grupo para un juego."""
    # Verificar canal permitido
    if ctx.channel.id != LFG_CHANNEL_ID:
        msg = await ctx.send("❌ Este comando solo puede usarse en el canal designado.")
        await asyncio.sleep(5)
        await msg.delete()
        await ctx.message.delete()
        return

    # Borrar el comando original
    await ctx.message.delete()

    # Validar argumentos
    if not juego or not jugadores:
        msg = await ctx.send("⚠️ Uso correcto: `!lfg <nombre_del_juego> <número_de_jugadores>`")
        await asyncio.sleep(5)
        await msg.delete()
        return

    try:
        jugadores = int(jugadores)
        if jugadores < 2:
            raise ValueError
    except ValueError:
        msg = await ctx.send("⚠️ El número de jugadores debe ser un entero >= 2.")
        await asyncio.sleep(5)
        await msg.delete()
        return

    # Llamar a la función que maneja la búsqueda de grupo
    await buscar_grupo(ctx, juego, jugadores)


async def buscar_grupo(ctx, juego: str, jugadores: int):
    # Enviar mensaje de anuncio que se borrará automáticamente tras 5 minutos
    anuncio = await ctx.send(
        f"🎮 **{ctx.author.display_name}** busca grupo de **{jugadores}** personas para **{juego}**.\n"
        f"Reacciona con 🎮 para unirte a la espera.",
        delete_after=300  # 5 minutos
    )
    await anuncio.add_reaction("🎮")

    jugadores_actuales = [ctx.author]

    # Función para comprobar la reacción
    def check_reaction(reaction, user):
        return (
            reaction.message.id == anuncio.id
            and str(reaction.emoji) == "🎮"
            and user not in jugadores_actuales
            and not user.bot
        )

    # Esperar jugadores
    while len(jugadores_actuales) < jugadores:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=300.0, check=check_reaction)
        except asyncio.TimeoutError:
            await ctx.send("⌛ La búsqueda de grupo ha expirado por inactividad.")
            try:
                await anuncio.delete()
            except:
                pass
            return
        else:
            jugadores_actuales.append(user)
            msg = await ctx.send(f"✅ {user.display_name} se ha unido ({len(jugadores_actuales)}/{jugadores})")
            await asyncio.sleep(3)
            await msg.delete()

    # Crear canales privados
    guild = ctx.guild
    category = get(guild.categories, name="𝓟𝓐𝓡𝓣𝓘𝓓𝓐𝓢 🖱️")
    if not category:
        category = await guild.create_category("𝓟𝓐𝓡𝓣𝓘𝓓𝓐𝓢 🖱️")

    overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False)}
    for player in jugadores_actuales:
        overwrites[player] = discord.PermissionOverwrite(view_channel=True, connect=True, send_messages=True)

    text_channel = await guild.create_text_channel(f"partida-{juego.lower()}", overwrites=overwrites, category=category)
    voice_channel = await guild.create_voice_channel(f"🎮 {juego}", overwrites=overwrites, category=category)

    # Mensaje inicial
    starter_message = await text_channel.send(
        f"✅ **Partida lista:** {', '.join([p.mention for p in jugadores_actuales])}\n"
        f"Canal de voz: {voice_channel.mention}\n"
        f"⏱️ Estos canales se eliminarán tras 5 minutos de inactividad."
    )

    # Monitorear inactividad
    await monitor_inactividad(ctx.bot, text_channel, voice_channel, starter_message, timeout=300)


async def monitor_inactividad(bot, text_channel, voice_channel, starter_message, timeout=300):
    print(f"👀 Monitorizando {text_channel.name} y {voice_channel.name}...")
    last_message_time = datetime.now(timezone.utc)  # aware

    while True:
        await asyncio.sleep(30)
        now = datetime.now(timezone.utc)  # aware

        # Verificar si hay alguien en el canal de voz
        voice_active = any(member for member in voice_channel.members if not member.bot)

        # Revisar último mensaje de usuario en el canal de texto
        try:
            async for message in text_channel.history(limit=1):
                if message.author != bot.user:
                    last_message_time = message.created_at.replace(tzinfo=timezone.utc)  # convertir a aware
        except:
            pass

        # Si no hay actividad ni usuarios
        if (not voice_active) and (now - last_message_time).total_seconds() > timeout:
            try:
                await text_channel.send("💤 Eliminando canales por inactividad...")
                await asyncio.sleep(3)
                await starter_message.delete()
            except:
                pass

            # Eliminar canales
            try:
                await text_channel.delete()
            except discord.NotFound:
                print(f"⚠️ Canal {text_channel.name} ya no existe.")
            try:
                await voice_channel.delete()
            except discord.NotFound:
                print(f"⚠️ Canal {voice_channel.name} ya no existe.")
            print(f"🗑️ Canales {text_channel.name} y {voice_channel.name} eliminados por inactividad.")
            return

# ----------------------------
# MENÚ DE SELECCIÓN DE ROLES
# ----------------------------

class RoleSelectView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=None)
        self.user = user
        self.temp_channel = None

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ Solo el creador puede usar este menú.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="💻 Plataforma", style=discord.ButtonStyle.primary)
    async def select_platform(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Selecciona tu plataforma:", view=PlatformButtons(self), ephemeral=True)

    @discord.ui.button(label="🎮 Juegos", style=discord.ButtonStyle.success)
    async def select_games(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Selecciona tus juegos:", view=GamesButtons(self), ephemeral=True)

    @discord.ui.button(label="✅ Finalizar", style=discord.ButtonStyle.green)
    async def finalize(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✅ Roles asignados. Canal temporal eliminado.", ephemeral=True)
        if self.temp_channel:
            await self.temp_channel.delete(reason="Usuario terminó selección de roles")

# -------------------------------
# BOTONES DE PLATAFORMA
# -------------------------------
class PlatformButtons(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=60)
        self.parent_view = parent_view

    @discord.ui.button(label="💻 PC", style=discord.ButtonStyle.primary)
    async def pc(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.assign_role(interaction, "PC")

    @discord.ui.button(label="🎮 PlayStation", style=discord.ButtonStyle.primary)
    async def ps(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.assign_role(interaction, "PlayStation")

    @discord.ui.button(label="🕹️ Xbox", style=discord.ButtonStyle.primary)
    async def xbox(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.assign_role(interaction, "Xbox")

    async def assign_role(self, interaction, role_name):
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Rol {role_name} asignado.", ephemeral=True)

            # Crear canal temporal si no existe
            if not self.parent_view.temp_channel:
                overwrites = {
                    interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    interaction.user: discord.PermissionOverwrite(view_channel=True)
                }
                category = discord.utils.get(interaction.guild.categories, name="🎮 Roles")
                if not category:
                    category = await interaction.guild.create_category("🎮 Roles")
                temp_channel = await interaction.guild.create_text_channel(
                    name=f"{interaction.user.name}-roles", overwrites=overwrites, category=category
                )
                self.parent_view.temp_channel = temp_channel
                await temp_channel.send("🎮 Canal privado creado para tu selección de roles y juegos.", view=self.parent_view)

# -------------------------------
# BOTONES DE JUEGOS
# -------------------------------
class GamesButtons(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=60)
        self.parent_view = parent_view

    @discord.ui.button(label="Valorant", style=discord.ButtonStyle.secondary)
    async def valorant(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.assign_role(interaction, "Valorant")

    @discord.ui.button(label="LoL", style=discord.ButtonStyle.secondary)
    async def lol(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.assign_role(interaction, "LoL")

    @discord.ui.button(label="Minecraft", style=discord.ButtonStyle.secondary)
    async def mc(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.assign_role(interaction, "Minecraft")

    @discord.ui.button(label="Fortnite", style=discord.ButtonStyle.secondary)
    async def fortnite(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.assign_role(interaction, "Fortnite")

    async def assign_role(self, interaction, role_name):
        role = discord.utils.get(interaction.guild.roles, name=role_name)
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Rol {role_name} asignado.", ephemeral=True)

# -------------------------------
# COMANDO PRINCIPAL
# -------------------------------
@bot.command()
async def roles(ctx):
    # Borrar el comando del canal público
    await ctx.message.delete()

    # Crear la vista principal
    view = RoleSelectView(ctx.author)

    # Crear canal temporal privado directamente al iniciar
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        ctx.author: discord.PermissionOverwrite(view_channel=True)
    }
    category = discord.utils.get(ctx.guild.categories, name="🎮 Roles")
    if not category:
        category = await ctx.guild.create_category("🎮 Roles")
    temp_channel = await ctx.guild.create_text_channel(
        name=f"{ctx.author.name}-roles", overwrites=overwrites, category=category
    )
    view.temp_channel = temp_channel

    # Enviar menú de botones en el canal privado
    await temp_channel.send(f"🎮 Hola {ctx.author.mention}, pulsa los botones para seleccionar tus roles y juegos:", view=view)


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

    # Enviar mensaje del bot y guardarlo
    bot_message = await ctx.send(
        f"✅ {ctx.author.mention}, se han creado tus canales temporales:\n"
        f"🎧 {voice_channel.mention}\n💬 {text_channel.mention}"
    )

    # Autoeliminar cuando quede vacío
    while True:
        await asyncio.sleep(10)  # espera 10 segundos antes de comprobar

        if len(voice_channel.members) == 0:
            # Borrar canales y mensaje del bot
            try:
                await text_channel.delete()
            except discord.Forbidden:
                pass

            try:
                await voice_channel.delete()
            except discord.Forbidden:
                pass

            try:
                await bot_message.delete()
            except discord.Forbidden:
                pass

            print(f"🗑️ Canales y mensaje de {ctx.author.name} eliminados automáticamente.")
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
        embed.set_image(url="https://i.pinimg.com/originals/1b/9e/e5/1b9ee55324c023928ecd2895aa602baa.gif")
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
    # Intentar borrar el mensaje del usuario que ejecuta el comando
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass  # No tiene permisos para borrar mensajes

    # Crear embed de aviso
    embed = discord.Embed(
        title="📢 Aviso del Staff",
        description=mensaje,
        color=discord.Color.red()
    )

    await ctx.send(embed=embed)

# ----------------------------
# ENVIAR MENSAJE
# ----------------------------

@bot.command()
async def say(ctx, *, mensaje):
    try:
        # Borrar el mensaje del usuario que ejecuta el comando
        await ctx.message.delete()
    except discord.Forbidden:
        pass  # No tiene permisos para borrar mensajes

    # Enviar el mensaje con el bot
    await ctx.send(mensaje)

#embed creation

class EmbedCreator(View):
    def __init__(self, author):
        super().__init__(timeout=600)
        self.author = author
        self.embed = discord.Embed(title="Título del embed", description="Descripción aquí...", color=discord.Color.blue())
        self.message = None
        self.messages_to_clean = []

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Solo el creador del embed puede usar este menú.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="📝 Título", style=discord.ButtonStyle.primary)
    async def set_title(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedFieldModal(self, "title", "Editar título", "Escribe el nuevo título"))

    @discord.ui.button(label="💬 Descripción", style=discord.ButtonStyle.primary)
    async def set_description(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedFieldModal(self, "description", "Editar descripción", "Escribe la descripción"))

    @discord.ui.button(label="🖼️ Imágenes", style=discord.ButtonStyle.primary)
    async def set_images(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedImagesModal(self))

    @discord.ui.button(label="🎨 Color", style=discord.ButtonStyle.secondary)
    async def set_color(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedColorModal(self))

    @discord.ui.button(label="🦶 Footer", style=discord.ButtonStyle.secondary)
    async def set_footer(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EmbedFieldModal(self, "footer", "Editar footer", "Texto del pie de página"))

    @discord.ui.button(label="📤 Publicar", style=discord.ButtonStyle.success)
    async def publish_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        channels = [
            discord.SelectOption(label=ch.name, value=str(ch.id))
            for ch in interaction.guild.text_channels
        ]
        select_view = PublishSelect(self, channels)
        await interaction.response.send_message("📨 Selecciona el canal donde publicar el embed:", view=select_view, ephemeral=True)


class EmbedFieldModal(Modal):
    def __init__(self, view: EmbedCreator, field: str, title: str, label: str):
        super().__init__(title=title)
        self.view = view
        self.field = field
        self.input = TextInput(label=label, style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.input)

    async def on_submit(self, interaction: discord.Interaction):
        value = self.input.value
        if self.field == "title":
            self.view.embed.title = value
        elif self.field == "description":
            self.view.embed.description = value
        elif self.field == "footer":
            self.view.embed.set_footer(text=value)

        await self.view.message.edit(embed=self.view.embed)
        await interaction.response.send_message("✅ Actualizado correctamente.", ephemeral=True)


class EmbedImagesModal(Modal, title="🖼️ Imágenes del embed"):
    def __init__(self, view: EmbedCreator):
        super().__init__()
        self.view = view
        self.image = TextInput(label="URL de imagen grande (opcional)", required=False)
        self.thumb = TextInput(label="URL de miniatura (opcional)", required=False)
        self.add_item(self.image)
        self.add_item(self.thumb)

    async def on_submit(self, interaction: discord.Interaction):
        if self.image.value:
            self.view.embed.set_image(url=self.image.value)
        if self.thumb.value:
            self.view.embed.set_thumbnail(url=self.thumb.value)
        await self.view.message.edit(embed=self.view.embed)
        await interaction.response.send_message("✅ Imágenes actualizadas.", ephemeral=True)


class EmbedColorModal(Modal, title="🎨 Cambiar color del borde"):
    def __init__(self, view: EmbedCreator):
        super().__init__()
        self.view = view
        self.color = TextInput(label="Color HEX (ej: #1c72ff)", required=True)
        self.add_item(self.color)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            color = int(self.color.value.replace("#", ""), 16)
            self.view.embed.color = discord.Color(color)
            await self.view.message.edit(embed=self.view.embed)
            await interaction.response.send_message("✅ Color actualizado.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Color no válido. Usa formato HEX (ej: #ff0000).", ephemeral=True)


class PublishSelect(View):
    def __init__(self, creator_view, channels):
        super().__init__(timeout=60)
        self.creator_view = creator_view
        self.add_item(ChannelSelectDropdown(self, channels))


class ChannelSelectDropdown(Select):
    def __init__(self, parent_view, channels):
        super().__init__(placeholder="Selecciona un canal...", options=channels)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        channel_id = int(self.values[0])
        channel = interaction.guild.get_channel(channel_id)
        if channel:
            await channel.send(embed=self.parent_view.creator_view.embed)
            await interaction.response.send_message(f"✅ Embed publicado en {channel.mention}", ephemeral=True)

            # 🔹 Limpieza solo de mensajes del creador y del bot
            async for msg in interaction.channel.history(limit=100):
                if msg.author == interaction.user or msg.author == interaction.client.user:
                    try:
                        await msg.delete()
                    except:
                        pass
            print(f"🧹 Canal {interaction.channel.name}: limpiados mensajes del menú y del creador.")


# ---- COMANDO ----
@commands.has_permissions(administrator=True)
@commands.command(name="embed")
async def embed_command(ctx):
    view = EmbedCreator(ctx.author)
    msg = await ctx.send(embed=view.embed, view=view)
    view.message = msg
    view.messages_to_clean.append(msg)
    await ctx.message.delete()

bot.add_command(embed_command)

# -------------------------------
# MODALES DE REPORTES
# -------------------------------
class PersonaModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Reporte de Persona")
        self.add_item(discord.ui.TextInput(label="Nombre de la persona reportada", placeholder="Usuario#1234"))
        self.add_item(discord.ui.TextInput(label="Descripción del reporte", style=discord.TextStyle.paragraph))

    async def on_submit(self, interaction: discord.Interaction):
        nombre = self.children[0].value
        descripcion = self.children[1].value

        await interaction.response.defer()  # Marca como respondida

        # Crear canal privado
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="𝕊𝕆ℙ𝕆ℝ𝕋𝔼")
        if not category:
            category = await guild.create_category("𝕊𝕆ℙ𝕆ℝ𝕋𝔼")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True)
        }
        report_channel = await guild.create_text_channel(
            name=f"reporte-{interaction.user.name}", overwrites=overwrites, category=category
        )

        # Enviar embed con la info
        embed = discord.Embed(
            title=f"Reporte de Persona: {nombre}",
            description=descripcion,
            color=discord.Color.red()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        await report_channel.send(embed=embed)

        # Botón de cerrar ticket
        view = CloseTicketButton(ticket_owner=interaction.user)
        await report_channel.send("📌 Pulsa el botón para cerrar este ticket.", view=view)

        # Mensaje de confirmación al usuario
        await interaction.followup.send(f"✅ Tu reporte de {nombre} ha sido enviado.", ephemeral=True)


class BugModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Reporte de Bug")
        self.add_item(discord.ui.TextInput(label="Descripción del bug", style=discord.TextStyle.paragraph))
        self.add_item(discord.ui.TextInput(label="Pasos para reproducir", style=discord.TextStyle.paragraph))

    async def on_submit(self, interaction: discord.Interaction):
        descripcion = self.children[0].value
        pasos = self.children[1].value

        await interaction.response.defer()

        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="𝕊𝕆ℙ𝕆ℝ𝕋𝔼")
        if not category:
            category = await guild.create_category("𝕊𝕆ℙ𝕆ℝ𝕋𝔼")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True)
        }

        report_channel = await guild.create_text_channel(
            name=f"reporte-bug-{interaction.user.name}", overwrites=overwrites, category=category
        )

        embed = discord.Embed(title="Reporte de Bug", description=descripcion, color=discord.Color.orange())
        embed.add_field(name="Pasos para reproducir", value=pasos, inline=False)
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        await report_channel.send(embed=embed)

        view = CloseTicketButton(ticket_owner=interaction.user)
        await report_channel.send("📌 Pulsa el botón para cerrar este ticket.", view=view)

        await interaction.followup.send("✅ Tu reporte de bug ha sido enviado.", ephemeral=True)


# -------------------------------
# BOTONES DEL MENSAJE FIJO
# -------------------------------
class ReportButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Persona", style=discord.ButtonStyle.danger)
    async def persona_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PersonaModal())

    @discord.ui.button(label="Bug", style=discord.ButtonStyle.primary)
    async def bug_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BugModal())

    @discord.ui.button(label="Información", style=discord.ButtonStyle.secondary)
    async def info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("ℹ️ Aquí podrías añadir otro modal o info.", ephemeral=True)


# -------------------------------
# BOTÓN DE CERRAR TICKET
# -------------------------------
class CloseTicketButton(discord.ui.View):
    def __init__(self, ticket_owner):
        super().__init__(timeout=None)
        self.ticket_owner = ticket_owner

    @discord.ui.button(label="🔒 Cerrar ticket", style=discord.ButtonStyle.red)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ticket_owner and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Solo el creador o un admin puede cerrar este ticket.", ephemeral=True)
            return

        await interaction.channel.delete(reason="Ticket cerrado")


# ============================================================
# BOTÓN PARA COMPROBAR LLAMADAS
# ============================================================

CANAL_LLAMADAS_ID = 1552429519791456256 # Canal donde estará el mensaje fijo

TIEMPO_BORRADO_LLAMADA = 5 * 60  # 5 minutos


# ============================================================
# OBTENER LLAMADAS ACTIVAS
# ============================================================

def obtener_llamadas_activas(guild):

    llamadas = []

    for canal in guild.voice_channels:

        # Ignorar canales sin personas
        personas = [
            miembro
            for miembro in canal.members
            if not miembro.bot
        ]

        if personas:

            llamadas.append({
                "canal": canal,
                "personas": personas
            })

    return llamadas


# ============================================================
# BOTÓN
# ============================================================

class BotonNotificarLlamadas(
    discord.ui.Button
):

    def __init__(self):

        super().__init__(
            label="🔔 Notificar llamadas",
            style=discord.ButtonStyle.primary,
            custom_id="notificar_llamadas"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):

        guild = interaction.guild

        if guild is None:

            await interaction.response.send_message(
                "❌ No se ha podido comprobar el servidor.",
                ephemeral=True
            )

            return

        # Comprobar llamadas ACTUALES
        llamadas = obtener_llamadas_activas(guild)

        # ====================================================
        # NO HAY NADIE
        # ====================================================

        if not llamadas:

            embed = discord.Embed(
                title="🔇 No hay nadie en llamada",
                description=(
                    "Actualmente no hay ninguna persona "
                    "conectada a un canal de voz."
                ),
                color=discord.Color.red(),
                timestamp=datetime.now(timezone.utc)
            )

            embed.set_footer(
                text="Este mensaje se eliminará en 5 minutos."
            )

            await interaction.response.send_message(
                embed=embed
            )

            mensaje = await interaction.original_response()

            await asyncio.sleep(
                TIEMPO_BORRADO_LLAMADA
            )

            try:
                await mensaje.delete()
            except discord.NotFound:
                pass

            return

        # ====================================================
        # HAY GENTE EN LLAMADA
        # ====================================================

        embed = discord.Embed(
            title="🎧 Gente en llamada",
            description=(
                "Actualmente hay personas conectadas "
                "a los siguientes canales:"
            ),
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )

        total_personas = 0

        for llamada in llamadas:

            canal = llamada["canal"]
            personas = llamada["personas"]

            total_personas += len(personas)

            lista_personas = "\n".join(
                f"👤 {persona.display_name}"
                for persona in personas
            )

            embed.add_field(
                name=(
                    f"🎙️ {canal.name} "
                    f"— {len(personas)} persona(s)"
                ),
                value=lista_personas,
                inline=False
            )

        embed.set_footer(
            text=(
                f"{total_personas} persona(s) conectada(s) • "
                "Este mensaje se eliminará en 5 minutos."
            )
        )

        allowed_mentions = discord.AllowedMentions(everyone=True)

        await interaction.response.send_message(
            content="@everyone",
            embed=embed,
            allowed_mentions=allowed_mentions,
            delete_after=300
        )

        await interaction.response.send_message(
            embed=embed
        )

        mensaje = await interaction.original_response()

        # ====================================================
        # BORRAR DESPUÉS DE 5 MINUTOS
        # ====================================================

        await asyncio.sleep(
            TIEMPO_BORRADO_LLAMADA
        )

        try:
            await mensaje.delete()

        except discord.NotFound:
            pass


# ============================================================
# VIEW DEL BOTÓN
# ============================================================

class VistaNotificarLlamadas(
    discord.ui.View
):

    def __init__(self):

        super().__init__(
            timeout=None
        )

        self.add_item(
            BotonNotificarLlamadas()
        )


# ============================================================
# PUBLICAR EL MENSAJE FIJO
# ============================================================

async def publicar_panel_llamadas():

    canal = bot.get_channel(
        CANAL_LLAMADAS_ID
    )

    if canal is None:

        print(
            "❌ No se encontró el canal "
            "para el panel de llamadas."
        )

        return

    # Buscar si ya existe nuestro mensaje
    async for mensaje in canal.history(
        limit=100
    ):

        if (
            mensaje.author == bot.user
            and mensaje.components
        ):

            print(
                "✔ Panel de llamadas ya existe."
            )

            return

    # ========================================================
    # CREAR PANEL
    # ========================================================

    embed = discord.Embed(
        title="📞 Notificaciones de llamadas",
        description=(
            "¿Quieres saber si hay gente en llamada?\n\n"
            "Pulsa el botón de abajo y comprobaré "
            "los canales de voz **en ese momento**.\n\n"
            "🔔 **Notificar llamadas**"
        ),
        color=discord.Color.blurple()
    )

    embed.set_footer(
        text="La información mostrada será la actual."
    )

    await canal.send(
        embed=embed,
        view=VistaNotificarLlamadas()
    )

    print(
        "✔ Panel de llamadas publicado."
    )

# ----------------------------
# INICIAR BOT
# ----------------------------
bot.run(os.getenv("DISCORD_TOKEN"))




































































































