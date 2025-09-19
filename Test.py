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

# Dicionário para mapear o NOME da patente para o ID do CARGO
PATENTES_E_CARGOS = {
    "Recruta Tx": 1387981757177004137,
    "Soldado Tx": 1387981756182823046,
    "Cabo Tx": 1387991889512501410,
    "3° Sargento Tx": 1387981755763658802,
    "2° Sargento Tx": 1387981755763658802,
    "1° Sargento Tx": 1387981755763658802,
    "Subtenente Tx": 1401423197936549930,
    "2° Tenente Tx": 1387981754559893626,
    "1° Tenente Tx": 1387981754559893626,
    "Capitã Tx": 1387981753569902804,
    "Capitão Tx": 1387981753569902804,
    "Sheriff": 1418429757607116820,
    "Major Tx": 1400245578939764736,
    "Tenente-Coronel": 1418429605303549992,
    "Coronel": 1418429367368810527,
    "Us Marshal": 1418429498034094230,
}

# --- CLASSES DO BOT ---

class FormularioRegistro(ui.Modal, title="Registro - Etapa 2/2: Nome"):
    def __init__(self, patente_selecionada: str):
        super().__init__()
        self.patente_selecionada = patente_selecionada

    nome = ui.TextInput(label="Qual o seu nome no jogo/personagem?", style=discord.TextStyle.short, required=True, max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        nome_usuario = self.nome.value
        patente_escolhida = self.patente_selecionada
        canal_aprovacao = interaction.guild.get_channel(ID_CANAL_APROVACAO)
        if not canal_aprovacao:
            await interaction.response.send_message("Erro: Canal de aprovação não encontrado.", ephemeral=True)
            return
        
        embed_aprovacao = discord.Embed(
            title="Novo Registro Pendente",
            description=f"O membro **{interaction.user.mention}** solicitou o registro.",
            color=discord.Color.gold()
        )
        embed_aprovacao.add_field(name="Nome", value=nome_usuario, inline=False)
        embed_aprovacao.add_field(name="Patente Solicitada", value=patente_escolhida, inline=False)
        embed_aprovacao.set_footer(text=f"ID do Usuário: {interaction.user.id}")
        
        view_aprovacao = ViewAprovacao(membro_id=interaction.user.id, nome=nome_usuario, patente=patente_escolhida)
        await canal_aprovacao.send(embed=embed_aprovacao, view=view_aprovacao)
        await interaction.response.edit_message(content="✅ Seu registro foi enviado para análise. Aguarde a aprovação.", view=None)

class ViewSelecaoPatente(ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @ui.select(
        placeholder="Selecione sua patente - Etapa 1/2",
        options=[discord.SelectOption(label=patente) for patente in PATENTES_E_CARGOS.keys()]
    )
    async def select_callback(self, interaction: discord.Interaction, select: ui.Select):
        patente_escolhida = select.values[0]
        await interaction.response.send_modal(FormularioRegistro(patente_selecionada=patente_escolhida))

class ViewIniciarRegistro(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Iniciar Registro", style=discord.ButtonStyle.primary, custom_id="iniciar_registro_persistente")
    async def iniciar(self, interaction: discord.Interaction, button: ui.Button):
        cargo_sem_registro = interaction.guild.get_role(ID_CARGO_SEM_REGISTRO)
        if cargo_sem_registro not in interaction.user.roles:
            await interaction.response.send_message("Você já está registrado!", ephemeral=True)
            return

        await interaction.response.send_message(
            content="Por favor, selecione sua patente abaixo para começar.",
            view=ViewSelecaoPatente(),
            ephemeral=True
        )

class ViewAprovacao(ui.View):
    def __init__(self, membro_id: int, nome: str, patente: str):
        super().__init__(timeout=None)
        self.membro_id = membro_id
        self.nome = nome
        self.patente = patente

    @ui.button(label="Aceitar", style=discord.ButtonStyle.success, custom_id="aceitar_registro")
    async def aceitar(self, interaction: discord.Interaction, button: ui.Button):
        membro = interaction.guild.get_member(self.membro_id)
        if not membro:
            await interaction.response.send_message("Membro não encontrado no servidor.", ephemeral=True)
            return
            
        cargo_sem_registro = interaction.guild.get_role(ID_CARGO_SEM_REGISTRO)
        id_cargo_patente = PATENTES_E_CARGOS.get(self.patente)
        cargo_patente = interaction.guild.get_role(id_cargo_patente)
        if not cargo_patente:
            await interaction.response.send_message(f"ERRO: O cargo para a patente '{self.patente}' não foi encontrado.", ephemeral=True)
            return
            
        try:
            partes = self.patente.split(' ') 
            if len(partes) > 1:
                patente_formatada = f"{partes[0].capitalize()} {partes[1].upper()}"
            else:
                patente_formatada = self.patente.capitalize()
            novo_apelido = f"{patente_formatada} | {self.nome}"
            await membro.edit(nick=novo_apelido)
            await membro.add_roles(cargo_patente)
            if cargo_sem_registro in membro.roles:
                await membro.remove_roles(cargo_sem_registro)
                
            button.disabled = True
            self.children[1].disabled = True
            await interaction.message.edit(view=self)
            
            await interaction.response.send_message(f"Registro de {membro.mention} aprovado!", ephemeral=True)
            await membro.send(f"Parabéns! Seu registro como **{self.patente}** foi aprovado no servidor {interaction.guild.name}.")
        except Exception as e:
            await interaction.response.send_message(f"Ocorreu um erro ao aprovar: {e}", ephemeral=True)
            print(e)

    @ui.button(label="Reprovar", style=discord.ButtonStyle.danger, custom_id="reprovar_registro")
    async def reprovar(self, interaction: discord.Interaction, button: ui.Button):
        membro = interaction.guild.get_member(self.membro_id)
        button.disabled = True
        self.children[0].disabled = True
        await interaction.message.edit(view=self)
        
        await interaction.response.send_message(f"Registro de {membro.mention if membro else 'ID: '+str(self.membro_id)} reprovado.", ephemeral=True)
        if membro:
            await membro.send(f"Seu registro no servidor {interaction.guild.name} foi reprovado.")

# --- CÓDIGO PRINCIPAL DO BOT ---
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot {bot.user} está online!')
    bot.add_view(ViewIniciarRegistro())
    bot.add_view(ViewAprovacao(membro_id=0, nome="", patente=""))
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos.")
    except Exception as e:
        print(e)

@bot.event
async def on_member_join(member):
    cargo_registro = member.guild.get_role(ID_CARGO_SEM_REGISTRO)
    if cargo_registro:
        await member.add_roles(cargo_registro)
        print(f"Cargo '{cargo_registro.name}' adicionado para {member.name}")

    canal_bemvindo = member.guild.get_channel(ID_CANAL_BEMVINDO)
    if canal_bemvindo:
        frase_bemvindo = (
            "Seja bem-vindo à mais nobre elite da Cavalaria de Atlanta — onde honra, força e bravura marcham lado a lado.\n\n"
            "No coração do deserto, sob o sol escaldante e o faroeste sem lei, cavalgamos unidos como irmãos.\n\n"
            "Somos a Cavalaria: firmes como o aço, rápidos como o vento e leais até o fim da estrada."
        )
        embed_bemvindo = discord.Embed(
            title=f"Saudações, Cavaleiro(a) {member.display_name}!",
            description=frase_bemvindo,
            color=discord.Color.dark_red()
        )
        embed_bemvindo.set_image(url=URL_IMAGEM_BEMVINDO)
        embed_bemvindo.set_thumbnail(url=member.display_avatar.url)
        embed_bemvindo.set_footer(text=f"ID do Usuário: {member.id}")
        await canal_bemvindo.send(content=member.mention, embed=embed_bemvindo)

@bot.tree.command(name="enviar_registro", description="Envia o painel de registro fixo neste canal.")
@app_commands.checks.has_permissions(administrator=True)
async def enviar_registro(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Registre-se",
        description="Seja bem-vindo à mais nobre elite da Cavalaria de Atlanta — onde honra, força e bravura marcham lado a lado.",
        color=discord.Color.dark_gold()
    )
    await interaction.channel.send(embed=embed, view=ViewIniciarRegistro())
    await interaction.response.send_message("Painel de registro enviado!", ephemeral=True)

# --- CÓDIGO DO SERVIDOR WEB PARA MANTER O BOT ONLINE 24/7 ---
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
