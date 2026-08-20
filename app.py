# ============================================================
# 🤖 ALEX IA ULTRA — CHAT INTELIGENTE (COM FUNCTION CALLING)
# Criado por: Geovani
# ============================================================

import base64
import importlib
import sys
from pathlib import Path

import streamlit as st

# ============================================================
# ⚙️ CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Alex IA Ultra",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# 📦 IMPORTAÇÕES DO PROJETO
# ============================================================

if "gerenciador_imagem" in sys.modules:
    importlib.reload(sys.modules["gerenciador_imagem"])
else:
    import gerenciador_imagem

from config_ultra import AI_NAME, CREATOR_NAME, GEMINI_MODEL, SYSTEM_PROMPT
from core.brain import processar_resposta_alex
from servicos import criar_cliente_gemini, verificar_servicos
from voz import mostrar_audio

# ============================================================
# 🧠 SESSION STATE
# ============================================================

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

if "ferramenta_ativa" not in st.session_state:
    st.session_state.ferramenta_ativa = None

if "video_duracao" not in st.session_state:
    st.session_state.video_duracao = 5

if "video_proporcao" not in st.session_state:
    st.session_state.video_proporcao = "16:9"

# ============================================================
# 🔐 SERVIÇOS
# ============================================================

servicos = verificar_servicos()

if not servicos.get("gemini"):
    st.error("🔐 A chave GEMINI_API_KEY não está configurada nos Secrets.")
    st.stop()

cliente = criar_cliente_gemini()

if cliente is None:
    st.error("❌ Não foi possível criar a conexão com o Gemini.")
    st.stop()


# ============================================================
# 🖼️ FUNDO & CSS
# ============================================================

def imagem_fundo_css():
    caminho = Path(__file__).with_name("fundo_chat.jpg")
    if not caminho.exists():
        return ""
    try:
        dados = base64.b64encode(caminho.read_bytes()).decode("utf-8")
        return f"background-image:url(data:image/jpeg;base64,{dados});"
    except Exception:
        return ""


