import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
from discord.ui import Modal, TextInput

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# IDs permitidas para configurar alianzas
USERS_ALLOWED = [682643114560848012, 352471626400661514]  # 👈 Cambia por tus IDs

# archivo donde se guardan los datos
FILE = "alianzas.json"

# si no existe el archivo, lo crea
if not os.path.exists(FILE):
    with open(FILE, "w") as f:
        json.dump({}, f)


def cargar_datos():
    with open(FILE, "r") as f:
        return json.load(f)


def guardar_datos(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=4)


# ---------- MODAL ----------
class ModalAlianza(discord.ui.Modal, title="Registrar Alianza"):
    def __init__(self, alianza):
        super().__init__()
        self.alianza = alianza

        self.nombre = TextInput(label="Nombre de la familia")
        self.numero = TextInput(label="Número de la familia")
        self.foto = TextInput(label="URL de la imagen")
        self.compra = TextInput(label="Descuento en compras (%)")
        self.venta = TextInput(label="Descuento en ventas (%)")

        self.add_item(self.nombre)
        self.add_item(self.numero)
        self.add_item(self.foto)
        self.add_item(self.compra)
        self.add_item(self.venta)

    async def on_submit(self, interaction: discord.Interaction):
        datos = cargar_datos()
        datos[self.alianza] = {
            "nombre": str(self.nombre),
            "numero": str(self.numero),
            "foto": str(self.foto),
            "compra": str(self.compra),
            "venta": str(self.venta)
        }
        guardar_datos(datos)
        await interaction.response.send_message(f"✅ Alianza **{self.alianza}** configurada correctamente.", ephemeral=True)


# ---------- SELECT ----------
class SelectAlianzas(discord.ui.Select):
    def __init__(self):
        opciones = [
            discord.SelectOption(label="porros"),
            discord.SelectOption(label="armas"),
            discord.SelectOption(label="lavado dinero"),
            discord.SelectOption(label="desguace"),
            discord.SelectOption(label="balas"),
            discord.SelectOption(label="meta"),
            discord.SelectOption(label="tarjetas"),
        ]
        super().__init__(placeholder="Selecciona una alianza…", min_values=1, max_values=1, options=opciones)

    async def callback(self, interaction: discord.Interaction):
        alianza = self.values[0]
        datos = cargar_datos()

        if alianza not in datos:
            return await interaction.response.send_message(f"⚠️ La alianza **{alianza}** no está configurada.", ephemeral=True)

        info = datos[alianza]

        embed = discord.Embed(title=f"📌 Datos de la alianza: {alianza}", color=discord.Color.blue())
        embed.add_field(name="🏷️ Nombre familia", value=info["nombre"], inline=False)
        embed.add_field(name="🔢 Número familia", value=info["numero"], inline=False)
        embed.add_field(name="💰 Descuento compras", value=f"{info['compra']}%", inline=True)
        embed.add_field(name="🪙 Descuento ventas", value=f"{info['venta']}%", inline=True)
        embed.set_image(url=info["foto"])
        embed.set_footer(text="Sistema de alianzas")

        await interaction.response.send_message(embed=embed)  # MENSAJE PÚBLICO 👈


class ViewAlianzas(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectAlianzas())


# ---------- COMANDOS ----------

# ID del canal donde se permite usar !alianzas
CANAL_ALIANZAS = 1442618930291281960  # 👈 CAMBIA por la ID del canal permitido


@bot.command()
async def alianzas(ctx):
    # ❌ Si el comando no se usa en el canal correcto
    if ctx.channel.id != CANAL_ALIANZAS:
        aviso = await ctx.reply(f"⛔ Este comando solo puede usarse en <#{CANAL_ALIANZAS}>.")
        await asyncio.sleep(5)
        await aviso.delete()
        await ctx.message.delete()
        return

    # ✔ Si está en el canal correcto
    await ctx.send("📌 Selecciona una alianza en el menú:", view=ViewAlianzas())


@bot.command()
async def setalianzas(ctx, alianza=None):
    if ctx.author.id not in USERS_ALLOWED:
        return await ctx.send("⛔ No tienes permiso para usar este comando.")

    alianzas_validas = ["porros", "armas", "lavado dinero", "desguace", "balas", "meta", "tarjetas"]

    if alianza is None:
        return await ctx.send("⚠️ Uso correcto: `!setalianzas <alianza>`")

    alianza = alianza.lower()
    if alianza not in alianzas_validas:
        return await ctx.send(f"❌ La alianza **{alianza}** no existe.")

    # Enviar un botón que abre el modal
    class OpenModalButton(discord.ui.View):
        @discord.ui.button(label="📋 Abrir formulario", style=discord.ButtonStyle.green)
        async def open(self, interaction: discord.Interaction, button: discord.ui.Button):
            modal = ModalAlianza(alianza)
            await interaction.response.send_modal(modal)

    await ctx.send(f"📝 Pulsa el botón para configurar **{alianza}**:", view=OpenModalButton())

@bot.command()
async def editalianzas(ctx, alianza=None):
    if ctx.author.id not in USERS_ALLOWED:
        return await ctx.send("⛔ No tienes permiso para usar este comando.")

    if alianza is None:
        return await ctx.send("⚠️ Uso correcto: `!editalianzas <alianza>`")

    alianza = alianza.lower()
    datos = cargar_datos()

    if alianza not in datos:
        return await ctx.send(f"❌ La alianza **{alianza}** todavía no está configurada.")

    info = datos[alianza]

    class EditModal(discord.ui.Modal, title=f"Editar {alianza}"):
        nombre = discord.ui.TextInput(label="Nombre familia", default=info["nombre"])
        numero = discord.ui.TextInput(label="Número de familia", default=info["numero"])
        foto = discord.ui.TextInput(label="URL foto", default=info["foto"])
        compra = discord.ui.TextInput(label="Descuento compras", default=info["compra"])
        venta = discord.ui.TextInput(label="Descuento ventas", default=info["venta"])

        async def on_submit(self, interaction: discord.Interaction):
            info["nombre"] = str(self.nombre)
            info["numero"] = str(self.numero)
            info["foto"] = str(self.foto)
            info["compra"] = str(self.compra)
            info["venta"] = str(self.venta)
            guardar_datos(datos)
            await interaction.response.send_message(f"✏️ Alianza **{alianza}** actualizada con éxito.", ephemeral=True)

    class EditButton(discord.ui.View):
        @discord.ui.button(label="✏️ Editar", style=discord.ButtonStyle.primary)
        async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(EditModal())

    await ctx.send(f"🔧 Editar alianza **{alianza}**", view=EditButton())

@bot.command()
async def deletealianzas(ctx, alianza=None):
    if ctx.author.id not in USERS_ALLOWED:
        return await ctx.send("⛔ No tienes permiso para usar este comando.")

    if alianza is None:
        return await ctx.send("⚠️ Uso correcto: `!deletealianzas <alianza>`")

    alianza = alianza.lower()
    datos = cargar_datos()

    if alianza not in datos:
        return await ctx.send(f"❌ La alianza **{alianza}** no está registrada.")

    del datos[alianza]
    guardar_datos(datos)

    await ctx.send(f"🗑️ Alianza **{alianza}** eliminada correctamente.")


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"🌐 Slash commands sincronizados: {len(synced)}")
    except Exception as e:
        print(e)

@bot.command()
async def hola(ctx):
    await ctx.send("👋 Hola, soy el segundo bot.")

import os
bot.run(os.getenv("DISCORD_TOKEN2"))
