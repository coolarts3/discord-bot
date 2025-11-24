import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio

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
    bot.tree.add_command(setalianzas)

    nombre = discord.ui.TextInput(label="Nombre familia", style=discord.TextStyle.short)
    numero = discord.ui.TextInput(label="Número familia", style=discord.TextStyle.short)
    compra = discord.ui.TextInput(label="Descuento en compras (%)", style=discord.TextStyle.short)
    venta = discord.ui.TextInput(label="Descuento en ventas (%)", style=discord.TextStyle.short)
    foto = discord.ui.TextInput(label="URL de imagen de situación (pegar enlace de imagen)", style=discord.TextStyle.short)

    def __init__(self, alianza):
        super().__init__()
        self.alianza = alianza

    async def on_submit(self, interaction: discord.Interaction):
        datos = cargar_datos()
        datos[self.alianza] = {
            "nombre": str(self.nombre),
            "numero": str(self.numero),
            "compra": str(self.compra),
            "venta": str(self.venta),
            "foto": str(self.foto)
        }
        guardar_datos(datos)

        await interaction.response.send_message(f"✅ Alianza **{self.alianza}** registrada correctamente.", ephemeral=True)


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
CANAL_ALIANZAS = 1442610362271797309  # 👈 CAMBIA por la ID del canal permitido


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


@app_commands.command(name="setalianzas", description="Configurar una alianza")
@app_commands.describe(alianza="Nombre de la alianza que deseas configurar")
async def setalianzas(interaction: discord.Interaction, alianza: str):
    bot.tree.add_command(setalianzas)

    # Permitir solo IDs autorizadas
    if interaction.user.id not in USERS_ALLOWED:
        return await interaction.response.send_message("⛔ No tienes permiso para usar este comando.", ephemeral=True)

    alianzas_validas = ["porros", "armas", "lavado dinero", "desguace", "balas", "meta", "tarjetas"]
    alianza = alianza.lower()

    if alianza not in alianzas_validas:
        return await interaction.response.send_message(
            f"⚠️ Alianza no válida.\nOpciones válidas: {', '.join(alianzas_validas)}",
            ephemeral=True
        )

    modal = ModalAlianza(alianza)
    await interaction.response.send_modal(modal)


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
