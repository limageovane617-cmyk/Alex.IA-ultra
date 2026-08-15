# ============================================================
# 🤖 ALEX IA ULTRA
# Aplicativo principal — novo visual de chat
# Criada por Geovani
# ============================================================

import base64
import os
import re
import sys
import importlib
from pathlib import Path

import streamlit as st


# ============================================================
# ⚙️ CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Alex IA Ultra",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# 🖼️ GERENCIADOR DE IMAGENS
# ============================================================

if "gerenciador_imagem" in sys.modules:
    del sys.modules["gerenciador_imagem"]

import gerenciador_imagem
importlib.reload(gerenciador_imagem)

from gerenciador_imagem import mostrar_imagem

from config_ultra import (
    SYSTEM_PROMPT,
    GEMINI_MODEL,
    AI_NAME,
    CREATOR_NAME,
)

from servicos import (
    criar_cliente_gemini,
    verificar_servicos,
)

from memoria import (
    salvar_memoria,
    carregar_memorias,
    apagar_memoria,
    apagar_todas_memorias,
)

from personagens import (
    salvar_personagem,
    carregar_personagem,
    listar_personagens,
    apagar_personagem,
)

from voz import mostrar_audio

from video import (
    gerar_video,
    mostrar_configuracao_video,
    verificar_magic_hour,
)

from arquivos import ler_arquivo

from codigo import (
    preparar_pedido_codigo,
    analisar_codigo,
    listar_linguagens,
)


# ============================================================
# 🧠 ESTADO DA CONVERSA
# ============================================================

DEFAULTS = {
    "mensagens": [],
    "personagem_atual": None,
    "arquivo_contexto": "",
    "arquivo_nome": "",
    "ferramenta_ativa": None,
    "usar_voz": False,
    "ultima_imagem_caminho": None,
}

for chave, valor in DEFAULTS.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor


# ============================================================
# 🔐 SERVIÇOS
# ============================================================

servicos = verificar_servicos()
gemini_disponivel = servicos["gemini"]
huggingface_disponivel = servicos["huggingface"]

if not gemini_disponivel:
    st.error(
        "🔐 A chave GEMINI_API_KEY não está configurada "
        "nos Secrets do Streamlit."
    )
    st.info(
        "Abra os Secrets do seu aplicativo e adicione "
        "GEMINI_API_KEY. Não coloque a chave dentro do app.py."
    )
    st.stop()

cliente = criar_cliente_gemini()

if cliente is None:
    st.error("❌ Não foi possível criar a conexão com o Gemini.")
    st.stop()
    
# ============================================================
# 🔎 TESTE MAGIC HOUR
# ============================================================

def verificar_magic_hour():
    try:
        chave = obter_api_key_magichour()

        if chave:
            return True, "✅ MAGIC_HOUR_API_KEY foi encontrada."
        else:
            return False, "❌ MAGIC_HOUR_API_KEY não foi encontrada."

    except Exception as erro:
        return False, f"❌ Erro ao verificar Magic Hour: {erro}"

# ============================================================
# 🎨 FUNDO + VISUAL DO CHAT
# ============================================================

def imagem_fundo_css():
    """Lê o fundo_chat.jpg do mesmo diretório do app.py."""
    caminho = Path(__file__).with_name("fundo_chat.jpg")

    if not caminho.exists():
        return ""

    try:
        dados = base64.b64encode(caminho.read_bytes()).decode("utf-8")
        return (
            "background-image: "
            f"url(data:image/jpeg;base64,{dados});"
        )
    except Exception:
        return ""


FUNDO_CSS = imagem_fundo_css()

