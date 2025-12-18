import discord
from discord.ext import commands
import os
import asyncio
from discord.ui import View, Modal, TextInput
from discord import Embed, ui
from datetime import datetime, timedelta
import random
import json
import re
import unicodedata

EMOJI = "🎉"

# ─────────────────────────────────────────────
# BOT E INTEN
# ─────────────────────────────────────────────
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

ALIANZAS_FILE = "alianzas.json"

if not os.path.exists(ALIANZAS_FILE):
    with open(ALIANZAS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, indent=4, ensure_ascii=False)

# ─────────────────────────────────────────────
# SISTEMA DE ALIANZAS
# ─────────────────────────────────────────────
CANAL_ALIANZAS = 1442618930291281960  # ID del canal permanente
USERS_ALLOWED = [352471626400661514, 691007149542998096]

DB_FOLDER = "/storage"
DB = f"{DB_FOLDER}/alianzas.db"
os.makedirs(DB_FOLDER, exist_ok=True)

def cargar_alianzas():
    with open(ALIANZAS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_alianzas(data):
    with open(ALIANZAS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def obtener_alianzas():
    data = cargar_alianzas()
    return [(a["id"], a["familia"], a["numero"], a["objeto"]) for a in data]

def obtener_info(id_familia):
    data = cargar_alianzas()
    for a in data:
        if a["id"] == id_familia:
            return a
    return None

def guardar_nueva(familia, numero, foto, compra, venta):
    data = cargar_alianzas()

    nuevo_id = max([a["id"] for a in data], default=0) + 1

    data.append({
        "id": nuevo_id,
        "familia": familia,
        "numero": numero,
        "foto": foto,
        "compra": compra,
        "venta": venta
    })

    guardar_alianzas(data)

def actualizar_alianza(id_fam, familia, numero, foto, compra, venta):
    data = cargar_alianzas()

    for a in data:
        if a["id"] == id_fam:
            a.update({
                "familia": familia,
                "numero": numero,
                "foto": foto,
                "compra": compra,
                "venta": venta
            })
            break

    guardar_alianzas(data)

def borrar_alianza(id_fam):
    data = cargar_alianzas()
    data = [a for a in data if a["id"] != id_fam]
    guardar_alianzas(data)

class ModalNuevaAlianza(discord.ui.Modal, title="➕ AÑADIR NUEVA ALIANZA"):
    familia = TextInput(label="🔮Familia + Material venta", placeholder="Ej: Los Corleone")
    numero = TextInput(label="🔢Número identificador", placeholder="Ej: 12")
    foto = TextInput(label="📎URL de la foto", placeholder="https://...")
    compra = TextInput(label="🔰Descuento de compra (%)", placeholder="Ej: 10")
    venta = TextInput(label="🔰Descuento de venta (%)", placeholder="Ej: 15")

    async def on_submit(self, interaction: discord.Interaction):
        guardar_nueva(self.familia.value, self.numero.value, self.foto.value, self.compra.value, self.venta.value)
        await interaction.response.send_message("✔ **Alianza añadida correctamente.**", ephemeral=True)
        await publicar_menu()


class ModalEditarAlianza(discord.ui.Modal, title="📝 Editar alianza"):
    def __init__(self, id_fam, datos):
        super().__init__()
        self.id_fam = id_fam

        self.familia = TextInput(label="🔮Familia + Material venta", default=datos["familia"])
        self.numero = TextInput(label="🔢Número identificador", default=datos["numero"])
        self.foto = TextInput(label="📎URL de la foto", default=datos["foto"])
        self.compra = TextInput(label="🔰Descuento de compra (%)", default=datos["compra"])
        self.venta = TextInput(label="🔰Descuento de venta (%)", default=datos["venta"])

        self.add_item(self.familia)
        self.add_item(self.numero)
        self.add_item(self.foto)
        self.add_item(self.compra)
        self.add_item(self.venta)

    async def on_submit(self, interaction: discord.Interaction):
        actualizar_alianza(
            self.id_fam,
            self.familia.value,
            self.numero.value,
            self.foto.value,
            self.compra.value,
            self.venta.value
        )
        await interaction.response.send_message("✔ **Alianza actualizada correctamente.**", ephemeral=True)
        await publicar_menu()


class ViewAbrirModalAlianza(discord.ui.View):
    @discord.ui.button(label="➕ Crear nueva alianza", style=discord.ButtonStyle.green)
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalNuevaAlianza())


class ViewEditarAlianza(discord.ui.View):
    def __init__(self, id_fam, datos):
        super().__init__()
        self.id_fam = id_fam
        self.datos = datos

    @discord.ui.button(label="✏ Editar esta alianza", style=discord.ButtonStyle.blurple)
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalEditarAlianza(self.id_fam, self.datos))


