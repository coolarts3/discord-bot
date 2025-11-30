import discord
from discord.ext import commands
import os
import asyncio
from discord.ui import View, Modal, TextInput, Select
import sqlite3
from datetime import datetime, timedelta
import random
import re
import unicodedata

EMOJI = "🎉"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ─────────────────────────────────────────────
# SISTEMA DE ALIANZAS
# ─────────────────────────────────────────────
CANAL_ALIANZAS = 1442618930291281960
USERS_ALLOWED = [352471626400661514, 352471626400661514]

DB_FOLDER = "/storage"
DB = f"{DB_FOLDER}/alianzas.db"
os.makedirs(DB_FOLDER, exist_ok=True)

conn = sqlite3.connect(DB)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS alianzas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    familia TEXT,
    numero TEXT,
    foto TEXT,
    compra TEXT,
    venta TEXT
)
""")
conn.commit()
conn.close()

def obtener_alianzas():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, familia, numero FROM alianzas")
    data = cursor.fetchall()
    conn.close()
    return data

def obtener_info(id_familia):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alianzas WHERE id = ?", (id_familia,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "familia": row[1],
        "numero": row[2],
        "foto": row[3],
        "compra": row[4],
        "venta": row[5],
    }

def guardar_nueva(familia, numero, foto, compra, venta):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alianzas (familia, numero, foto, compra, venta)
        VALUES (?, ?, ?, ?, ?)
    """, (familia, numero, foto, compra, venta))
    conn.commit()
    conn.close()

