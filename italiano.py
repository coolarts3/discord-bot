import discord
from discord.ext import commands
import os
import asyncio
from discord.ui import Modal, TextInput
import sqlite3

# ───── Base de datos │ alianzas.db ─────────────────────────────────

DB = "alianzas.db"
conn = sqlite3.connect(DB)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS alianzas (
    tipo TEXT PRIMARY KEY,
    nombre TEXT,
    numero TEXT,
    foto TEXT,
    compra TEXT,
    venta TEXT
)
""")
conn.commit()
conn.close()


def guardar_alianza(tipo, nombre, numero, foto, compra, venta):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO alianzas (tipo, nombre, numero, foto, compra, venta)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (tipo, nombre, numero, foto, compra, venta))
    conn.commit()
    conn.close()


def cargar_alianza(tipo):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, numero, foto, compra, venta FROM alianzas WHERE tipo = ?", (tipo,))
    data = cursor.fetchone()
    conn.close()
    if not data:
        return None
    return {
        "nombre": data[0],
        "numero": data[1],
        "foto": data[2],
        "compra": data[3],
        "venta": data[4]
    }


def borrar_alianza(tipo):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM alianzas WHERE tipo = ?", (tipo,))
    conn.commit()
    conn.close()


# ───── Discord bot ─────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

USERS_ALLOWED = [682643114560848012, 352471626400661514]  # IDs con permiso
CANAL_ALIANZAS = 1442618930291281960  # Canal permitido para !alianzas


# ───── MODAL REGISTRO ─────────────────────────────

class ModalAlianza(Modal, title="Registrar Alianza"):
    def __init__(self, alianza):
        super().__init__()
        self.alianza = alianza
        self.nombre = TextInput(label="Nombre familia")
        self.numero = TextInput(label="Número familia")
        self.foto = TextInput(label="URL imagen")
        self.compra = TextInput(label="Compra %")
        self.venta = TextInput(label="Venta %")

        self.add_item(self.nombre)
        self.add_item(self.numero)
        self.add_item(self.foto)
        self.add_item(self.compra)
        self.add_item(self.venta)

    async def on_submit(self, interaction):
        guardar_alianza(
            self.alianza,
            str(self.nombre),
            str(self.numero),
            str(self.foto),
            str(self.compra),
            str(self.venta)
        )
        await interaction.response.send_message(
            f"✅ Alianza **{self.alianza}** registrada correctamente.",
            delete_after=20
        )


# ───── MODAL EDICIÓN ─────────────────────────────

class EditModal(Modal, title="Editar alianza"):
    def __init__(self, alianza, data):
        super().__init__()
        self.alianza = alianza
        self.nombre = TextInput(label="Nombre familia", default=data["nombre"])
        self.numero = TextInput(label="Número familia", default=data["numero"])
        self.foto = TextInput(label="URL imagen", default=data["foto"])
        self.compra = TextInput(label="Compra %", default=data["compra"])
        self.venta = TextInput(label="Venta %", default=data["venta"])

        self.add_item(self.nombre)
        self.add_item(self.numero)
        self.add_item(self.foto)
        self.add_item(self.compra)
        self.add_item(self.venta)

    async def on_submit(self, interaction):
        guardar_alianza(
            self.alianza,
            str(self.nombre),
            str(self.numero),
            str(self.foto),
            str(self.compra),
            str(self.venta)
        )
        await interaction.response.send_message(
            f"✏️ Alianza **{self.alianza}** actualizada correctamente.",
            delete_after=600
        )


# ───── Select View ─────────────────────────────

class SelectAlianzas(discord.ui.Select):
    def __init__(self):
        opciones = [
            discord.SelectOption(label=a) for a in
            ["porros", "armas", "lavado dinero", "desguace", "balas", "meta", "tarjetas"]
        ]
        super().__init__(placeholder="Selecciona una alianza…", options=opciones)

    async def callback(self, interaction):
        data = cargar_alianza(self.values[0])
        if not data:
            return await interaction.response.send_message(
                f"⚠️ La alianza **{self.values[0]}** no está configurada.",
                delete_after=10
            )

        embed = discord.Embed(title=f"📌 Información de la alianza: {self.values[0]}", color=discord.Color.blue())
        embed.add_field(name="🏷️ Nombre", value=data["nombre"], inline=False)
        embed.add_field(name="🔢 Número", value=data["numero"], inline=False)
        embed.add_field(name="💰 Compra", value=f"{data['compra']}%", inline=True)
        embed.add_field(name="🪙 Venta", value=f"{data['venta']}%", inline=True)
        embed.set_image(url=data["foto"])
        embed.set_footer(text="Sistema de alianzas")

        await interaction.response.send_message(embed=embed, delete_after=120)


class ViewAlianzas(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectAlianzas())


# ───── COMANDOS ─────────────────────────────────────

@bot.command()
async def alianzas(ctx):
    if ctx.channel.id != CANAL_ALIANZAS:
        msg = await ctx.reply(f"⛔ Este comando solo puede usarse en <#{CANAL_ALIANZAS}>.", delete_after=10)
        await asyncio.sleep(5)
        await ctx.message.delete()
        return

    await ctx.send("📌 Selecciona una alianza:", view=ViewAlianzas(), delete_after=20)


@bot.command()
async def setalianzas(ctx, alianza=None):
    if ctx.author.id not in USERS_ALLOWED:
        return await ctx.send("⛔ No tienes permiso.", delete_after=8)

    validas = ["porros", "armas", "lavado dinero", "desguace", "balas", "meta", "tarjetas"]
    if not alianza or alianza.lower() not in validas:
        return await ctx.send("⚠️ Uso correcto: `!setalianzas <alianza>`", delete_after=12)

    alianza = alianza.lower()

    class Button(discord.ui.View):
        @discord.ui.button(label="📋 Abrir formulario", style=discord.ButtonStyle.green)
        async def open(self, interaction, button):
            await interaction.response.send_modal(ModalAlianza(alianza))

    await ctx.send(f"📝 Configurar **{alianza}**:", view=Button(), delete_after=30)


@bot.command()
async def editalianzas(ctx, alianza=None):
    if ctx.author.id not in USERS_ALLOWED:
        return await ctx.send("⛔ No tienes permiso.", delete_after=10)

    if not alianza:
        return await ctx.send("⚠️ Uso correcto: `!editalianzas <alianza>`", delete_after=10)

    data = cargar_alianza(alianza.lower())
    if not data:
        return await ctx.send(f"❌ La alianza **{alianza}** no está registrada.", delete_after=10)

    class Button(discord.ui.View):
        @discord.ui.button(label="✏️ Editar", style=discord.ButtonStyle.blurple)
        async def abrir(self, interaction, button):
            await interaction.response.send_modal(EditModal(alianza.lower(), data))

    await ctx.send(f"🔧 Editar alianza **{alianza.lower()}**:", view=Button(), delete_after=30)


@bot.command()
async def deletealianzas(ctx, alianza=None):
    if ctx.author.id not in USERS_ALLOWED:
        return await ctx.send("⛔ No tienes permiso.", delete_after=8)

    if not alianza:
        return await ctx.send("⚠️ Uso correcto: `!deletealianzas <alianza>`", delete_after=12)

    if not cargar_alianza(alianza.lower()):
        return await ctx.send(f"❌ La alianza **{alianza}** no existe.", delete_after=10)

    borrar_alianza(alianza.lower())
    await ctx.send(f"🗑️ Alianza **{alianza.lower()}** eliminada.", delete_after=10)


@bot.command()
async def hola(ctx):
    await ctx.send("👋 Hola, soy el segundo bot.", delete_after=10)

@bot.command()
async def aviso(ctx, *, mensaje=None):
    if not mensaje:
        return await ctx.send("❌ Uso correcto: `!aviso <mensaje>`", delete_after=8)

    # Imagen de cabecera del aviso
    banner = "https://i.imgur.com/SYlRwEf.png"  # Puedes cambiarla por otra

    embed = discord.Embed(
        title="⚠️ AVISO IMPORTANTE",
        description=f"📢 **{mensaje}**",
        color=discord.Color.red()
    )
    embed.set_image(url=banner)
    embed.set_footer(text=f"Anuncio realizado por {ctx.author}", icon_url=ctx.author.avatar)
    embed.timestamp = discord.utils.utcnow()

    aviso = await ctx.send(content="🔔 @everyone", embed=embed)
    await ctx.message.delete()

    # borrar automáticamente después de 10 minutos
    await asyncio.sleep(600)
    await aviso.delete()

# ⬇️ IDs de usuarios que pueden crear planes
USERS_ALLOWED_PLAN = [352471626400661514, 682643114560848012]

# ⬇️ Canal donde funciona exclusivamente el comando !plan
CANAL_PLANES = 1415492411022512213  # ⬅️ CAMBIA ESTE NÚMERO POR LA ID DEL CANAL

# ⬇️ Emoji para apuntarse al atraco
EMOJI_PARTICIPAR = "🔫"

# ⚙️ Memoria de planes activos
planes_activos = {}  # message_id : {"msg": msg, "usuarios": set(), "embed": embed}


# 📌 Modal para crear un plan
class ModalPlan(discord.ui.Modal, title="📋 Crear Plan de Atraco"):
    def __init__(self):
        super().__init__()

        self.lugar = TextInput(label="📍 Lugar del atraco", placeholder="Ej: Banco Central")
        self.hora = TextInput(label="⏳ Hora del golpe", placeholder="Ej: 22:30")
        self.objetivo = TextInput(label="🎯 Dinero", placeholder="Ej: Cámara de seguridadp")
        self.participantes = TextInput(label="👥 Participantes previstos", placeholder="Ej: 5")
        
        # campo combinado: palabra clave + detalles
        self.detalles = TextInput(
            label="🧠 Detalles extra",
            placeholder="Información y notas del atraco...",
            style=discord.TextStyle.paragraph,
            required=False
        )

        # máximo 5 → ahora está correcto
        self.add_item(self.lugar)
        self.add_item(self.hora)
        self.add_item(self.objetivo)
        self.add_item(self.participantes)
        self.add_item(self.detalles)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔥 PLAN DE ATRACO EN MARCHA 🔥",
            color=discord.Color.red()
        )
        embed.add_field(name="📍 Lugar", value=self.lugar.value, inline=False)
        embed.add_field(name="⏳ Hora", value=self.hora.value, inline=True)
        embed.add_field(name="🎯 Dinero", value=self.objetivo.value, inline=True)
        embed.add_field(name="👥 Participantes previstos", value=self.participantes.value, inline=True)
        embed.add_field(name="🧠 Clave / Detalles del plan", value=self.detalles.value or "No especificado", inline=False)

        embed.add_field(name="👥 Participantes confirmados", value="0", inline=False)
        embed.set_footer(text=f"Plan creado por {interaction.user}", icon_url=interaction.user.avatar)
        embed.timestamp = discord.utils.utcnow()

        msg = await interaction.channel.send(embed=embed)
        await msg.add_reaction("🔫")

        planes_activos[msg.id] = {"msg": msg, "usuarios": set(), "embed": embed}

        await interaction.response.send_message("📡 Plan enviado — los miembros pueden reaccionar para unirse.", ephemeral=True)

        await asyncio.sleep(900)
        try:
            await msg.delete()
        except:
            pass
        planes_activos.pop(msg.id, None)


# 📌 Comando !plan
@bot.command()
async def plan(ctx):
    # ❌ Bloquear si no es el canal correcto
    if ctx.channel.id != CANAL_PLANES:
        aviso = await ctx.reply(f"⛔ Este comando solo puede usarse en <#{CANAL_PLANES}>.")
        await asyncio.sleep(5)
        await aviso.delete()
        await ctx.message.delete()
        return

    # ❌ Bloquear si no tiene permisos
    if ctx.author.id not in USERS_ALLOWED_PLAN:
        return await ctx.reply("⛔ No tienes permiso para planear atracos.", delete_after=7)

    class ViewBotonPlan(discord.ui.View):
        @discord.ui.button(label="📋 Crear plan de atraco", style=discord.ButtonStyle.red)
        async def abrir_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(ModalPlan())

    await ctx.send("🕵️ Pulsa el botón para crear un plan de atraco:", view=ViewBotonPlan(), delete_after=60)


# 📌 Reacción para unirse al plan
@bot.event
async def on_raw_reaction_add(payload):
    if payload.message_id not in planes_activos:
        return
    if str(payload.emoji) != EMOJI_PARTICIPAR:
        return
    if payload.user_id == bot.user.id:
        return

    data = planes_activos[payload.message_id]
    data["usuarios"].add(payload.user_id)

    embed = data["embed"]
    embed.set_field_at(
        index=3,
        name="👥 Participantes confirmados",
        value=str(len(data["usuarios"])),
        inline=False
    )
    await data["msg"].edit(embed=embed)


# 📌 Al quitar la reacción, se resta el participante
@bot.event
async def on_raw_reaction_remove(payload):
    if payload.message_id not in planes_activos:
        return
    if str(payload.emoji) != EMOJI_PARTICIPAR:
        return

    data = planes_activos[payload.message_id]
    data["usuarios"].discard(payload.user_id)

    embed = data["embed"]
    embed.set_field_at(
        index=3,
        name="👥 Participantes confirmados",
        value=str(len(data["usuarios"])),
        inline=False
    )
    await data["msg"].edit(embed=embed)

# ====== CONFIG ======
CANAL_PRECIOS_ARM = 1442783256704712795  # ⬅️ ID del canal permitido
USERS_ALLOWED_PRECIOS = [352471626400661514, 352471626400661514]  # ⬅️ IDs que tienen permiso

IMG_0  = "https://i.imgur.com/BWLOxla.png"
IMG_20 = "https://i.imgur.com/ediQEet.png"
IMG_25 = "https://i.imgur.com/eXVpoQN.png"
IMG_30 = "https://i.imgur.com/AAqnNcQ.png"

ultimo_mensaje_precios = None  # se usará para restaurar el mensaje tras un reinicio


# ====== SELECT ======
class SelectPrecios(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="📌 Selecciona tu descuento de armas...",
            options=[
                discord.SelectOption(label="0% DESCUENTO"),
                discord.SelectOption(label="20% DESCUENTO"),
                discord.SelectOption(label="25% DESCUENTO"),
                discord.SelectOption(label="30% DESCUENTO")
            ]
        )

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user

        # Selección de imagen según la opción
        match self.values[0]:
            case "0% DESCUENTO": img = IMG_0
            case "20% DESCUENTO": img = IMG_20
            case "25% DESCUENTO": img = IMG_25
            case "30% DESCUENTO": img = IMG_30

        try:
            embed = discord.Embed(color=discord.Color.dark_red())
            embed.set_image(url=img)
            await user.send(f"🔫 **Tabla de precios {self.values[0]}**", embed=embed)
            await interaction.response.send_message("📬 ¡Revisá tus MD!", ephemeral=True)
        except:
            await interaction.response.send_message(
                "⚠ No puedo enviarte mensajes privados. Activa tus MD.",
                ephemeral=True
            )


# ====== VIEW ======
class ViewPrecios(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectPrecios())


# ====== FUNCIÓN PARA PUBLICAR EL MENSAJE PERMANENTE ======
async def publicar_menu_precios():
    global ultimo_mensaje_precios
    canal = bot.get_channel(CANAL_PRECIOS_ARM)
    if not canal:
        print("⚠ CANAL_PRECIOS_ARM no encontrado")
        return

    # borrar SOLO mensajes previos enviados por el bot
    async for msg in canal.history(limit=500):
        if msg.author == bot.user:
            try:
                await msg.delete()
            except:
                pass

    # crear de nuevo el mensaje permanente
    embed = discord.Embed(
        title="🔫 PRECIO DE ARMAS 🔫",
        description="Selecciona a continuación tu descuento.\n📩 La tabla se enviará **por mensaje privado**.",
        color=discord.Color.dark_red()
    )

    ultimo_mensaje_precios = await canal.send(embed=embed, view=ViewPrecios())
    print("✔ Menú de precios publicado")


# ====== COMANDO (RESTRINGIDO) ======
@bot.command()
async def preciosarm(ctx):
    if ctx.author.id not in USERS_ALLOWED_PRECIOS:
        await ctx.reply("⛔ No tienes permiso para usar este comando.", delete_after=8)
        return

    if ctx.channel.id != CANAL_PRECIOS_ARM:
        aviso = await ctx.reply(f"⛔ Este comando solo puede usarse en <#{CANAL_PRECIOS_ARM}>.", delete_after=7)
        await asyncio.sleep(5)
        await aviso.delete()
        await ctx.message.delete()
        return

    await publicar_menu_precios()
    await ctx.message.delete()

@bot.event
async def on_message(message):
    # ignorar mensajes del propio bot
    if message.author == bot.user:
        return

    # si el mensaje empieza por "!"
    if message.content.startswith("!"):
        # borrar después de 10 segundos
        await message.delete(delay=10)

    # NECESARIO para que sigan funcionando los comandos
    await bot.process_commands(message)


# ───── Startup ─────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"🤖 Bot conectado como {bot.user}")


bot.run(os.getenv("DISCORD_TOKEN2"))