st.markdown(
    f"""
<style>

/* ==========================================================
   BASE
   ========================================================== */

.stApp {{
    {FUNDO_CSS}
    background-size: cover;
    background-position: center center;
    background-attachment: fixed;
    background-repeat: no-repeat;
}}

/* Camada escura para manter o texto legível. */
.stApp::before {{
    content: "";
    position: fixed;
    inset: 0;
    background: rgba(2, 8, 16, 0.68);
    z-index: -1;
    pointer-events: none;
}}

/* Remove o visual branco do conteúdo principal. */
.main .block-container {{
    max-width: 980px;
    padding-top: 1.2rem;
    padding-bottom: 8rem;
}}

/* ==========================================================
   CABEÇALHO
   ========================================================== */

.ultra-header {{
    text-align: center;
    margin: 0 auto 1.2rem auto;
    padding: 0.65rem 1rem;
    border-radius: 22px;
    background: rgba(4, 15, 28, 0.58);
    border: 1px solid rgba(120, 200, 255, 0.16);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    box-shadow: 0 10px 35px rgba(0,0,0,0.28);
}}

.ultra-name {{
    font-size: clamp(25px, 5vw, 39px);
    font-weight: 800;
    letter-spacing: -0.5px;
    margin: 0;
}}

.ultra-subtitle {{
    color: rgba(235,245,255,0.72);
    font-size: 13px;
    margin-top: 2px;
}}

/* ==========================================================
   MENSAGENS — ESTILO CONVERSA
   ========================================================== */

div[data-testid="stChatMessage"] {{
    background: transparent !important;
    border: 0 !important;
    padding: 0.28rem 0 !important;
}}

div[data-testid="stChatMessageContent"] {{
    border-radius: 20px !important;
    padding: 0.72rem 0.95rem !important;
    box-shadow: 0 5px 20px rgba(0,0,0,0.20) !important;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}}

div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) div[data-testid="stChatMessageContent"] {{
    background: rgba(8, 104, 78, 0.90) !important;
    border: 1px solid rgba(76, 236, 184, 0.18) !important;
}}

div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) div[data-testid="stChatMessageContent"] {{
    background: rgba(19, 30, 43, 0.88) !important;
    border: 1px solid rgba(185, 220, 245, 0.12) !important;
}}

/* ==========================================================
   BOTÃO + / MENU DE FERRAMENTAS
   ========================================================== */

button[kind="secondary"] {{
    border-radius: 16px !important;
}}

.tool-label {{
    font-size: 12px;
    color: rgba(235,245,255,0.68);
    margin: 0 0 0.25rem 0;
}}

.tool-panel {{
    margin: 0 auto 0.65rem auto;
    padding: 0.75rem;
    border-radius: 22px;
    background: rgba(8, 17, 29, 0.92);
    border: 1px solid rgba(130, 210, 255, 0.16);
    box-shadow: 0 12px 35px rgba(0,0,0,0.30);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
}}

.tool-title {{
    font-weight: 750;
    font-size: 15px;
    margin-bottom: 0.35rem;
}}

/* ==========================================================
   CHAT INPUT
   ========================================================== */

div[data-testid="stChatInput"] {{
    background: rgba(12, 22, 35, 0.94) !important;
    border: 1px solid rgba(150, 215, 255, 0.20) !important;
    border-radius: 25px !important;
    box-shadow: 0 10px 35px rgba(0,0,0,0.35) !important;
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
}}

div[data-testid="stChatInput"] textarea {{
    color: white !important;
}}

/* ==========================================================
   SIDEBAR — fica disponível, mas fechado por padrão
   ========================================================== */

section[data-testid="stSidebar"] {{
    background: rgba(4, 11, 20, 0.96);
}}

/* ==========================================================
   MOBILE
   ========================================================== */

@media (max-width: 700px) {{
    .main .block-container {{
        padding-left: 0.65rem;
        padding-right: 0.65rem;
        padding-top: 0.65rem;
    }}

    .ultra-header {{
        border-radius: 18px;
        margin-bottom: 0.65rem;
    }}

    div[data-testid="stChatMessageContent"] {{
        border-radius: 18px !important;
    }}
}}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 🤖 CABEÇALHO
# ============================================================

st.markdown(
    f"""
<div class="ultra-header">
    <div class="ultra-name">🤖 {AI_NAME}</div>
    <div class="ultra-subtitle">
        Criada por {CREATOR_NAME} • inteligência artificial pessoal
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# 🧰 FUNÇÕES AUXILIARES DO MENU
# ============================================================

def selecionar_ferramenta(nome):
    st.session_state.ferramenta_ativa = nome


def fechar_ferramenta():
    st.session_state.ferramenta_ativa = None


# ============================================================
# 💬 HISTÓRICO DA CONVERSA
# ============================================================

for indice, mensagem in enumerate(st.session_state.mensagens):
    role = mensagem.get("role", "assistant")
    tipo = mensagem.get("tipo", "texto")

    with st.chat_message(role):
        if tipo == "imagem":
            caminho = mensagem.get("arquivo")
            if caminho and os.path.exists(caminho):
                st.image(caminho, use_container_width=True)
            st.caption(mensagem.get("content", "🖼️ Imagem criada."))

        elif tipo == "video":
            caminho = mensagem.get("arquivo")
            if caminho and os.path.exists(caminho):
                st.video(caminho)
            st.caption(mensagem.get("content", "🎬 Vídeo criado."))

        else:
            st.write(mensagem.get("content", ""))


# ============================================================
# ➕ MENU DE FUNÇÕES
# ============================================================

with st.popover("＋", use_container_width=False):

    st.markdown("### 🧰 Ferramentas da Ultra")
    st.caption("Escolha uma função. O painel aparece acima do campo de conversa.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🖼️ Imagem", use_container_width=True):
            selecionar_ferramenta("imagem")
            st.rerun()

        if st.button("🎬 Vídeo", use_container_width=True):
            selecionar_ferramenta("video")
            st.rerun()

        if st.button("🔊 Voz", use_container_width=True):
            selecionar_ferramenta("voz")
            st.rerun()

        if st.button("💻 Código", use_container_width=True):
            selecionar_ferramenta("codigo")
            st.rerun()

    with col2:
        if st.button("📎 Arquivo", use_container_width=True):
            selecionar_ferramenta("arquivo")
            st.rerun()

        if st.button("🎭 Personagem", use_container_width=True):
            selecionar_ferramenta("personagem")
            st.rerun()

        if st.button("🧠 Memória", use_container_width=True):
            selecionar_ferramenta("memoria")
            st.rerun()

        if st.button("🗑️ Limpar chat", use_container_width=True):
            st.session_state.mensagens = []
            st.rerun()


# ============================================================
# 🛠️ PAINEL DA FERRAMENTA ESCOLHIDA
# ============================================================

ferramenta = st.session_state.ferramenta_ativa

if ferramenta:
    st.markdown('<div class="tool-panel">', unsafe_allow_html=True)

    titulo = {
        "imagem": "🖼️ Criar imagem",
        "video": "🎬 Criar vídeo",
        "voz": "🔊 Voz",
        "codigo": "💻 Programação",
        "arquivo": "📎 Arquivo",
        "personagem": "🎭 Personagem",
        "memoria": "🧠 Memória",
    }.get(ferramenta, "🧰 Ferramenta")

    st.markdown(
        f'<div class="tool-title">{titulo}</div>',
        unsafe_allow_html=True,
    )

    if st.button("✕ Fechar ferramenta", key="fechar_ferramenta"):
        fechar_ferramenta()
        st.rerun()

    # --------------------------------------------------------
    # 🖼️ IMAGEM
    # --------------------------------------------------------
    if ferramenta == "imagem":
        st.caption("Descreva a imagem que você quer criar.")
        prompt_tool = st.text_area(
            "Prompt da imagem",
            key="tool_prompt_imagem",
            placeholder="Ex.: um robô futurista em uma cidade neon...",
            height=100,
        )

        if st.button("🖼️ Gerar imagem", key="gerar_imagem_tool", type="primary"):
            if not prompt_tool.strip():
                st.warning("Digite o que você quer na imagem.")
            else:
                with st.chat_message("assistant"):
                    st.write("🖼️ Entendi! Vou criar sua imagem agora...")
                    sucesso = mostrar_imagem(prompt_tool.strip())

                caminho = st.session_state.get("ultima_imagem_caminho")

                if sucesso:
                    st.session_state.mensagens.append({
                        "role": "assistant",
                        "content": "🖼️ Imagem criada.",
                        "tipo": "imagem",
                        "arquivo": caminho,
                    })
                    st.session_state.ferramenta_ativa = None
                    st.rerun()
                else:
                    st.session_state.mensagens.append({
                        "role": "assistant",
                        "content": "❌ Não consegui gerar a imagem.",
                    })
                    st.rerun()

    # --------------------------------------------------------
    # 🎬 VÍDEO
    # --------------------------------------------------------
    elif ferramenta == "video":

        st.caption(
            "🎬 Crie um vídeo a partir de uma descrição "
            "ou de uma imagem."
        )

        # ----------------------------------------------------
        # ⚙️ CONFIGURAÇÃO
        # ----------------------------------------------------

        camera_video, proporcao_video, duracao_video = (
            mostrar_configuracao_video()
        )

        # ----------------------------------------------------
        # 🖼️ IMAGEM DE REFERÊNCIA
        # ----------------------------------------------------

        st.markdown("### 🖼️ Imagem para iniciar o vídeo")

        imagem_video = st.file_uploader(
            "📤 Enviar imagem",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp"
            ],
            key="video_imagem_upload",
            help=(
                "Envie uma imagem para o vídeo começar "
                "a partir dela."
            ),
        )

        if imagem_video:

            st.image(
                imagem_video,
                caption="🖼️ Imagem de referência",
                use_container_width=True,
            )

            st.success(
                "✅ Imagem carregada. "
                "O vídeo será baseado nela."
            )

        else:

            st.info(
                "💡 Você também pode gerar um vídeo "
                "sem imagem."
            )

        # ----------------------------------------------------
        # 📝 DESCRIÇÃO
        # ----------------------------------------------------

        descricao_video = st.text_area(
            "📝 Descrição do vídeo",
            key="tool_prompt_video",
            placeholder=(
                "Ex.: a personagem começa a caminhar "
                "lentamente para frente, enquanto a câmera "
                "acompanha suavemente..."
            ),
            height=130,
        )

        # ----------------------------------------------------
        # 🎬 GERAR
        # ----------------------------------------------------

        if st.button(
            "🎬 Gerar vídeo",
            key="gerar_video_tool",
            type="primary",
        ):

            if not descricao_video.strip():

                st.warning(
                    "⚠️ Digite a descrição do que deve "
                    "acontecer no vídeo."
                )

            else:

                # --------------------------------------------
                # 🖼️ PREPARAR IMAGEM
                # --------------------------------------------

                imagem_bytes = None
                nome_imagem = "imagem.png"

                if imagem_video:

                    imagem_bytes = (
                        imagem_video.getvalue()
                    )

                    nome_imagem = (
                        imagem_video.name
                    )

                # --------------------------------------------
                # 🎥 PROMPT CINEMATOGRÁFICO
                # --------------------------------------------

                prompt_video = (
                    descricao_video.strip()
                    + "\n\n"
                    + f"Câmera cinematográfica: {camera_video}."
                    + f"\nProporção desejada: {proporcao_video}."
                    + "\nMovimento natural e cinematográfico."
                    + "\nManter o mesmo personagem, rosto, cabelo, "
                      "roupa, aparência e identidade durante "
                      "toda a cena."
                )

                # --------------------------------------------
                # 🎬 GERAR
                # --------------------------------------------

                with st.spinner(
                    "🎬 Gerando seu vídeo..."
                ):

                    try:

                        resultado_video = gerar_video(
                            prompt=prompt_video,

                            imagem_bytes=imagem_bytes,

                            nome_imagem=nome_imagem,

                            duracao=float(
                                duracao_video
                            ),

                            width=512,

                            height=512,
                        )

                        # ------------------------------------
                        # RESULTADO
                        # ------------------------------------

                        caminho_video = (
                            resultado_video.get(
                                "video"
                            )
                        )

                        motor_video = (
                            resultado_video.get(
                                "motor",
                                "Motor desconhecido"
                            )
                        )

                        if caminho_video:

                            st.success(
                                "🎉 Vídeo gerado com sucesso!"
                            )

                            st.caption(
                                "🎥 Motor utilizado: "
                                + motor_video
                            )

                            st.video(
                                caminho_video
                            )

                            st.session_state.mensagens.append({
                                "role": "assistant",
                                "content": (
                                    "🎬 Vídeo criado com sucesso."
                                ),
                                "tipo": "video",
                                "arquivo": caminho_video,
                            })

                            st.session_state.ferramenta_ativa = None

                            st.rerun()

                        else:

                            st.error(
                                "❌ O vídeo não foi retornado."
                            )

                    except Exception as erro:

                        st.error(
                            "❌ Não foi possível gerar o vídeo."
                        )

                        st.code(
                            str(erro)
                        )

    # --------------------------------------------------------
    # 🔊 VOZ
    # --------------------------------------------------------
    elif ferramenta == "voz":
        st.session_state.usar_voz = st.checkbox(
            "🔊 Ler respostas da Alex em voz",
            value=st.session_state.usar_voz,
            key="tool_checkbox_voz",
        )
        st.info("A voz será usada nas próximas respostas do chat.")

    # --------------------------------------------------------
    # 💻 CÓDIGO
    # --------------------------------------------------------
    elif ferramenta == "codigo":
        linguagem_codigo = st.selectbox(
            "Linguagem",
            listar_linguagens(),
            key="tool_linguagem_codigo",
        )
        st.caption("Você também pode usar `codigo:` diretamente no chat.")

    # --------------------------------------------------------
    # 📎 ARQUIVO
    # --------------------------------------------------------
    elif ferramenta == "arquivo":
        arquivo = st.file_uploader(
            "Enviar arquivo",
            type=["pdf", "txt", "docx"],
            key="tool_arquivo_upload",
        )

        if arquivo and st.button("📥 Ler arquivo", key="ler_arquivo_tool"):
            texto_arquivo, erro_arquivo = ler_arquivo(arquivo)

            if erro_arquivo:
                st.error(f"❌ {erro_arquivo}")
            else:
                st.session_state.arquivo_contexto = texto_arquivo[:50000]
                st.session_state.arquivo_nome = arquivo.name
                st.success("✅ Arquivo carregado e disponível no chat.")

        if st.session_state.arquivo_contexto:
            st.caption(f"📎 {st.session_state.arquivo_nome}")
            if st.button("🗑️ Remover arquivo", key="remover_arquivo_tool"):
                st.session_state.arquivo_contexto = ""
                st.session_state.arquivo_nome = ""
                st.rerun()

    # --------------------------------------------------------
    # 🎭 PERSONAGEM
    # --------------------------------------------------------
    elif ferramenta == "personagem":
        personagens = listar_personagens()
        personagem_selecionado = st.selectbox(
            "Personagem salvo",
            ["Nenhum"] + personagens,
            key="tool_personagem_selecionado",
        )

        dados_personagem = None
        if personagem_selecionado != "Nenhum":
            dados_personagem = carregar_personagem(personagem_selecionado)
            if dados_personagem:
                st.session_state.personagem_atual = dados_personagem

        nome = st.text_input(
            "Nome",
            value=dados_personagem["nome"] if dados_personagem else "",
            key="tool_personagem_nome",
        )
        idade = st.text_input(
            "Idade",
            value=dados_personagem["idade"] if dados_personagem else "",
            key="tool_personagem_idade",
        )
        aparencia = st.text_area(
            "Aparência",
            value=dados_personagem["aparencia"] if dados_personagem else "",
            key="tool_personagem_aparencia",
        )
        roupa = st.text_input(
            "Roupa",
            value=dados_personagem["roupa"] if dados_personagem else "",
            key="tool_personagem_roupa",
        )
        personalidade = st.text_area(
            "Personalidade",
            value=dados_personagem["personalidade"] if dados_personagem else "",
            key="tool_personagem_personalidade",
        )

        if st.button("💾 Salvar personagem", key="salvar_personagem_tool"):
            if not nome.strip():
                st.warning("Digite um nome para o personagem.")
            else:
                salvar_personagem(
                    nome=nome,
                    idade=idade,
                    aparencia=aparencia,
                    roupa=roupa,
                    personalidade=personalidade,
                )
                st.session_state.personagem_atual = {
                    "nome": nome,
                    "idade": idade,
                    "aparencia": aparencia,
                    "roupa": roupa,
                    "personalidade": personalidade,
                }
                st.success("✅ Personagem salvo!")
                st.rerun()

        if personagens:
            apagar = st.selectbox(
                "Apagar personagem",
                ["Nenhum"] + personagens,
                key="tool_apagar_personagem",
            )
            if st.button("🗑️ Apagar personagem", key="apagar_personagem_tool"):
                if apagar != "Nenhum":
                    apagar_personagem(apagar)
                    st.rerun()

    # --------------------------------------------------------
    # 🧠 MEMÓRIA
    # --------------------------------------------------------
    elif ferramenta == "memoria":
        memorias = carregar_memorias()

        st.caption(f"{len(memorias)} memória(s) salva(s)")

        memoria_nova = st.text_area(
            "Salvar nova memória",
            key="tool_memoria_nova",
            placeholder="Ex.: Prefiro que a Ultra responda em português...",
            height=80,
        )

        if st.button("💾 Salvar memória", key="salvar_memoria_tool"):
            if memoria_nova.strip():
                salvar_memoria(memoria_nova.strip())
                st.success("🧠 Memória salva!")
                st.rerun()
            else:
                st.warning("Digite a informação que deseja memorizar.")

        if memorias:
            memoria_apagar = st.selectbox(
                "Escolha uma memória",
                ["Nenhuma"] + memorias,
                key="tool_memoria_apagar",
            )

            if st.button("🗑️ Apagar memória", key="apagar_memoria_tool"):
                if memoria_apagar != "Nenhuma":
                    apagar_memoria(memoria_apagar)
                    st.rerun()

            if st.button("🗑️ Apagar todas as memórias", key="apagar_todas_memorias_tool"):
                apagar_todas_memorias()
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)