class SelectAlianzas(discord.ui.Select):
    def __init__(self):
        alianzas = obtener_alianzas()
        options = [
            discord.SelectOption(label=f"{row[1]} (Nº {row[2]}) - {row[3]}", value=str(row[0]))
            for row in alianzas
        ]

        super().__init__(
            placeholder="Selecciona una familia",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        info = obtener_info(int(self.values[0]))
        if not info:
            return await interaction.response.send_message(
                "⚠ Esta familia ya no existe.", ephemeral=True
            )

        embed = discord.Embed(
            title=f"📌 Alianza con {info['familia']}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Número", value=info["numero"], inline=True)
        embed.add_field(name="Compra %", value=info["compra"], inline=True)
        embed.add_field(name="Venta %", value=info["venta"], inline=True)
        embed.add_field(name="Producto", value=info["objeto"], inline=True)
        embed.add_field(name="Precio Base", value=info["precio"], inline=True)
        embed.set_image(url=info["foto"])
        embed.set_footer(text="Sistema de alianzas")

        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        await asyncio.sleep(30)
        try:
            await msg.delete()
        except:
            pass


class ViewAlianzas(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectAlianzas())


async def publicar_menu():
    canal = bot.get_channel(CANAL_ALIANZAS)
    if not canal:
        print("⚠ Canal de alianzas no encontrado")
        return

    # borrar solo mensajes del bot
    async for msg in canal.history(limit=200):
        if msg.author == bot.user:
            try:
                await msg.delete()
            except:
                pass

    alianzas = obtener_alianzas()

    embed = discord.Embed(
        title="🤝 LISTA DE ALIANZAS DISPONIBLES",
        color=discord.Color.gold()
    )

    if not alianzas:
        embed.description = "⚠ No hay alianzas registradas.\nUsa `!setalianzas` para añadir una."
        await canal.send(embed=embed)
    else:
        embed.description = "📌 Selecciona una familia en el menú de abajo."
        await canal.send(embed=embed, view=ViewAlianzas())

    print("✔ Menú de alianzas actualizado")


@bot.command()
async def setalianzas(ctx):
    if ctx.author.id not in USERS_ALLOWED:
        return await ctx.send("⛔ No tienes permiso.", delete_after=8)

    await ctx.send(
        "📄 Haz clic en el botón para crear una alianza:",
        view=ViewAbrirModalAlianza(),
        delete_after=60
    )


@bot.command()
async def deletealianza(ctx, id_fam=None):
    if ctx.author.id not in USERS_ALLOWED:
        return await ctx.send("⛔ No tienes permiso.", delete_after=8)

    if not id_fam or not id_fam.isdigit():
        return await ctx.send("Uso: `!deletealianza <ID>`", delete_after=8)

    borrar_alianza(int(id_fam))
    await ctx.send("🗑 Eliminada.", delete_after=6)

    await publicar_menu()


@bot.command()
async def editaralianzas(ctx, id_fam=None):
    if ctx.author.id not in USERS_ALLOWED:
        return await ctx.send("⛔ No tienes permiso.", delete_after=8)

    if not id_fam or not id_fam.isdigit():
        return await ctx.send("Uso: `!editaralianzas <ID>`", delete_after=8)

    datos = obtener_info(int(id_fam))
    if not datos:
        return await ctx.send("❌ No existe una alianza con ese ID.", delete_after=8)

    await ctx.send(
        content=f"📌 Estás editando la alianza **{datos['familia']}**.\nPulsa el botón para abrir el formulario:",
        view=ViewEditarAlianza(int(id_fam), datos),
        delete_after=60
    )

# ─────────────────────────────────────────────
# HOLA Y AVISO
# ─────────────────────────────────────────────

@bot.command()
async def hola(ctx):
    await ctx.send("👋 Hola, soy el segundo bot.", delete_after=10)


@bot.command()
async def aviso(ctx, *, mensaje=None):
    if not mensaje:
        return await ctx.send("❌ Uso correcto: `!aviso <mensaje>`", delete_after=8)

    banner = "https://i.imgur.com/SYlRwEf.png"

    embed = discord.Embed(
        title="⚠️ AVISO IMPORTANTE",
        description=f"📢 **{mensaje}**",
        color=discord.Color.red()
    )
    embed.set_image(url=banner)
    embed.set_footer(text=f"Anuncio realizado por {ctx.author}", icon_url=ctx.author.avatar)
    embed.timestamp = discord.utils.utcnow()

    aviso_msg = await ctx.send(content="🔔 @everyone", embed=embed)
    await ctx.message.delete()

    await asyncio.sleep(600)
    await aviso_msg.delete()

# ─────────────────────────────────────────────
# SISTEMA PLANES
# ─────────────────────────────────────────────

USERS_ALLOWED_PLAN = [352471626400661514, 682643114560848012]
CANAL_PLANES = 1415492411022512213
EMOJI_PARTICIPAR = "🔫"
planes_activos = {}  # message_id : {"msg": msg, "usuarios": set(), "embed": embed}


class ModalPlan(discord.ui.Modal, title="📋 Crear Plan de Atraco"):
    def __init__(self):
        super().__init__()

        self.lugar = TextInput(label="📍 Lugar del atraco", placeholder="Ej: Banco Central")
        self.hora = TextInput(label="⏳ Hora del golpe", placeholder="Ej: 22:30")
        self.objetivo = TextInput(label="🎯 Dinero", placeholder="Ej: Cámara de seguridad")
        self.participantes = TextInput(label="👥 Participantes previstos", placeholder="Ej: 5")
        self.detalles = TextInput(
            label="🧠 Detalles extra",
            placeholder="Información y notas del atraco...",
            style=discord.TextStyle.paragraph,
            required=False
        )

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
        embed.add_field(
            name="🧠 Clave / Detalles del plan",
            value=self.detalles.value or "No especificado",
            inline=False
        )
        embed.add_field(name="👥 Participantes confirmados", value="0", inline=False)
        embed.set_footer(text=f"Plan creado por {interaction.user}", icon_url=interaction.user.avatar)
        embed.timestamp = discord.utils.utcnow()

        msg = await interaction.channel.send(embed=embed)
        await msg.add_reaction(EMOJI_PARTICIPAR)

        planes_activos[msg.id] = {"msg": msg, "usuarios": set(), "embed": embed}

        await interaction.response.send_message(
            "📡 Plan enviado — los miembros pueden reaccionar para unirse.",
            ephemeral=True
        )

        await asyncio.sleep(900)
        try:
            await msg.delete()
        except:
            pass
        planes_activos.pop(msg.id, None)


@bot.command()
async def plan(ctx):
    if ctx.channel.id != CANAL_PLANES:
        aviso = await ctx.reply(f"⛔ Este comando solo puede usarse en <#{CANAL_PLANES}>.")
        await asyncio.sleep(5)
        await aviso.delete()
        await ctx.message.delete()
        return

    if ctx.author.id not in USERS_ALLOWED_PLAN:
        return await ctx.reply("⛔ No tienes permiso para planear atracos.", delete_after=7)

    class ViewBotonPlan(discord.ui.View):
        @discord.ui.button(label="📋 Crear plan de atraco", style=discord.ButtonStyle.red)
        async def abrir_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(ModalPlan())

    await ctx.send("🕵️ Pulsa el botón para crear un plan de atraco:", view=ViewBotonPlan(), delete_after=60)


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

# ─────────────────────────────────────────────
# SISTEMA PRECIOS ARMAS
# ─────────────────────────────────────────────

CANAL_PRECIOS_ARM = 1442783256704712795
USERS_ALLOWED_PRECIOS = [352471626400661514, 352471626400661514]

IMG_0  = "https://i.imgur.com/BWLOxla.png"
IMG_20 = "https://i.imgur.com/ediQEet.png"
IMG_25 = "https://i.imgur.com/eXVpoQN.png"
IMG_30 = "https://i.imgur.com/AAqnNcQ.png"


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

        match self.values[0]:
            case "0% DESCUENTO":
                img = IMG_0
            case "20% DESCUENTO":
                img = IMG_20
            case "25% DESCUENTO":
                img = IMG_25
            case "30% DESCUENTO":
                img = IMG_30
            case _:
                img = IMG_0

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


class ViewPrecios(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectPrecios())


async def publicar_menu_precios():
    canal = bot.get_channel(CANAL_PRECIOS_ARM)
    if not canal:
        print("⚠ CANAL_PRECIOS_ARM no encontrado")
        return

    async for msg in canal.history(limit=500):
        if msg.author == bot.user:
            try:
                await msg.delete()
            except:
                pass

    embed = discord.Embed(
        title="🔫 PRECIO DE ARMAS 🔫",
        description="Selecciona tu descuento.\n📩 La tabla se enviará **por mensaje privado**.",
        color=discord.Color.dark_red()
    )

    await canal.send(embed=embed, view=ViewPrecios())
    print("✔ Menú de precios publicado")


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

# ─────────────────────────────────────────────
# FILTRO DE MENSAJES / SOLO COMANDOS
# ─────────────────────────────────────────────

CANALES_SOLO_COMANDOS = [
    1442618930291281960,
    234567890123456789,
]


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    if message.content.startswith("!"):
        await message.delete(delay=10)
        await bot.process_commands(message)
        return

    if message.channel.id in CANALES_SOLO_COMANDOS:
        try:
            await message.delete()
        except:
            pass
        return

    await bot.process_commands(message)

# ─────────────────────────────────────────────
# SISTEMA VERIFICACIÓN IDENTIDAD
# ─────────────────────────────────────────────

CANAL_VERIFICACION = 1442810380446335036
ROL_VERIFICADO = 1415492409269424214


class ModalVerificacion(Modal, title="📋 Verificación de identidad"):
    nombre = TextInput(label="Nombre (solo una palabra)", required=True)
    apellido = TextInput(label="Apellido (solo una palabra)", required=True)
    codigo = TextInput(label="ID numérica (2–6 dígitos)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        nombre = self.nombre.value.strip()
        apellido = self.apellido.value.strip()
        codigo = self.codigo.value.strip()

        if not re.match(r"^[A-Za-zÀ-ÿ]+$", nombre):
            return await interaction.response.send_message(
                "❌ El **nombre** debe ser una sola palabra y solo letras.",
                ephemeral=True
            )

        if not re.match(r"^[A-Za-zÀ-ÿ]+$", apellido):
            return await interaction.response.send_message(
                "❌ El **apellido** debe ser una sola palabra y solo letras.",
                ephemeral=True
            )

        if not re.match(r"^\d{2,6}$", codigo):
            return await interaction.response.send_message(
                "❌ El **ID** debe contener solo números y tener **entre 2 y 6 dígitos**.",
                ephemeral=True
            )

        nuevo_nombre = f"{nombre} {apellido} | {codigo}"

        await interaction.response.send_message(
            "🔓 **Verificación completada correctamente.** Bienvenido al servidor.",
            ephemeral=True
        )

        rol = interaction.guild.get_role(ROL_VERIFICADO)
        if rol:
            try:
                await interaction.user.add_roles(rol, reason="Verificación completada")
            except:
                print("⚠ No se pudo asignar el rol")

        try:
            await interaction.user.edit(nick=nuevo_nombre)
        except:
            print("⚠ No se pudo cambiar el nickname (quizás falta permiso)")


class BotonVerificarIdentidad(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="📌 Verificar identidad",
        style=discord.ButtonStyle.green
    )
    async def abrir_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalVerificacion())


async def publicar_mensaje_permanente():
    canal = bot.get_channel(CANAL_VERIFICACION)
    if not canal:
        print("⚠ El canal de verificación no se encontró")
        return

    async for msg in canal.history(limit=50):
        if msg.author == bot.user:
            try:
                await msg.delete()
            except:
                pass

    embed = discord.Embed(
        title="🔒 VERIFICACIÓN OBLIGATORIA",
        description="Para acceder al servidor debes **verificar tu identidad**.\n\n"
                    "Pulsa el botón de abajo para continuar.\n"
                    "📌 **Formato obligatorio:** Nombre + Apellido + Código",
        color=discord.Color.gold(),
    )
    embed.set_footer(text="Sistema automático de verificación")

    await canal.send(embed=embed, view=BotonVerificarIdentidad())
    print("✔ Mensaje de verificación publicado nuevamente")


@bot.command()
async def verificar(ctx):
    if ctx.channel.id != CANAL_VERIFICACION:
        await ctx.reply("⛔ Solo puedes usar este comando en el canal de verificación.", delete_after=6)
        await ctx.message.delete()
        return

    await publicar_mensaje_permanente()
    await ctx.message.delete()

# ─────────────────────────────────────────────
# SISTEMA VALIDACIÓN RETIROS
# ─────────────────────────────────────────────

LOG_CHANNEL = 1444293463670788206        # canal donde se envía lo que escribe el usuario
VERIFY_CHANNEL = 1417317069124272250     # canal donde habla el otro bot


def normalize(text: str):
    text = text.strip().lower()
    text = ''.join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return text


class RetiroModal(discord.ui.Modal, title="Verificar Retiro"):
    pasaporte = discord.ui.TextInput(label="Pasaporte", required=True)
    item = discord.ui.TextInput(label="Ítem retirado", required=True)
    fecha = discord.ui.TextInput(label="Fecha (DD/MM/AAAA)", required=True)
    hora = discord.ui.TextInput(label="Hora (HH:MM)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        log_channel = bot.get_channel(LOG_CHANNEL)
        if log_channel:
            await log_channel.send(
                f"📌 Registro de Retiro:\n"
                f"👤 Pasaporte: {self.pasaporte.value}\n"
                f"📦 Ítem: {self.item.value}\n"
                f"📅 Fecha: {self.fecha.value}\n"
                f"⏰ Hora: {self.hora.value}"
            )

        await interaction.response.send_message("⏳ Verificando información, un momento...", ephemeral=True)

        await asyncio.sleep(10)

        canal_verificacion = bot.get_channel(VERIFY_CHANNEL)
        if not canal_verificacion:
            return await interaction.followup.send("❌ Canal de verificación no configurado.", ephemeral=True)

        async for mensaje in canal_verificacion.history(limit=1):
            contenido = mensaje.content
            break
        else:
            return await interaction.followup.send("❌ No hay mensajes para verificar.", ephemeral=True)

        usr_pasaporte = normalize(self.pasaporte.value)
        usr_item = normalize(self.item.value)
        usr_fecha = normalize(self.fecha.value)
        usr_hora = normalize(self.hora.value)

        texto = normalize(contenido)

        match_pasaporte = usr_pasaporte in texto
        match_item = usr_item in texto
        match_fecha = usr_fecha in texto
        match_hora = usr_hora in texto

        if match_pasaporte and match_item and match_fecha and match_hora:
            resultado = "🟢 **VALIDADO** – Coinciden todos los datos."
        else:
            resultado = "🔴 **NO COINCIDE** – La información no coincide con el registro del otro bot."

        await interaction.followup.send(resultado, ephemeral=True)


class BotonVerificarRetiro(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verificar Retiro",
        style=discord.ButtonStyle.green
    )
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RetiroModal())


@bot.command()
async def panel(ctx):
    await ctx.send(
        "📌 **Sistema de Validación de Retiro**\nPulsa el botón para iniciar la verificación:",
        view=BotonVerificarRetiro()
    )

# ─────────────────────────────────────────────
# SISTEMA SORTEO (MANUAL CON !finalizar)
# ─────────────────────────────────────────────

class SorteoModal(discord.ui.Modal, title="Crear Sorteo"):
    premio = discord.ui.TextInput(label="Premio", required=True)
    hora = discord.ui.TextInput(
        label="Hora de entrega (DD/MM HH:MM)",
        placeholder="Ej: 1/12 21:30",
        required=True
    )
    metodo = discord.ui.TextInput(
        label="Método de participación",
        default="Reaccionar con 🎉",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        texto_hora = self.hora.value.strip().replace("  ", " ")

        match = re.match(r"^(\d{1,2})/(\d{1,2}) (\d{2}):(\d{2})$", texto_hora)
        if not match:
            return await interaction.response.send_message(
                "❌ Formato incorrecto. Usa **DD/MM HH:MM**", ephemeral=True
            )

        await interaction.response.send_message(
            f"🎉 **¡SORTEO ABIERTO!** 🎉\n\n"
            f"📦 **Premio:** {self.premio.value}\n"
            f"⏰ **Entrega:** {texto_hora}\n"
            f"🟢 **Para participar reacciona con 🎉**\n\n"
        )

        mensaje = await interaction.original_response()
        await mensaje.add_reaction(EMOJI)


class BotonSorteo(discord.ui.View):
    @discord.ui.button(label="Crear Sorteo", style=discord.ButtonStyle.green)
    async def crear(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SorteoModal())


@bot.command(name="sorteo")
async def sorteo(ctx):
    await ctx.reply(
        "🧾 Pulsa el botón para crear un sorteo:",
        view=BotonSorteo()
    )


@bot.command(name="finalizar")
async def finalizar(ctx, message_id: int):
    try:
        mensaje = await ctx.channel.fetch_message(message_id)
    except:
        return await ctx.reply("❌ No se pudo encontrar ese mensaje.")

    reaction = discord.utils.get(mensaje.reactions, emoji=EMOJI)
    if not reaction:
        return await ctx.reply("❌ El mensaje no tiene reacciones del sorteo.")

    usuarios = [u async for u in reaction.users()]
    participantes = [u for u in usuarios if not u.bot]

    if not participantes:
        return await ctx.reply("❌ Nadie participó en el sorteo.")

    ganador = random.choice(participantes)
    await ctx.send(
        f"🏆 **¡TENEMOS GANADOR DEL SORTEO!** 🏆\n\n"
        f"🎉 Felicidades <@{ganador.id}>!\n"
        f"📦 Premio obtenido del sorteo.\n"
        f"🪄 ID del sorteo: `{message_id}`"
    )

# ---------- CONFIG: ajusta estos IDs ----------
LOG_CHANNEL_RECEPCION = 1448631419982053377  # <-- canal donde guardar registros de "recepción"
LOG_CHANNEL_ENTREGA   = 1448631483920023632  # <-- canal donde guardar registros de "entrega realizada"
ROLE_ALLOWED_ID       = 1442629004518756412  # <-- solo miembros con este rol pueden usar el modal de recepción
# ----------------------------------------------

def normalize_text(t: str) -> str:
    t = (t or "").strip()
    return ''.join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")

async def resolve_member_from_mention(interaction: discord.Interaction, raw: str):
    """Extrae ID numérico de una mención o número crudo. Devuelve (Member|None, display_string)."""
    m = re.search(r"(\d{5,20})", (raw or ""))
    if m:
        user_id = int(m.group(1))
        try:
            member = interaction.guild.get_member(user_id) or await interaction.guild.fetch_member(user_id)
            return member, member.mention if member else f"<@{user_id}>"
        except Exception:
            return None, f"<@{user_id}>"
    # No contiene ID, devolver raw tal cual
    return None, raw

# ---------- MODAL 1: Recepción (solo rol permitido para abrir) ----------
class ModalRecepcion(ui.Modal, title="📥 Registrar RECEPCIÓN"):
    id_jugador = ui.TextInput(label="ID jugador (juego)", placeholder="Ej: 28399", required=True)
    discord_user = ui.TextInput(label="ID o mención de Discord", placeholder="Ej: <@1234567890> o 1234567890", required=True)
    cantidad = ui.TextInput(label="Cantidad de droga recibida", placeholder="Ej: 60 coca", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        # enviar al canal LOG_CHANNEL_RECEPCION
        log_channel = bot.get_channel(LOG_CHANNEL_RECEPCION)
        id_juego = self.id_jugador.value.strip()
        raw_mention = self.discord_user.value.strip()
        cantidad = self.cantidad.value.strip()

        member, display = await resolve_member_from_mention(interaction, raw_mention)

        embed = Embed(title="📥 RECEPCIÓN registrada", color=discord.Color.green(), timestamp=discord.utils.utcnow())
        embed.add_field(name="ID jugador (juego)", value=id_juego, inline=True)
        embed.add_field(name="Usuario (Discord)", value=display, inline=True)
        embed.add_field(name="Cantidad recibida", value=cantidad, inline=False)
        embed.set_footer(text=f"Registrado por {interaction.user}", icon_url=interaction.user.display_avatar.url)

        try:
            if log_channel:
                await log_channel.send(embed=embed)
            else:
                # fallback: enviar al canal donde se ejecutó (no ideal)
                await interaction.channel.send(embed=embed)
            await interaction.response.send_message("✅ Recepción registrada y enviada a logs.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error al enviar el registro: {e}", ephemeral=True)

# ---------- MODAL 2: Entrega realizada ----------
class ModalEntregaRealizada(ui.Modal, title="📤 Registrar ENTREGA realizada"):
    id_jugador = ui.TextInput(label="ID jugador (juego)", placeholder="Ej: 28399", required=True)
    discord_user = ui.TextInput(label="ID o mención de Discord", placeholder="Ej: <@1234567890> o 1234567890", required=True)
    cantidad = ui.TextInput(label="Cantidad de droga entregada", placeholder="Ej: 60 Coca", required=True)
    cantidad_dinero = ui.TextInput(label="Cantidad de dinero recibido", placeholder="Ej: 1000000$", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        log_channel = bot.get_channel(LOG_CHANNEL_ENTREGA)
        id_juego = self.id_jugador.value.strip()
        raw_mention = self.discord_user.value.strip()
        cantidad = self.cantidad.value.strip()
        cantidad_dinero = self.cantidad_dinero.value.strip()

        member, display = await resolve_member_from_mention(interaction, raw_mention)

        embed = Embed(title="📤 ENTREGA registrada", color=discord.Color.orange(), timestamp=discord.utils.utcnow())
        embed.add_field(name="ID jugador (juego)", value=id_juego, inline=True)
        embed.add_field(name="Usuario (Discord)", value=display, inline=True)
        embed.add_field(name="Cantidad entregada", value=cantidad, inline=True)
        embed.add_field(name="Dinero Recibido", value=cantidad_dinero, inline=False)
        embed.set_footer(text=f"Registrado por {interaction.user}", icon_url=interaction.user.display_avatar.url)

        try:
            if log_channel:
                await log_channel.send(embed=embed)
            else:
                await interaction.channel.send(embed=embed)
            await interaction.response.send_message("✅ Entrega registrada y enviada a logs.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error al enviar el registro: {e}", ephemeral=True)

# ---------- VIEW con los 2 botones ----------
class ViewEntregas(ui.View):
    def __init__(self, timeout: float | None = None):
        super().__init__(timeout=timeout)

    @ui.button(label="📥 Registrar RECEPCIÓN", style=discord.ButtonStyle.green, custom_id="btn_recepcion_entrega")
    async def boton_recepcion(self, interaction: discord.Interaction, button: ui.Button):
        # comprobar rol del usuario antes de abrir modal
        has_role = any(r.id == ROLE_ALLOWED_ID for r in getattr(interaction.user, "roles", []))
        if not has_role:
            return await interaction.response.send_message("⛔ No tienes permiso para registrar recepciones.", ephemeral=True)

        await interaction.response.send_modal(ModalRecepcion())

    @ui.button(label="📤 Registrar ENTREGA realizada", style=discord.ButtonStyle.blurple, custom_id="btn_entrega_realizada")
    async def boton_entrega(self, interaction: discord.Interaction, button: ui.Button):
        # este botón puede usarlo cualquiera (o añade otra comprobación si quieres)
        await interaction.response.send_modal(ModalEntregaRealizada())

# ---------- comando que publica el mensaje con los 2 botones ----------
@bot.command(name="entrega")
async def comando_entrega(ctx: commands.Context):
    vista = ViewEntregas(timeout=None)  # timeout=None para que la view funcione indefinidamente
    await ctx.send("📦 Panel de entregas — elige una acción:", view=vista)

@bot.command()
@commands.has_permissions(administrator=True)  # ❗ Quita esta línea si NO quieres limitar a admins
async def clearall(ctx):
    await ctx.send("🧹 Borrando todos los mensajes…", delete_after=2)

    try:
        await ctx.channel.purge(limit=None)
    except Exception as e:
        return await ctx.send(f"❌ Error al borrar mensajes: {e}", delete_after=5)

    await ctx.send("✅ **Canal limpiado por completo**.", delete_after=3)

@bot.command(name="ayuda")
async def help_command(ctx):
    embed = discord.Embed(
        title="📖 AYUDA DEL BOT",
        description="Lista completa de comandos disponibles.\n"
                    "Algunos comandos pueden requerir permisos especiales o canales específicos.",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="👋 Comandos generales",
        value=(
            "`!hola` → Saludo del bot\n"
            "`!help` → Muestra este menú de ayuda"
        ),
        inline=False
    )

    embed.add_field(
        name="🤝 Sistema de Alianzas",
        value=(
            "`!setalianzas` → Crear nueva alianza (usuarios autorizados)\n"
            "`!editaralianzas <ID>` → Editar una alianza existente\n"
            "`!deletealianza <ID>` → Eliminar una alianza\n"
            "📌 El menú de alianzas se gestiona automáticamente"
        ),
        inline=False
    )

    embed.add_field(
        name="🔫 Planes de Atraco",
        value=(
            "`!plan` → Crear un plan de atraco (canal específico)\n"
            "🔫 Reacciona para unirte al plan\n"
            "⏱️ Los planes se eliminan automáticamente"
        ),
        inline=False
    )

    embed.add_field(
        name="💰 Precios de Armas",
        value=(
            "`!preciosarm` → Publica el menú de precios\n"
            "📩 Las tablas se envían por mensaje privado"
        ),
        inline=False
    )

    embed.add_field(
        name="🔒 Verificación de Identidad",
        value=(
            "`!verificar` → Publica el panel de verificación\n"
            "🆔 Formato: Nombre + Apellido + Código"
        ),
        inline=False
    )

    embed.add_field(
        name="📦 Validación de Retiros",
        value=(
            "`!panel` → Abrir panel de verificación de retiros\n"
            "🔍 El sistema compara con el registro de otro bot"
        ),
        inline=False
    )

    embed.add_field(
        name="🎉 Sorteos",
        value=(
            "`!sorteo` → Crear un sorteo\n"
            "`!finalizar <ID mensaje>` → Finalizar sorteo y elegir ganador\n"
            "🎉 Participación mediante reacción"
        ),
        inline=False
    )

    embed.add_field(
        name="🚚 Entregas",
        value=(
            "`!entrega` → Abrir panel de entregas\n"
            "📥 Registrar recepción (requiere rol)\n"
            "📤 Registrar entrega realizada"
        ),
        inline=False
    )

    embed.add_field(
        name="🧹 Administración",
        value=(
            "`!clearall` → Borra todos los mensajes del canal (admin)"
        ),
        inline=False
    )

    embed.set_footer(
        text=f"Solicitado por {ctx.author}",
        icon_url=ctx.author.display_avatar.url
    )

    await ctx.send(embed=embed, delete_after=120)

# ─────────────────────────────────────────────
# ON_READY: ACTUALIZAR CANALES AUTOMÁTICAMENTE
# ─────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"🤖 Bot conectado como {bot.user}")

    await asyncio.sleep(5)

    try:
        await publicar_mensaje_permanente()
        print("🔄 Verificación restaurada")
    except Exception as e:
        print(f"⚠ Error al restaurar verificación: {e}")

    try:
        await publicar_menu()
        print("🔄 Alianzas restauradas")
    except Exception as e:
        print(f"⚠ Error al restaurar alianzas: {e}")

    try:
        await publicar_menu_precios()
        print("🔄 Precios restaurados")
    except Exception as e:
        print(f"⚠ Error al restaurar precios: {e}")

    print("✔ Todos los sistemas han sido restaurados correctamente")


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

bot.run(os.getenv("DISCORD_TOKEN2"))
