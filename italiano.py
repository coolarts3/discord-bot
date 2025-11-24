import discord
from discord.ext import commands
import os
import asyncio
from discord.ui import Modal, TextInput
import sqlite3

# ───── Base de datos ─────────────────────────────────────────────

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


# ───── Bot ─────────────────────────────────────────────

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

USERS_ALLOWED = [682643114560848012, 352471626400661514]  # IDs permitidas
CANAL_ALIANZAS = 1442618930291281960                     # canal permitido !alianzas


# ───── MODAL (Registrar Alianza) ─────────────────────────────────

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
            delete_after=600
        )


# ───── SELECT para mostrar alianzas ─────────────────────────────────

class SelectAlianzas(discord.ui.Select):
    def __init__(self):
        opciones = [
            discord.SelectOption(label=a) for a in
            ["porros", "armas", "lavado dinero", "desguace", "balas", "meta", "tarjetas"]
        ]
        super().__init__(placeholder="Selecciona una alianza…", options=opciones)

    async def callback(self, interaction: discord.Interaction):
        alianza = self.values[0]
        data = cargar_alianza(alianza)

        if not data:
            return await interaction.response.send_message(
                f"⚠️ La alianza **{alianza}** no está configurada.",
                delete_after=10
            )

        embed = discord.Embed(title=f"📌 Datos de la alianza: {alianza}", color=discord.Color.blue())
        embed.add_field(name="🏷️ Nombre familia", value=data["nombre"], inline=False)
        embed.add_field(name="🔢 Número familia", value=data["numero"], inline=False)
        embed.add_field(name="💰 Descuento compras", value=f"{data['compra']}%", inline=True)
        embed.add_field(name="🪙 Descuento ventas", value=f"{data['venta']}%", inline=True)
        embed.set_image(url=data["foto"])
        embed.set_footer(text="Sistema de alianzas")

        await interaction.response.send_message(embed=embed, delete_after=600)


class ViewAlianzas(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(SelectAlianzas())


# ───── COMANDOS ─────────────────────────────────────────────

@bot.command()
async def alianzas(ctx):
    if ctx.channel.id != CANAL_ALIANZAS:
        aviso = await ctx.reply(f"⛔ Este comando solo puede usarse en <#{CANAL_ALIANZAS}>.", delete_after=10)
        await asyncio.sleep(5)
        await ctx.message.delete()
        return

    await ctx.send("📌 Selecciona una alianza:", view=ViewAlianzas(), delete_after=600)


@bot.command()
async def setalianzas(ctx, alianza=None):
    if ctx.author.id not in USERS_ALLOWED:
        return await ctx.send("⛔ No tienes permiso.", delete_after=10)

    alianzas_validas = ["porros", "armas", "lavado dinero", "desguace", "balas", "meta", "tarjetas"]

    if not alianza or alianza.lower() not in alianzas_validas:
        return await ctx.send("⚠️ Uso: `!setalianzas <alianza>`", delete_after=10)

    class OpenModal(discord.ui.View):
        @discord.ui.button(label="📋 Abrir formulario", style=discord.ButtonStyle.green)
        async def open(self, interaction, button):
            await interaction.response.send_modal(EditModal(alianza.lower(), data))

    await ctx.send(f"📝 Configurar **{alianza.lower()}**:", view=OpenModal(), delete_after=30)


@bot.command()
async def editalianzas(ctx, alianza=None):
    if ctx.author.id not in USERS_ALLOWED:
        return await ctx.send("⛔ No tienes permiso.", delete_after=10)

    if not alianza:
        return await ctx.send("⚠️ Uso: `!editalianzas <alianza>`", delete_after=10)

    data = cargar_alianza(alianza.lower())
    if not data:
        return await ctx.send(f"❌ La alianza **{alianza}** no existe.", delete_after=10)

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
    class ButtonEdit(discord.ui.View):
        @discord.ui.button(label="✏️ Editar", style=discord.ButtonStyle.primary)
        async def btn(self, interaction, button):
            await interaction.response.send_modal(EditModal(alianza.lower(), data))

    await ctx.send(f"🔧 Editar alianza **{alianza.lower()}**:", view=ButtonEdit(), delete_after=30)


@bot.command()
async def deletealianzas(ctx, alianza=None):
    if ctx.author.id not in USERS_ALLOWED:
        return await ctx.send("⛔ No tienes permiso.", delete_after=10)

    if not alianza:
        return await ctx.send("⚠️ Uso: `!deletealianzas <alianza>`", delete_after=10)

    if not cargar_alianza(alianza.lower()):
        return await ctx.send(f"❌ La alianza **{alianza}** no existe.", delete_after=10)

    borrar_alianza(alianza.lower())
    await ctx.send(f"🗑️ Alianza **{alianza.lower()}** eliminada.", delete_after=10)


@bot.command()
async def hola(ctx):
    await ctx.send("👋 Hola, soy el segundo bot.", delete_after=10)


# ───── Inicio del bot ─────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"🤖 Bot conectado como {bot.user}")


bot.run(os.getenv("DISCORD_TOKEN2"))