st.markdown(
    f"""
    <style>
    .stApp {{
        {imagem_fundo_css()}
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    .stApp::before {{
        content: "";
        position: fixed;
        inset: 0;
        background: rgba(2,8,16,.68);
        z-index: -1;
        pointer-events: none;
    }}

    .main .block-container {{
        max-width: 980px;
        padding-top: 1.5rem;
        padding-bottom: 160px !important;
    }}

    [data-testid="stChatMessageAvatar"],
    [data-testid="stChatMessageAvatarCustom"],
    .stChatMessageAvatar,
    div[data-testid="stChatMessage"] > div:first-child {{
        display: none !important;
    }}

    div[data-testid="stChatMessage"] {{
        padding: 14px 18px !important;
        background: rgba(12, 22, 36, 0.75) !important;
        border: 1px solid rgba(130, 210, 255, 0.18) !important;
        border-radius: 18px 18px 18px 4px !important;
        margin-bottom: 14px !important;
        gap: 0px !important;
    }}

    div[data-testid="stBottom"] {{
        padding-bottom: 50px !important;
    }}

    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPopover"]) {{
        position: fixed !important;
        bottom: 10px !important;
        left: 16px !important;
        z-index: 99999 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        display: flex !important;
        flex-direction: row !important;
        gap: 10px !important;
        width: auto !important;
    }}

    div[data-testid="stPopover"] > button {{
        background: rgba(12, 22, 36, 0.90) !important;
        border: 1px solid rgba(0, 210, 255, 0.4) !important;
        color: #00d2ff !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        height: 38px !important;
        min-width: 50px !important;
        padding: 0 10px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        backdrop-filter: blur(8px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35) !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# 🤖 CABEÇALHO
# ============================================================

st.markdown(f"## 🤖 {AI_NAME}")
st.caption(f"Criada por {CREATOR_NAME} • inteligência artificial pessoal")
st.divider()

# ============================================================
# 💬 HISTÓRICO DE MENSAGENS
# ============================================================

for mensagem in st.session_state.mensagens:
    role = mensagem.get("role", "assistant")
    texto = mensagem.get("content", "")
    tipo = mensagem.get("tipo", "texto")

    if role == "user":
        st.markdown(
            f"""
            <div style="display: flex; justify-content: flex-end; margin-bottom: 14px;">
                <div style="
                    background: rgba(0, 132, 255, 0.32);
                    border: 1px solid rgba(0, 180, 255, 0.45);
                    color: #ffffff;
                    padding: 10px 16px;
                    border-radius: 18px 18px 2px 18px;
                    max-width: 82%;
                    font-size: 1rem;
                    line-height: 1.5;
                    word-wrap: break-word;">
                    {texto}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        with st.chat_message("assistant"):
            if (
                tipo == "imagem"
                and mensagem.get("arquivo")
                and Path(mensagem["arquivo"]).exists()
            ):
                st.image(mensagem["arquivo"], use_container_width=True)

            elif (
                tipo == "video"
                and mensagem.get("arquivo")
                and Path(mensagem["arquivo"]).exists()
            ):
                st.video(mensagem["arquivo"])

            if texto:
                st.write(texto)

            if tipo == "texto" and texto:
                try:
                    mostrar_audio(texto)
                except Exception:
                    pass

# ============================================================
# 🛠️ PAINEL DE FERRAMENTAS ATIVAS
# ============================================================

if st.session_state.ferramenta_ativa:
    ferramenta = st.session_state.ferramenta_ativa

    with st.expander(f"🛠️ Módulo Ativo: {ferramenta.capitalize()}", expanded=True):
        if ferramenta == "codigo":
            st.info("💻 Envie seu código ou dúvida de programação direto no chat.")

        elif ferramenta == "arquivo":
            st.file_uploader("Envie um arquivo para a Alex analisar:")

        elif ferramenta == "personagem":
            st.info("🎭 A personalidade da Alex está configurada em tom natural.")

        elif ferramenta == "memoria":
            st.info("🧠 Memória do sistema sincronizada.")

        if st.button("Fechar Módulo"):
            st.session_state.ferramenta_ativa = None
            st.rerun()

# ============================================================
# 🧰 BOTÕES NA PARTE INFERIOR
# ============================================================

col_menu, col_video_cfg = st.columns([1, 1])

with col_menu:
    with st.popover("➕"):
        st.subheader("🧰 Ferramentas da Ultra")

        if st.button("💻 Código", use_container_width=True):
            st.session_state.ferramenta_ativa = "codigo"

        if st.button("📎 Arquivo", use_container_width=True):
            st.session_state.ferramenta_ativa = "arquivo"

        if st.button("🎭 Personagem", use_container_width=True):
            st.session_state.ferramenta_ativa = "personagem"

        if st.button("🧠 Memória", use_container_width=True):
            st.session_state.ferramenta_ativa = "memoria"

        st.divider()

        if st.button("🗑️ Limpar chat", use_container_width=True):
            st.session_state.mensagens = []
            st.session_state.ferramenta_ativa = None
            st.rerun()

with col_video_cfg:
    with st.popover("🎬"):
        st.subheader("⚙️ Configurar Vídeo Automático")

        st.session_state.video_duracao = st.slider(
            "Duração (Segundos):",
            min_value=2,
            max_value=15,
            value=st.session_state.video_duracao,
            step=1,
        )

        st.session_state.video_proporcao = st.selectbox(
            "Proporção:",
            options=["16:9", "9:16", "1:1"],
            index=0,
        )

# ============================================================
# 💬 ENTRADA DO CHAT COM AUTONOMIA NATIVA (CORE/BRAIN)
# ============================================================

pergunta = st.chat_input("Digite sua mensagem para Alex...")

if pergunta:
    pergunta_limpa = pergunta.strip()
    if not pergunta_limpa:
        st.stop()

    st.session_state.mensagens.append({
        "role": "user",
        "content": pergunta_limpa,
    })

    with st.chat_message("assistant"):
        with st.spinner("🤖 Alex IA está pensando..."):
            config_vid = {
                "duracao": st.session_state.video_duracao,
                "proporcao": st.session_state.video_proporcao,
            }

            resultado = processar_resposta_alex(
                cliente=cliente,
                modelo_id=GEMINI_MODEL,
                prompt_sistema=SYSTEM_PROMPT,
                historico=st.session_state.mensagens,
                mensagem_usuario=pergunta_limpa,
                config_video=config_vid,
            )

            if resultado["tipo"] == "imagem" and resultado["arquivo"]:
                st.image(resultado["arquivo"], use_container_width=True)

            elif resultado["tipo"] == "video" and resultado["arquivo"]:
                st.video(resultado["arquivo"])

            st.write(resultado["texto"])

            if resultado["tipo"] == "texto":
                try:
                    mostrar_audio(resultado["texto"])
                except Exception:
                    pass

            st.session_state.mensagens.append({
                "role": "assistant",
                "content": resultado["texto"],
                "tipo": resultado["tipo"],
                "arquivo": resultado["arquivo"],
            })

    st.rerun()

