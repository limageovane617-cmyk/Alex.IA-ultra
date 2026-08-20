# ============================================================
# 🤖 ALEX IA ULTRA — CHAT INTELIGENTE (COM FUNCTION CALLING & LOTE)
# Criado por: Geovani
# ============================================================

import base64
import importlib
import sys
from pathlib import Path
from PIL import Image

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
# 📦 IMPORTAÇÕES SEGURAS DOS MÓDULOS DE MÍDIA
# ============================================================

try:
    if "gerenciador_imagem" in sys.modules:
        importlib.reload(sys.modules["gerenciador_imagem"])
    import gerenciador_imagem
except Exception:
    gerenciador_imagem = None

try:
    if "video" in sys.modules:
        importlib.reload(sys.modules["video"])
    import video
except Exception:
    video = None

from config_ultra import AI_NAME, CREATOR_NAME, GEMINI_MODEL, SYSTEM_PROMPT
from core.brain import processar_resposta_alex
from servicos import criar_cliente_gemini, verificar_servicos
from voz import mostrar_audio

# ============================================================
# 🛠️ VALIDAÇÃO REAL DE MÍDIA (TESTA CABEÇALHO DO ARQUIVO)
# ============================================================

def midia_valida(caminho, tipo="video"):
    """Verifica se o arquivo existe, tem tamanho >0 e cabeçalho de mídia válido."""
    if not caminho:
        return False
    
    str_caminho = str(caminho)
    if str_caminho.startswith("http://") or str_caminho.startswith("https://"):
        return True
        
    p = Path(str_caminho)
    if not (p.exists() and p.is_file() and p.stat().st_size > 100):
        return False

    try:
        dados = p.read_bytes()[:32]
        
        if tipo == "imagem":
            with Image.open(p) as img:
                img.verify()
            return True
            
        elif tipo == "video":
            # Verifica cabeçalhos comuns de MP4/WebM/AVI
            headers_validos = [b"ftyp", b"\x1a\x45\xdf\xa3", b"RIFF"]
            return any(h in dados for h in headers_validos)
            
    except Exception:
        return False

    return True

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
            if tipo == "imagem" and midia_valida(mensagem.get("arquivo"), "imagem"):
                st.image(mensagem["arquivo"], use_container_width=True)

            elif tipo == "video" and midia_valida(mensagem.get("arquivo"), "video"):
                st.video(mensagem["arquivo"])

            elif tipo == "multiplos_videos" and mensagem.get("lista_videos"):
                for item in mensagem["lista_videos"]:
                    if midia_valida(item.get("arquivo"), "video"):
                        st.caption(f"🎬 {item.get('prompt', '')}")
                        st.video(item["arquivo"])

            if texto:
                st.write(texto)

            if texto:
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
# 💬 ENTRADA DO CHAT COM AUTONOMIA NATIVA
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
        with st.spinner("🤖 Alex IA está processando..."):
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

            msg_low = pergunta_limpa.lower()

            # 🎬 PROCESSAMENTO DE VÍDEO
            if any(w in msg_low for w in ["video", "vídeo"]) and not midia_valida(resultado.get("arquivo"), "video"):
                if video and hasattr(video, "gerar_video"):
                    try:
                        res_v = video.gerar_video(
                            prompt=pergunta_limpa,
                            duracao=st.session_state.video_duracao,
                            proporcao=st.session_state.video_proporcao,
                        )
                        caminho_v = res_v.get("arquivo") if isinstance(res_v, dict) else res_v
                        
                        if midia_valida(caminho_v, "video"):
                            resultado["tipo"] = "video"
                            resultado["arquivo"] = caminho_v
                            resultado["texto"] = "Aqui está o seu vídeo!"
                        else:
                            st.error("⚠️ A API de vídeo não retornou um MP4 válido. Verifique suas chaves/créditos de API do serviço de vídeo.")
                            resultado["texto"] = "Não foi possível gerar o vídeo no momento."
                            resultado["tipo"] = "texto"
                    except Exception as e:
                        st.error(f"❌ Erro ao chamar gerador de vídeo: {e}")
                        resultado["texto"] = "Ocorreu um erro ao gerar o vídeo."
                        resultado["tipo"] = "texto"

            # 🖼️ PROCESSAMENTO DE IMAGEM
            elif any(w in msg_low for w in ["imagem", "foto", "desenho", "criar imagem", "cria uma imagem"]) and not midia_valida(resultado.get("arquivo"), "imagem"):
                if gerenciador_imagem:
                    func_img = getattr(gerenciador_imagem, "gerar_imagem", None) or getattr(gerenciador_imagem, "criar_imagem", None)
                    if func_img:
                        try:
                            res_i = func_img(pergunta_limpa)
                            caminho_i = res_i.get("arquivo") if isinstance(res_i, dict) else res_i
                            
                            if midia_valida(caminho_i, "imagem"):
                                resultado["tipo"] = "imagem"
                                resultado["arquivo"] = caminho_i
                                resultado["texto"] = "Aqui está a sua imagem!"
                            else:
                                st.error("⚠️ A API de imagem falhou ao gerar a figura. Verifique os logs de erro ou limites da API.")
                                resultado["texto"] = "Não foi possível gerar a imagem no momento."
                                resultado["tipo"] = "texto"
                        except Exception as e:
                            st.error(f"❌ Erro ao chamar gerador de imagem: {e}")
                            resultado["texto"] = "Ocorreu um erro ao gerar a imagem."
                            resultado["tipo"] = "texto"

            # Renderiza Mídia se for VÁLIDA
            if resultado.get("tipo") == "imagem" and midia_valida(resultado.get("arquivo"), "imagem"):
                st.image(resultado["arquivo"], use_container_width=True)

            elif resultado.get("tipo") == "video" and midia_valida(resultado.get("arquivo"), "video"):
                st.video(resultado["arquivo"])

            elif resultado.get("tipo") == "multiplos_videos" and resultado.get("lista_videos"):
                for item in resultado["lista_videos"]:
                    if midia_valida(item.get("arquivo"), "video"):
                        st.caption(f"🎬 {item.get('prompt', '')}")
                        st.video(item["arquivo"])

            # Renderiza Texto
            if resultado.get("texto"):
                st.write(resultado["texto"])

            # Voz
            if resultado.get("texto"):
                try:
                    mostrar_audio(resultado["texto"])
                except Exception:
                    pass

            st.session_state.mensagens.append({
                "role": "assistant",
                "content": resultado.get("texto", ""),
                "tipo": resultado.get("tipo", "texto"),
                "arquivo": resultado.get("arquivo") if midia_valida(resultado.get("arquivo"), resultado.get("tipo")) else None,
                "lista_videos": resultado.get("lista_videos"),
            })

    st.rerun()
                            