# ============================================================
# 💬 CAMPO PRINCIPAL DE CHAT
# ============================================================

pergunta = st.chat_input("Digite sua mensagem para a Alex...")


# ============================================================
# 🚀 PROCESSAMENTO DA MENSAGEM
# ============================================================

if pergunta:
    pergunta = pergunta.strip()

    if not pergunta:
        st.stop()

    st.session_state.mensagens.append({
        "role": "user",
        "content": pergunta,
    })

    # --------------------------------------------------------
    # 🧠 MEMÓRIA DIRETA
    # --------------------------------------------------------
    if pergunta.lower().startswith("memorize:"):
        informacao = pergunta[len("memorize:"):].strip()

        if informacao:
            salvar_memoria(informacao)
            resposta_memoria = "🧠 Pronto! Salvei essa informação na minha memória."
        else:
            resposta_memoria = (
                "Digite depois de `memorize:` a informação que você quer salvar."
            )

        st.session_state.mensagens.append({
            "role": "assistant",
            "content": resposta_memoria,
        })
        st.rerun()

    # --------------------------------------------------------
    # 🖼️ COMANDO DE IMAGEM
    # --------------------------------------------------------
    texto_pergunta = pergunta.lower().strip()

    prefixos_imagem = (
        "imagem:", "gerar imagem", "gere imagem", "gere uma imagem",
        "gerar uma imagem", "crie imagem", "crie uma imagem",
        "criar imagem", "criar uma imagem", "faça imagem", "faca imagem",
        "faça uma imagem", "faca uma imagem", "fazer imagem",
        "fazer uma imagem", "quero uma imagem", "quero criar uma imagem",
        "quero gerar uma imagem", "pode criar uma imagem",
        "pode gerar uma imagem", "pode fazer uma imagem",
        "consegue criar uma imagem", "consegue gerar uma imagem",
        "produza uma imagem", "produzir uma imagem", "desenhe uma imagem",
        "desenhar uma imagem", "crie uma arte", "criar uma arte",
        "gere uma arte", "gerar uma arte", "faça uma arte", "faca uma arte",
        "cria ", "crie ", "criar ", "gera ", "gere ", "gerar ",
        "faz ", "faca ", "faça ", "fazer ", "desenha ", "desenhe ",
        "desenhar ",
    )

    pedido_eh_imagem = texto_pergunta.startswith(prefixos_imagem)

    if pedido_eh_imagem:
        prompt_imagem = pergunta.strip()

        padroes_remover = (
            r"^imagem:\s*",
            r"^gere\s+uma\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^gere\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^gerar\s+uma\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^gerar\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^crie\s+uma\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^crie\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^criar\s+uma\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^criar\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^faça\s+uma\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^faca\s+uma\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^fazer\s+uma\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^fazer\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^quero\s+uma\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^quero\s+criar\s+uma\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^quero\s+gerar\s+uma\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^pode\s+criar\s+uma\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^pode\s+gerar\s+uma\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^pode\s+fazer\s+uma\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^consegue\s+criar\s+uma\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^consegue\s+gerar\s+uma\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^produza\s+uma\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^produzir\s+uma\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^desenhe\s+uma\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^desenhar\s+uma\s+imagem\s*(?:de|do|da|dos|das)?\s*",
            r"^crie\s+uma\s+arte\s*(?:de|do|da|dos|das)?\s*",
            r"^criar\s+uma\s+arte\s*(?:de|do|da|dos|das)?\s*",
            r"^gere\s+uma\s+arte\s*(?:de|do|da|dos|das)?\s*",
            r"^gerar\s+uma\s+arte\s*(?:de|do|da|dos|das)?\s*",
            r"^faça\s+uma\s+arte\s*(?:de|do|da|dos|das)?\s*",
            r"^faca\s+uma\s+arte\s*(?:de|do|da|dos|das)?\s*",
            r"^cria\s+", r"^crie\s+", r"^criar\s+", r"^gera\s+",
            r"^gere\s+", r"^gerar\s+", r"^faz\s+", r"^faca\s+",
            r"^faça\s+", r"^fazer\s+", r"^desenha\s+", r"^desenhe\s+",
            r"^desenhar\s+",
        )

        for padrao in padroes_remover:
            novo_prompt = re.sub(
                padrao,
                "",
                prompt_imagem,
                count=1,
                flags=re.IGNORECASE,
            )
            if novo_prompt != prompt_imagem:
                prompt_imagem = novo_prompt.strip()
                break

        if not prompt_imagem:
            st.session_state.mensagens.append({
                "role": "assistant",
                "content": "🖼️ Diga o que você quer na imagem.",
            })
            st.rerun()

        with st.chat_message("assistant"):
            st.write("🖼️ Entendi! Vou criar sua imagem agora...")
            sucesso_imagem = mostrar_imagem(prompt_imagem)

        caminho_imagem = st.session_state.get("ultima_imagem_caminho")

        if sucesso_imagem:
            st.session_state.mensagens.append({
                "role": "assistant",
                "content": "🖼️ Imagem criada.",
                "tipo": "imagem",
                "arquivo": caminho_imagem,
            })
        else:
            st.session_state.mensagens.append({
                "role": "assistant",
                "content": "❌ Não consegui gerar a imagem. Veja a mensagem de erro acima.",
            })

        st.rerun()

    # --------------------------------------------------------
    # 🎬 COMANDO DE VÍDEO
    # --------------------------------------------------------
    if pergunta.lower().startswith("video:"):
        descricao_video = pergunta[len("video:"):].strip()

        if not descricao_video:
            st.session_state.mensagens.append({
                "role": "assistant",
                "content": "Digite a descrição depois de `video:`.",
            })
            st.rerun()

        camera_video, proporcao_video, duracao_video = mostrar_configuracao_video()

        with st.chat_message("assistant"):
            st.write("🎬 Preparando seu vídeo cinematográfico...")
            with st.spinner("🎬 Gerando seu vídeo..."):
                caminho_video, mensagem_video = gerar_video(
                    descricao=descricao_video,
                    camera=camera_video,
                    proporcao=proporcao_video,
                    duracao=duracao_video,
                )

            if caminho_video:
                st.success("🎬 Vídeo gerado com sucesso!")
                st.video(caminho_video)
                resposta_video = "🎬 Vídeo gerado com sucesso."
            else:
                resposta_video = f"❌ Não foi possível gerar o vídeo.\n\n{mensagem_video}"
                st.error(resposta_video)

        if caminho_video:
            st.session_state.mensagens.append({
                "role": "assistant",
                "content": resposta_video,
                "tipo": "video",
                "arquivo": caminho_video,
            })
        else:
            st.session_state.mensagens.append({
                "role": "assistant",
                "content": resposta_video,
            })

        st.rerun()

    # --------------------------------------------------------
    # 💻 COMANDO DE CÓDIGO
    # --------------------------------------------------------
    if pergunta.lower().startswith("codigo:"):
        pedido_codigo = pergunta[len("codigo:"):].strip()

        if not pedido_codigo:
            resposta_codigo = "Digite o que você quer programar depois de `codigo:`."
        else:
            linguagem_codigo = st.session_state.get(
                "tool_linguagem_codigo",
                listar_linguagens()[0],
            )

            prompt_codigo = preparar_pedido_codigo(
                pedido=pedido_codigo,
                linguagem=linguagem_codigo,
            )

            try:
                resposta = cliente.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt_codigo,
                )
                resposta_codigo = (
                    resposta.text
                    if resposta.text
                    else "Não consegui gerar o código."
                )
            except Exception as erro:
                resposta_codigo = f"❌ Erro ao gerar código: {erro}"

        st.session_state.mensagens.append({
            "role": "assistant",
            "content": resposta_codigo,
        })
        st.rerun()

    # --------------------------------------------------------
    # 👁️ ANÁLISE DA ÚLTIMA IMAGEM
    # --------------------------------------------------------
    comandos_imagem = (
        "essa imagem", "esta imagem", "essa foto", "esta foto",
        "essa cena", "esta cena", "sobre essa imagem", "sobre esta imagem",
        "baseado nessa imagem", "baseado nesta imagem", "na imagem",
        "nessa imagem", "nesta imagem",
    )

    pedido_sobre_imagem = any(
        comando in texto_pergunta
        for comando in comandos_imagem
    )

    if pedido_sobre_imagem:
        caminho_imagem = st.session_state.get("ultima_imagem_caminho")

        if not caminho_imagem:
            st.session_state.mensagens.append({
                "role": "assistant",
                "content": "🖼️ Ainda não tenho uma imagem disponível para analisar. Crie uma imagem primeiro.",
            })
            st.rerun()

        if not os.path.exists(caminho_imagem):
            st.session_state.mensagens.append({
                "role": "assistant",
                "content": "❌ Não consegui encontrar o arquivo da última imagem.",
            })
            st.rerun()

        try:
            with open(caminho_imagem, "rb") as arquivo:
                dados_imagem = arquivo.read()

            nome_arquivo = os.path.basename(caminho_imagem)
            extensao = nome_arquivo.lower().split(".")[-1]
            tipos_imagem = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "webp": "image/webp",
            }
            mime_type = tipos_imagem.get(extensao, "image/png")

            from google.genai import types

            imagem_gemini = types.Part.from_bytes(
                data=dados_imagem,
                mime_type=mime_type,
            )

            with st.chat_message("assistant"):
                with st.spinner("👁️ Alex IA está analisando a imagem..."):
                    resposta = cliente.models.generate_content(
                        model=GEMINI_MODEL,
                        contents=[imagem_gemini, pergunta],
                    )
                    texto_resposta = (
                        resposta.text
                        if resposta.text
                        else "Não consegui analisar a imagem."
                    )
                st.write(texto_resposta)

            st.session_state.mensagens.append({
                "role": "assistant",
                "content": texto_resposta,
            })

        except Exception as erro:
            mensagem_erro = f"❌ Não consegui analisar a imagem.\n\nDetalhes: {erro}"
            st.session_state.mensagens.append({
                "role": "assistant",
                "content": mensagem_erro,
            })
            st.error(mensagem_erro)

        st.stop()

    # --------------------------------------------------------
    # 📄 CONTEXTO DO ARQUIVO
    # --------------------------------------------------------
    contexto_arquivo = ""
    if st.session_state.arquivo_contexto:
        contexto_arquivo = f"""
Arquivo enviado pelo usuário:

Nome:
{st.session_state.arquivo_nome}

Conteúdo:

{st.session_state.arquivo_contexto}
"""

    # --------------------------------------------------------
    # 🎭 PERSONAGEM
    # --------------------------------------------------------
    contexto_personagem = ""
    personagem = st.session_state.personagem_atual

    if personagem:
        contexto_personagem = f"""
Personagem atualmente selecionado:

Nome:
{personagem["nome"]}

Idade:
{personagem["idade"]}

Aparência:
{personagem["aparencia"]}

Roupa:
{personagem["roupa"]}

Personalidade:
{personagem["personalidade"]}

Use o personagem somente quando isso fizer sentido para o pedido do usuário.
"""

    # --------------------------------------------------------
    # 🧠 MEMÓRIAS
    # --------------------------------------------------------
    memorias = carregar_memorias()
    contexto_memoria = ""

    if memorias:
        contexto_memoria = "Memórias importantes do usuário:\n\n" + "\n".join(
            f"- {memoria}" for memoria in memorias
        )

    # --------------------------------------------------------
    # 📜 HISTÓRICO
    # --------------------------------------------------------
    historico = ""
    for mensagem in st.session_state.mensagens:
        if mensagem.get("tipo") in ("imagem", "video"):
            continue

        if mensagem["role"] == "user":
            historico += f"Geovani: {mensagem['content']}\n"
        elif mensagem["role"] == "assistant":
            historico += f"{AI_NAME}: {mensagem['content']}\n"

    # --------------------------------------------------------
    # 🧠 INSTRUÇÃO FINAL
    # --------------------------------------------------------
    instrucao = f"""
{SYSTEM_PROMPT}

Regras adicionais:

- Responda sempre em português do Brasil.
- Você está conversando diretamente com Geovani.
- Mantenha continuidade com o histórico.
- Use as memórias quando forem relevantes.
- Use o personagem somente quando necessário.
- Se houver um arquivo enviado, analise seu conteúdo.
- Não invente informações sobre arquivos.
- Seja clara, inteligente e objetiva.
- Ajude Geovani a desenvolver a Alex IA Ultra.
- Quando não souber algo, diga claramente.

{contexto_memoria}

{contexto_personagem}

{contexto_arquivo}

Histórico da conversa:

{historico}

Pergunta atual:

{pergunta}
"""

    # --------------------------------------------------------
    # 🤖 GEMINI
    # --------------------------------------------------------
    try:
        with st.chat_message("assistant"):
            with st.spinner("🤖 Alex IA está pensando..."):
                resposta = cliente.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=instrucao,
                )

                texto_resposta = (
                    resposta.text
                    if resposta.text
                    else "Não consegui gerar uma resposta."
                )

            st.write(texto_resposta)

            if st.session_state.usar_voz:
                with st.spinner("🔊 Gerando voz..."):
                    mostrar_audio(texto_resposta)

        st.session_state.mensagens.append({
            "role": "assistant",
            "content": texto_resposta,
        })

    except Exception as erro:
        mensagem_erro = f"❌ Erro ao conversar com o Gemini:\n\n{erro}"
        st.session_state.mensagens.append({
            "role": "assistant",
            "content": mensagem_erro,
        })
        st.error(mensagem_erro)
