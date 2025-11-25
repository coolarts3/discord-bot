import discord
from discord.ext import commands
import os
import asyncio
from discord.ui import View, Modal, TextInput, Select
import sqlite3

class ModalNuevaAlianza(discord.ui.Modal, title="➕ Añadir nueva alianza"):
    familia = TextInput(label="Familia", placeholder="Ej: Los Corleone")
    numero = TextInput(label="Número identificador", placeholder="Ej: 12")
    foto = TextInput(label="URL de la foto", placeholder="https://...")
    compra = TextInput(label="Descuento de compra (%)", placeholder="Ej: 10")
    venta = TextInput(label="Descuento de venta (%)", placeholder="Ej: 15")

    async def on_submit(self, interaction: discord.Interaction):
        guardar_nueva(self.familia.value, self.numero.value, self.foto.value, self.compra.value, self.venta.value)
        await interaction.response.send_message("✔ **Alianza añadida correctamente.**", ephemeral=True)
        await publicar_menu()

class ModalEditarAlianza(discord.ui.Modal, title="📝 Editar alianza"):
    def __init__(self, id_fam, datos):
        super().__init__()
        self.id_fam = id_fam

        self.familia = TextInput(label="Familia", default=datos["familia"])
        self.numero = TextInput(label="Número", default=datos["numero"])
        self.foto = TextInput(label="URL de foto", default=datos["foto"])
        self.compra = TextInput(label="Compra %", default=datos["compra"])
        self.venta = TextInput(label="Venta %", default=datos["venta"])

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
        
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


# ▬▬▬▬▬▬ CONFIG ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
CANAL_ALIANZAS = 1442618930291281960  # ID del canal permanente
USERS_ALLOWED = [352471626400661514, 352471626400661514]  # IDs con permiso
DB = "/storage/alianzas.db"
# ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬

# ▬▬▬▬▬▬ BASE DE DATOS ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
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


# --------------- MENÚ DE SELECCIÓN ---------------
class SelectAlianzas(discord.ui.Select):
    def __init__(self):
        alianzas = obtener_alianzas()

        options = [
            discord.SelectOption(label=f"{row[1]} (#{row[2]})", value=str(row[0]))
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
        embed.set_image(url=info["foto"])
        embed.set_footer(text="Sistema de alianzas")

        msg = await interaction.response.send_message(embed=embed)
        await asyncio.sleep(30)  # segundos antes de borrar
        await msg.delete()


class ViewAlianzas(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SelectAlianzas())


# --------------- PUBLICAR MENSAJE PERMANENTE ---------------
async def publicar_menu():
    canal = bot.get_channel(CANAL_ALIANZAS)
    if not canal:
        print("⚠ Canal no encontrado")
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


# --------------- COMANDO PARA AÑADIR ---------------
@bot.command()
async def setalianzas(ctx):
    if ctx.author.id not in USERS_ALLOWED:
        return await ctx.send("⛔ No tienes permiso.", delete_after=8)

    await ctx.send("📄 Haz clic en el botón para crear una alianza:", view=ViewAbrirModalAlianza(), delete_after=60)


# --------------- COMANDO PARA BORRAR ---------------
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

CANALES_SOLO_COMANDOS = [
    1442618930291281960,   # ID del canal 1
    234567890123456789,   # ID del canal 2
]

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # 🟢 BORRAR comandos "!" después de 10 segundos
    if message.content.startswith("!"):
        await message.delete(delay=10)
        return await bot.process_commands(message)

    # 🔴 BORRAR mensajes que NO sean comandos en canales restringidos
    if message.channel.id in CANALES_SOLO_COMANDOS:
        try:
            await message.delete()
        except:
            pass
        return  # No procesar comandos si no empiezan por "!"

    # NECESARIO para que sigan funcionando los comandos en canales normales
    await bot.process_commands(message)


# ❗ Pon tus IDs aquí
CANAL_VERIFICACION = 1442810380446335036
ROL_VERIFICADO = 1415492409269424214

# Guardamos el mensaje fijo del canal
mensaje_verificacion = None


# ---------- MODAL ----------
import re

class ModalVerificacion(Modal, title="📋 Verificación de identidad"):
    nombre = TextInput(label="Nombre (solo una palabra)", required=True)
    apellido = TextInput(label="Apellido (solo una palabra)", required=True)
    codigo = TextInput(label="ID numérica (2–6 dígitos)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        nombre = self.nombre.value.strip()
        apellido = self.apellido.value.strip()
        codigo = self.codigo.value.strip()

        # VALIDACIONES
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

        # RESPONDEMOS PRIMERO AL USUARIO (obligatorio para evitar errores)
        await interaction.response.send_message(
            "🔓 **Verificación completada correctamente.** Bienvenido al servidor.",
            ephemeral=True
        )

        # LUEGO acciones secundarias (rol y nick)
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


# ---------- BOTÓN DEL MENSAJE PERMANENTE ----------
class BotonVerificar(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📌 Verificar identidad", style=discord.ButtonStyle.green)
    async def abrir_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ModalVerificacion())


# ---------- PUBLICAR MENSAJE PERMANENTE ----------
async def publicar_mensaje_permanente():
    global mensaje_verificacion
    canal = bot.get_channel(CANAL_VERIFICACION)
    if not canal:
        print("⚠ El canal de verificación no se encontró")
        return

    # Eliminar mensajes previos del bot
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

    mensaje_verificacion = await canal.send(embed=embed, view=BotonVerificar())
    print("✔ Mensaje de verificación publicado nuevamente")


# ---------- COMANDO !verificar ----------
@bot.command()
async def verificar(ctx):
    """Vuelve a publicar el mensaje permanente (solo para staff)"""
    if ctx.channel.id != CANAL_VERIFICACION:
        await ctx.reply("⛔ Solo puedes usar este comando en el canal de verificación.", delete_after=6)
        await ctx.message.delete()
        return

    await publicar_mensaje_permanente()
    await ctx.message.delete()


# ---------- AL INICIAR EL BOT ----------
@bot.event
async def on_ready():
    print(f"🤖 Bot conectado como {bot.user}")

    # esperamos 5s para asegurarnos de que Discord cargó todos los canales
    await asyncio.sleep(5)

    # 🔐 VERIFICACIÓN
    try:
        await publicar_mensaje_permanente()
        print("🔄 Verificación restaurada")
    except Exception as e:
        print(f"⚠ Error al restaurar verificación: {e}")

    # 🤝 ALIANZAS
    try:
        await publicar_menu()
        print("🔄 Alianzas restauradas")
    except Exception as e:
        print(f"⚠ Error al restaurar alianzas: {e}")

    # 💰 PRECIOS
    try:
        await publicar_menu_precios()
        print("🔄 Precios restaurados")
    except Exception as e:
        print(f"⚠ Error al restaurar precios: {e}")

    print("✔ Todos los sistemas han sido restaurados correctamente")

# ───── Startup ─────────────────────────────────────────────




bot.run(os.getenv("DISCORD_TOKEN2"))
