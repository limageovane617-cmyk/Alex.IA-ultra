# ============================================================
# 🤖 ALEX IA ULTRA — CHAT INTELIGENTE + CONTROLES FIXOS NO RODAPÉ
# Criado por: Geovani
# ============================================================

import base64
import importlib
import os
import re
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
from gerenciador_imagem import mostrar_imagem
from servicos import criar_cliente_gemini, verificar_servicos
from voz import mostrar_audio
import video

gerar_video = video.gerar_video

# ============================================================
# 🧠 SESSION STATE
# ============================================================

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

if "ferramenta_ativa" not in st.session_state:
    st.session_state.ferramenta_ativa = None

# Configurações padrão de vídeo
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
# 🖼️ FUNDO & CSS FIXO
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
        padding-bottom: 140px !important; /* Dá espaço para os botões fixos não cobrirem o chat */
    }}

    /* Ocultar avatares */
    [data-testid="stChatMessageAvatar"],
    [data-testid="stChatMessageAvatarCustom"],
    .stChatMessageAvatar,
    div[data-testid="stChatMessage"] > div:first-child {{
        display: none !important;
    }}

    /* Estilização dos balões da Alex */
    div[data-testid="stChatMessage"] {{
        padding: 14px 18px !important;
        background: rgba(12, 22, 36, 0.75) !important;
        border: 1px solid rgba(130, 210, 255, 0.18) !important;
        border-radius: 18px 18px 18px 4px !important;
        margin-bottom: 14px !important;
        gap: 0px !important;
    }}

    /* FIXA A BARRA DE BOTÕES NO RODAPÉ (EXATAMENTE ACIMA DO CHAT INPUT) */
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPopover"]) {{
        position: fixed !important;
        bottom: 75px !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 90% !important;
        max-width: 980px !important;
        z-index: 9999 !important;
        background: rgba(12, 22, 36, 0.90) !important;
        padding: 8px 12px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(130, 210, 255, 0.25) !important;
        backdrop-filter: blur(10px) !important;
    }}

    /* Estilo interno dos botões Popover */
    div[data-testid="stPopover"] > button {{
        background: rgba(0, 132, 255, 0.2) !important;
        border: 1px solid rgba(130, 210, 255, 0.4) !important;
        color: #00d2ff !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        width: 100% !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# 🤖 CABEÇALHO LIMPO
# ============================================================

st.markdown(f"## 🤖 {AI_NAME}")
st.caption(f"Criada por {CREATOR_NAME} • inteligência artificial pessoal")
st.divider()

# ============================================================
# 💬 HISTÓRICO DE MENSAGENS (ÁREA CENTRAL)
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
                and os.path.exists(mensagem["arquivo"])
            ):
                st.image(mensagem["arquivo"], use_container_width=True)

            elif (
                tipo == "video"
                and mensagem.get("arquivo")
                and os.path.exists(mensagem["arquivo"])
            ):
                st.video(mensagem["arquivo"])

            if texto:
                st.write(texto)

            # Áudio automático no final da resposta da Alex
            if tipo == "texto" and texto:
                mostrar_audio(texto)

# ============================================================
# 🛠️ PAINEL DE FERRAMENTAS ATIVAS (EXPANDER)
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
# 🧰 BARRA DE FERRAMENTAS FIXA NO RODAPÉ
# ============================================================

col_menu, col_video_cfg = st.columns([1, 1.2])

with col_menu:
    with st.popover("➕ Ferramentas"):
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
    with st.popover("🎬 Ajustes de Vídeo"):
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
# 💬 ENTRADA DO CHAT (RODAPÉ)
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

    low = pergunta_limpa.lower()

    gatilhos_imagem = [
        "cria uma imagem", "gera uma imagem", "gerar imagem",
        "crie uma imagem", "faz uma imagem", "desenha ", "desenhe ",
        "imagem de ", "foto de ", "gera imagem"
    ]

    gatilhos_video = [
        "cria um vídeo", "gera um vídeo", "gerar vídeo",
        "crie um vídeo", "faz um vídeo", "vídeo de ", "gera vídeo", "faça um vídeo"
    ]

    quer_imagem = any(g in low for g in gatilhos_imagem)
    quer_video = any(g in low for g in gatilhos_video)

    # 1. DETECÇÃO DE VÍDEO
    if quer_video:
        with st.chat_message("assistant"):
            with st.spinner("🎬 Alex IA está gerando seu vídeo..."):
                prompt_video = re.sub(
                    r"(cria|gera|gerar|crie|faz|faça)\s+(um\s+)?vídeo(\s+de)?",
                    "",
                    pergunta_limpa,
                    flags=re.IGNORECASE,
                ).strip() or pergunta_limpa

                resultado = gerar_video(
                    descricao=prompt_video,
                    camera="Sony FX6",
                    proporcao=st.session_state.video_proporcao,
                    duracao=st.session_state.video_duracao,
                    width=512,
                    height=512,
                )

                if isinstance(resultado, dict) and resultado.get("sucesso") and resultado.get("video"):
                    caminho = resultado["video"]
                    st.write(f"🎬 Aqui está o vídeo ({st.session_state.video_duracao}s) sobre: **{prompt_video}**")
                    st.video(caminho)

                    st.session_state.mensagens.append({
                        "role": "assistant",
                        "content": f"🎬 Vídeo gerado: {prompt_video}",
                        "tipo": "video",
                        "arquivo": caminho,
                    })
                else:
                    st.error("❌ Não foi possível gerar o vídeo neste momento.")

        st.rerun()

    # 2. DETECÇÃO DE IMAGEM
    elif quer_imagem:
        with st.chat_message("assistant"):
            prompt_imagem = re.sub(
                r"(cria|gera|gerar|crie|faz|desenha|desenhe)\s+(uma\s+)?(imagem|foto)?(\s+de)?",
                "",
                pergunta_limpa,
                flags=re.IGNORECASE,
            ).strip() or pergunta_limpa

            sucesso = mostrar_imagem(prompt_imagem)

            if sucesso:
                caminho_img = st.session_state.get("ultima_imagem_caminho")
                st.session_state.mensagens.append({
                    "role": "assistant",
                    "content": f"🖼️ Imagem gerada: {prompt_imagem}",
                    "tipo": "imagem",
                    "arquivo": caminho_img,
                })

        st.rerun()

    # 3. CONVERSA GEMINI + ÁUDIO AUTOMÁTICO
    else:
        contexto = "\n".join(
            f"{m['role']}: {m['content']}"
            for m in st.session_state.mensagens[-20:]
            if m.get("tipo") not in ("imagem", "video")
        )

        instrucao = (
            f"{SYSTEM_PROMPT}\n\n"
            "Responda sempre em português do Brasil.\n\n"
            f"Histórico:\n{contexto}\n\n"
            f"Pergunta:\n{pergunta_limpa}"
        )

        try:
            with st.chat_message("assistant"):
                with st.spinner("🤖 Alex IA está pensando..."):
                    resposta = cliente.models.generate_content(
                        model=GEMINI_MODEL, contents=instrucao
                    )

                    texto = (
                        resposta.text
                        if resposta.text
                        else "Não consegui gerar uma resposta."
                    )

                st.write(texto)
                mostrar_audio(texto)

            st.session_state.mensagens.append({
                "role": "assistant",
                "content": texto,
                "tipo": "texto",
            })

            st.rerun()

        except Exception as erro:
            st.error(f"❌ Erro ao conversar com a Alex: {erro}")
                    
