# ============================================================
# 🚀 APP.PY — ALEX IA ULTRA (INTERFACE STREAMLIT)
# ============================================================

import os
import streamlit as st
from google import genai
import core.brain as brain
import video

# ------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA
# ------------------------------------------------------------
st.set_page_config(
    page_title="Alex IA Ultra",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ------------------------------------------------------------
# 2. INICIALIZAÇÃO DO ESTADO (SESSION STATE)
# ------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "cliente_gemini" not in st.session_state:
    api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if api_key:
        st.session_state.cliente_gemini = genai.Client(api_key=api_key)
    else:
        st.session_state.cliente_gemini = None

# ------------------------------------------------------------
# 3. SIDEBAR / CONFIGURAÇÕES
# ------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configurações da Alex")
    camera, proporcao, duracao = video.mostrar_configuracao_video()
    config_video = {
        "camera": camera,
        "proporcao": proporcao,
        "duracao": duracao
    }

# ------------------------------------------------------------
# 4. CABEÇALHO DO APLICATIVO
# ------------------------------------------------------------
st.title("🤖 Alex IA Ultra")
st.caption("Criada por Geovane • Inteligência Artificial Pessoal")

if not st.session_state.cliente_gemini:
    st.error("⚠️ Chave `GEMINI_API_KEY` não foi configurada nas Secrets do Streamlit.")
    st.stop()

# ------------------------------------------------------------
# 5. EXIBIÇÃO DO HISTÓRICO DE MENSAGENS E MÍDIAS
# ------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg.get("content", ""))

        # 🔊 Renderizar Áudio
        if msg.get("audio") and os.path.exists(msg["audio"]):
            st.audio(msg["audio"])

        # 🖼️ Renderizar Imagem
        if msg.get("tipo") == "imagem" and msg.get("arquivo"):
            if os.path.exists(msg["arquivo"]):
                st.image(msg["arquivo"])

        # 🎬 Renderizar Vídeo Único
        elif msg.get("tipo") == "video" and msg.get("arquivo"):
            if os.path.exists(msg["arquivo"]):
                st.video(msg["arquivo"])

        # 🎬🎬 Renderizar Múltiplos Vídeos (Mini Série / Lote)
        elif msg.get("tipo") == "multiplos_videos" and msg.get("lista_videos"):
            for item in msg["lista_videos"]:
                if item.get("sucesso") and item.get("arquivo") and os.path.exists(item["arquivo"]):
                    st.caption(f"🎬 **{item.get('prompt', 'Cena')}**")
                    st.video(item["arquivo"])

# ------------------------------------------------------------
# 6. ENTRADA DE MENSAGENS E PROCESSAMENTO
# ------------------------------------------------------------
prompt_usuario = st.chat_input("Digite sua mensagem para Alex...")

if prompt_usuario:
    # Registra mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": prompt_usuario})
    with st.chat_message("user"):
        st.write(prompt_usuario)

    # Processa resposta com a Alex IA
    with st.chat_message("assistant"):
        with st.spinner("Alex está processando..."):
            prompt_sistema = "Você é a Alex IA Ultra, uma assistente pessoal inteligente, prestativa e autônoma."
            
            resposta_dict = brain.processar_resposta_alex(
                cliente=st.session_state.cliente_gemini,
                modelo_id="gemini-2.5-flash",
                prompt_sistema=prompt_sistema,
                historico=st.session_state.messages,
                mensagem_usuario=prompt_usuario,
                config_video=config_video
            )

            texto_resposta = resposta_dict.get("texto", "")
            tipo_resposta = resposta_dict.get("tipo", "texto")
            arquivo_midia = resposta_dict.get("arquivo")
            lista_videos = resposta_dict.get("lista_videos", [])

            st.write(texto_resposta)

            # Renderização imediata na tela
            if tipo_resposta == "imagem" and arquivo_midia and os.path.exists(arquivo_midia):
                st.image(arquivo_midia)

            elif tipo_resposta == "video" and arquivo_midia and os.path.exists(arquivo_midia):
                st.video(arquivo_midia)

            elif tipo_resposta == "multiplos_videos" and lista_videos:
                for item in lista_videos:
                    if item.get("sucesso") and item.get("arquivo") and os.path.exists(item["arquivo"]):
                        st.caption(f"🎬 **{item.get('prompt', 'Cena')}**")
                        st.video(item["arquivo"])

            # Adiciona resposta no histórico da sessão
            st.session_state.messages.append({
                "role": "assistant",
                "content": texto_resposta,
                "tipo": tipo_resposta,
                "arquivo": arquivo_midia,
                "lista_videos": lista_videos
            })

            st.rerun()
            