def actualizar_alianza(id_fam, familia, numero, foto, compra, venta):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE alianzas SET familia=?, numero=?, foto=?, compra=?, venta=? WHERE id=?
    """, (familia, numero, foto, compra, venta, id_fam))
    conn.commit()
    conn.close()

def borrar_alianza(id_fam):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM alianzas WHERE id=?", (id_fam,))
    conn.commit()
    conn.close()

class ModalNuevaAlianza(discord.ui.Modal, title="➕ AÑADIR NUEVA ALIANZA"):
    familia = TextInput(label="🔮Familia + Material venta")
    numero = TextInput(label="🔢Número identificador")
    foto = TextInput(label="📎URL de la foto")
    compra = TextInput(label="🔰Descuento de compra (%)")
    venta = TextInput(label="🔰Descuento de venta (%)")

    async def on_submit(self, interaction):
        guardar_nueva(self.familia.value, self.numero.value, self.foto.value, self.compra.value, self.venta.value)
        await interaction.response.send_message("✔ Alianza añadida.", ephemeral=True)
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

        for i in (self.familia, self.numero, self.foto, self.compra, self.venta):
            self.add_item(i)

    async def on_submit(self, interaction):
        actualizar_alianza(self.id_fam, self.familia.value, self.numero.value, self.foto.value, self.compra.value, self.venta.value)
        await interaction.response.send_message("✔ Alianza actualizada.", ephemeral=True)
        await publicar_menu()

class ViewAbrirModalAlianza(discord.ui.View):
    @discord.ui.button(label="➕ Crear nueva alianza", style=discord.ButtonStyle.green)
    async def abrir(self, interaction, button):
        await interaction.response.send_modal(ModalNuevaAlianza())

class ViewEditarAlianza(discord.ui.View):
    def __init__(self, id_fam, datos):
        super().__init__()
        self.id_fam = id_fam
        self.datos = datos

    @discord.ui.button(label="✏ Editar esta alianza", style=discord.ButtonStyle.blurple)
    async def abrir(self, interaction, _):
        await interaction.response.send_modal(ModalEditarAlianza(self.id_fam, self.datos))

class SelectAlianzas(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label=f"{f} (#{n})", value=str(i))
            for i, f, n in obtener_alianzas()
        ]
        super().__init__(placeholder="Selecciona una familia", options=options)

    async def callback(self, interaction):
        info = obtener_info(int(self.values[0]))
        if not info:
            return await interaction.response.send_message("⚠ Ya no existe.", ephemeral=True)

        embed = discord.Embed(
            title=f"📌 Alianza con {info['familia']}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Número", value=info["numero"])
        embed.add_field(name="Compra %", value=info["compra"])
        embed.add_field(name="Venta %", value=info["venta"])
        embed.set_image(url=info["foto"])
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()

        await asyncio.sleep(30)
        try: await msg.delete()
        except: pass

class ViewAlianzas(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectAlianzas())

async def publicar_menu():
    canal = bot.get_channel(CANAL_ALIANZAS)
    if not canal: return

    async for msg in canal.history(limit=200):
        if msg.author == bot.user:
            try: await msg.delete()
            except: pass

    alianzas = obtener_alianzas()
    embed = discord.Embed(title="🤝 LISTA DE ALIANZAS DISPONIBLES", color=discord.Color.gold())
    embed.description = (
        "⚠ No hay alianzas registradas." if not alianzas else
        "📌 Selecciona una familia en el menú de abajo."
    )
    await canal.send(embed=embed, view=ViewAlianzas())

@bot.command()
async def setalianzas(ctx):
    if ctx.author.id not in USERS_ALLOWED:
        return await ctx.send("⛔ No tienes permiso.", delete_after=8)
    await ctx.send("📄 Crea una alianza:", view=ViewAbrirModalAlianza(), delete_after=60)

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
        return await ctx.send("❌ No existe esa alianza.", delete_after=8)

    await ctx.send(
        f"Editando **{datos['familia']}** — pulsa el botón:",
        view=ViewEditarAlianza(int(id_fam), datos),
        delete_after=60
    )

# ─────────────────────────────────────────────
# SISTEMA DE PRECIOS ARMAS
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

    async def callback(self, interaction):
        user = interaction.user
        tabla = {
            "0% DESCUENTO": IMG_0,
            "20% DESCUENTO": IMG_20,
            "25% DESCUENTO": IMG_25,
            "30% DESCUENTO": IMG_30
        }[self.values[0]]

        try:
            embed = discord.Embed(color=discord.Color.dark_red())
            embed.set_image(url=tabla)
            await user.send(f"🔫 Tabla de precios {self.values[0]}", embed=embed)
            await interaction.response.send_message("📬 ¡Revisá tus MD!", ephemeral=True)
        except:
            await interaction.response.send_message("⚠ No puedo enviarte MD.", ephemeral=True)

class ViewPrecios(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectPrecios())

async def publicar_menu_precios():
    canal = bot.get_channel(CANAL_PRECIOS_ARM)
    if not canal: return

    async for msg in canal.history(limit=500):
        if msg.author == bot.user:
            try: await msg.delete()
            except: pass

    embed = discord.Embed(
        title="🔫 PRECIO DE ARMAS 🔫",
        description="Selecciona tu descuento. La tabla se enviará por MD.",
        color=discord.Color.dark_red()
    )
    await canal.send(embed=embed, view=ViewPrecios())

@bot.command()
async def preciosarm(ctx):
    if ctx.author.id not in USERS_ALLOWED_PRECIOS:
        return await ctx.reply("⛔ Sin permiso.", delete_after=8)
    if ctx.channel.id != CANAL_PRECIOS_ARM:
        aviso = await ctx.reply(f"⛔ Usa este comando en <#{CANAL_PRECIOS_ARM}>.", delete_after=7)
        await asyncio.sleep(5)
        await aviso.delete()
        await ctx.message.delete()
        return
    await publicar_menu_precios()
    await ctx.message.delete()

# ─────────────────────────────────────────────
# SISTEMA DE VERIFICACIÓN IDENTIDAD
# ─────────────────────────────────────────────
CANAL_VERIFICACION = 1442810380446335036
ROL_VERIFICADO = 1415492409269424214

class ModalVerificacion(Modal, title="📋 Verificación de identidad"):
    nombre = TextInput(label="Nombre")
    apellido = TextInput(label="Apellido")
    codigo = TextInput(label="ID numérica (2–6 dígitos)")

    async def on_submit(self, interaction):
        nombre = self.nombre.value.strip()
        apellido = self.apellido.value.strip()
        codigo = self.codigo.value.strip()
        if not re.match(r"^[A-Za-zÀ-ÿ]+$", nombre):
            return await interaction.response.send_message("❌ Nombre inválido.", ephemeral=True)
        if not re.match(r"^[A-Za-zÀ-ÿ]+$", apellido):
            return await interaction.response.send_message("❌ Apellido inválido.", ephemeral=True)
        if not re.match(r"^\d{2,6}$", codigo):
            return await interaction.response.send_message("❌ ID inválida.", ephemeral=True)

        nuevo_nombre = f"{nombre} {apellido} | {codigo}"
        await interaction.response.send_message("🔓 Verificado.", ephemeral=True)

        rol = interaction.guild.get_role(ROL_VERIFICADO)
        if rol:
            try: await interaction.user.add_roles(rol)
            except: pass

        try: await interaction.user.edit(nick=nuevo_nombre)
        except: pass

class BotonVerificarIdentidad(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📌 Verificar identidad", style=discord.ButtonStyle.green)
    async def abrir(self, interaction, _):
        await interaction.response.send_modal(ModalVerificacion())

async def publicar_mensaje_permanente():
    canal = bot.get_channel(CANAL_VERIFICACION)
    if not canal: return
    async for msg in canal.history(limit=50):
        if msg.author == bot.user:
            try: await msg.delete()
            except: pass
    embed = discord.Embed(
        title="🔒 VERIFICACIÓN OBLIGATORIA",
        description="Pulsa el botón para verificarte.\nFormato: Nombre + Apellido + Código",
        color=discord.Color.gold()
    )
    await canal.send(embed=embed, view=BotonVerificarIdentidad())

@bot.command()
async def verificar(ctx):
    if ctx.channel.id != CANAL_VERIFICACION:
        await ctx.reply("⛔ Solo en este canal.", delete_after=6)
        await ctx.message.delete()
        return
    await publicar_mensaje_permanente()
    await ctx.message.delete()

# ─────────────────────────────────────────────
# ⚠ SISTEMA DE VALIDACIÓN DE RETIROS (CLASE RENOMBRADA)
# ─────────────────────────────────────────────
LOG_CHANNEL = 1444293463670788206
VERIFY_CHANNEL = 1417317069124272250

def normalize(text: str):
    text = text.strip().lower()
    return ''.join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")

class RetiroModal(discord.ui.Modal, title="Verificar Retiro"):
    pasaporte = TextInput(label="Pasaporte", required=True)
    item = TextInput(label="Ítem retirado", required=True)
    fecha = TextInput(label="Fecha (DD/MM/AAAA)", required=True)
    hora = TextInput(label="Hora (HH:MM)", required=True)

    async def on_submit(self, interaction):
        log_channel = bot.get_channel(LOG_CHANNEL)
        if log_channel:
            await log_channel.send(
                f"📌 Registro de Retiro:\n"
                f"👤 Pasaporte: {self.pasaporte.value}\n"
                f"📦 Ítem: {self.item.value}\n"
                f"📅 Fecha: {self.fecha.value}\n"
                f"⏰ Hora: {self.hora.value}"
            )

        await interaction.response.send_message("⏳ Verificando...", ephemeral=True)
        await asyncio.sleep(10)

        canal_verificacion = bot.get_channel(VERIFY_CHANNEL)
        if not canal_verificacion:
            return await interaction.followup.send("❌ Canal no configurado.", ephemeral=True)

        async for m in canal_verificacion.history(limit=1):
            contenido = m.content
            break
        else:
            return await interaction.followup.send("❌ No hay mensajes.", ephemeral=True)

        usr = [normalize(x) for x in [self.pasaporte.value, self.item.value, self.fecha.value, self.hora.value]]
        texto = normalize(contenido)

        if all(u in texto for u in usr):
            msg = "🟢 VALIDADO — Coinciden todos los datos."
        else:
            msg = "🔴 NO COINCIDE — Los datos no coinciden."

        await interaction.followup.send(msg, ephemeral=True)

class BotonVerificarRetiro(View):   # ← nombre corregido
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verificar Retiro", style=discord.ButtonStyle.green, custom_id="boton_verificar_retiro")
    async def abrir(self, interaction, _):
        await interaction.response.send_modal(RetiroModal())

@bot.command()
async def panel(ctx):
    await ctx.send("📌 Sistema de validación de retiro — pulsa el botón:", view=BotonVerificarRetiro())

# ─────────────────────────────────────────────
# SISTEMA DE SORTEOS
# ─────────────────────────────────────────────
class SorteoModal(discord.ui.Modal, title="Crear Sorteo"):
    premio = TextInput(label="Premio", required=True)
    hora = TextInput(label="Hora de entrega (DD/MM HH:MM)", required=True)
    metodo = TextInput(label="Método de participación", default="Reaccionar con 🎉")

    async def on_submit(self, interaction):
        match = re.match(r"^(\d{1,2})/(\d{1,2}) (\d{2}):(\d{2})$", self.hora.value.strip())
        if not match:
            return await interaction.response.send_message("❌ Formato incorrecto.", ephemeral=True)

        await interaction.response.send_message(
            f"🎉 **¡SORTEO ABIERTO!** 🎉\n"
            f"📦 Premio: {self.premio.value}\n"
            f"⏰ Entrega: {self.hora.value}\n"
            f"🟢 Reacciona con 🎉 para participar"
        )
        mensaje = await interaction.original_response()
        await mensaje.add_reaction(EMOJI)

class BotonSorteo(discord.ui.View):
    @discord.ui.button(label="Crear Sorteo", style=discord.ButtonStyle.green)
    async def crear(self, interaction, _):
        await interaction.response.send_modal(SorteoModal())

@bot.command(name="sorteo")
async def sorteo(ctx):
    await ctx.reply("🧾 Pulsa el botón para crear un sorteo:", view=BotonSorteo())

@bot.command()
async def finalizar(ctx, message_id: int):
    try:
        mensaje = await ctx.channel.fetch_message(message_id)
    except:
        return await ctx.reply("❌ Mensaje no encontrado.")

    reaction = discord.utils.get(mensaje.reactions, emoji=EMOJI)
    if not reaction:
        return await ctx.reply("❌ Nadie participó.")

    usuarios = [u async for u in reaction.users()]
    participantes = [u for u in usuarios if not u.bot]
    if not participantes:
        return await ctx.reply("❌ Nadie participó.")

    ganador = random.choice(participantes)
    await ctx.send(f"🏆 **GANADOR:** <@{ganador.id}> — ID del sorteo: `{message_id}`")

# ─────────────────────────────────────────────
# ON READY — actualización automática de canales
# ─────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"🤖 Bot conectado como {bot.user}")

    # bot.add_view() para botones persistentes
    bot.add_view(BotonVerificarIdentidad())
    bot.add_view(BotonVerificarRetiro())
    bot.add_view(ViewAlianzas())
    bot.add_view(ViewPrecios())

    await asyncio.sleep(5)

    try: await publicar_mensaje_permanente(); print("🔄 Verificación restaurada")
    except Exception as e: print("⚠ Error al restaurar verificación:", e)

    try: await publicar_menu(); print("🔄 Alianzas restauradas")
    except Exception as e: print("⚠ Error al restaurar alianzas:", e)

    try: await publicar_menu_precios(); print("🔄 Precios restaurados")
    except Exception as e: print("⚠ Error al restaurar precios:", e)

    print("✔ Todos los sistemas cargados correctamente")

bot.run(os.getenv("DISCORD_TOKEN2"))
