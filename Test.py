import discord
from discord.ext import commands
from discord import app_commands, ui
import asyncio
import os
from flask import Flask
from threading import Thread

# --- CONFIGURAÇÕES ---
TOKEN = os.getenv("DISCORD_TOKEN")
ID_CARGO_SEM_REGISTRO = 1418396595153539248
ID_CARGO_APROVADOR = 1401064899597172746
ID_CANAL_APROVACAO = 1418396682093330493
ID_CANAL_BEMVINDO = 1418396564342177813
URL_IMAGEM_BEMVINDO = "https://cdn.discordapp.com/attachments/1418369933951238342/1418373459951620136/unnamed.png?ex=68cde2b8&is=68cc9138&hm=93fc8e238c1eb5ffd70c846d0a07263fa5399c77683298284afb06a0448426c8&"

# URL fixa para a imagem do painel de registro
# (Esta imagem foi removida do painel, mas a variável pode ser usada se você quiser adicionar a imagem de volta no futuro)
URL_IMAGEM_REGISTRO = "URL_DA_SUA_IMAGEM_FIXA_PARA_O_REGISTRO_AQUI" 

# Dicionário de Patentes...
PATENTES_E_CARGOS = {
    # ... seu dicionário de patentes ...
}

# --- As classes do bot (Views, Modal) ---
class FormularioRegistro(ui.Modal, title="Registro - Etapa 2/2: Nome"):
    # ... (código da classe igual)
    def __init__(self, patente_selecionada: str):
        super().__init__()
        self.patente_selecionada = patente_selecionada
    nome = ui.TextInput(label="Qual o seu nome no jogo/personagem?", style=discord.TextStyle.short, required=True, max_length=50)
    async def on_submit(self, interaction: discord.Interaction):
        # ... (código do on_submit igual)
        
class ViewSelecaoPatente(ui.View):
    # ... (código da classe igual)
    def __init__(self):
        super().__init__(timeout=180)
    @ui.select(
        placeholder="Selecione sua patente - Etapa 1/2",
        options=[discord.SelectOption(label=patente) for patente in PATENTES_E_CARGOS.keys()]
    )
    async def select_callback(self, interaction: discord.Interaction, select: ui.Select):
        patente_escolhida = select.values[0]
        await interaction.response.send_modal(FormularioRegistro(patente_selecionada=patente_escolhida))

# --- RE-ADICIONADO: A VIEW COM O BOTÃO "INICIAR REGISTRO" ---
class ViewIniciarRegistro(ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Botão permanente

    @ui.button(label="Iniciar Registro", style=discord.ButtonStyle.primary, custom_id="iniciar_registro_persistente")
    async def iniciar(self, interaction: discord.Interaction, button: ui.Button):
        # Verifica se o usuário já está registrado
        cargo_sem_registro = interaction.guild.get_role(ID_CARGO_SEM_REGISTRO)
        if cargo_sem_registro not in interaction.user.roles:
            await interaction.response.send_message("Você já está registrado!", ephemeral=True)
            return

        # Envia o menu de seleção de patente de forma privada
        await interaction.response.send_message(
            content="Por favor, selecione sua patente abaixo para começar.",
            view=ViewSelecaoPatente(),
            ephemeral=True
        )

class ViewAprovacao(ui.View):
    # ... (código da classe igual)
    def __init__(self, membro_id: int, nome: str, patente: str):
        super().__init__(timeout=None)
        # ... (resto do init igual)
    @ui.button(label="Aceitar", style=discord.ButtonStyle.success, custom_id="aceitar_registro")
    async def aceitar(self, interaction: discord.Interaction, button: ui.Button):
        # ... (código de aceitar igual)
    @ui.button(label="Reprovar", style=discord.ButtonStyle.danger, custom_id="reprovar_registro")
    async def reprovar(self, interaction: discord.Interaction, button: ui.Button):
        # ... (código de reprovar igual)

# --- CÓDIGO PRINCIPAL DO BOT ---
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} está online!')
    # --- ALTERADO: Adicionamos a View do botão de registro de volta ---
    bot.add_view(ViewIniciarRegistro())
    bot.add_view(ViewAprovacao(membro_id=0, nome="", patente=""))
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos.")
    except Exception as e:
        print(e)

@bot.event
async def on_member_join(member):
    # ... (código do on_member_join igual)

# O comando /registrar foi removido

# --- RE-ADICIONADO: O COMANDO DE ADMIN /enviar_registro ---
@bot.tree.command(name="enviar_registro", description="Envia o painel de registro fixo neste canal.")
@app_commands.checks.has_permissions(administrator=True)
async def enviar_registro(interaction: discord.Interaction):
    # Criamos o Embed sem a imagem, como no seu primeiro print
    embed = discord.Embed(
        title="Registre-se",
        description="Seja bem-vindo à mais nobre elite da Cavalaria de Atlanta — onde honra, força e bravura marcham lado a lado.",
        color=discord.Color.dark_gold() # Você pode mudar a cor aqui se quiser
    )
    
    # Envia o painel com o Embed e o botão "Iniciar Registro"
    await interaction.channel.send(embed=embed, view=ViewIniciarRegistro())
    await interaction.response.send_message("Painel de registro enviado!", ephemeral=True)

# --- Código do servidor web para manter o bot online 24/7 ---
# ... (código do keep_alive igual)
app = Flask('')
@app.route('/')
def home():
    return "Servidor do bot está ativo."
def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- LIGA O BOT ---
keep_alive()
bot.run(TOKEN)
