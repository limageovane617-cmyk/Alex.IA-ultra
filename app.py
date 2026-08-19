import streamlit as st
from pathlib import Path
import time

# Se o seu arquivo de vídeo estiver na mesma pasta, importamos a função:
# from video import gerenciar_geracao_video

st.set_page_config(page_title="Alex IA Ultra", page_icon="🤖", layout="centered")

# --- ESTADO DA SESSÃO ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "ferramenta_ativa" not in st.session_state:
    st.session_state.ferramenta_ativa = None

# --- CABEÇALHO ---
st.title("🤖 Alex IA Ultra")
st.caption("Criada por Geovani • inteligência artificial pessoal")

# --- HISTÓRICO DE MENSAGENS ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "video" in message:
            st.video(message["video"])
        if "image" in message:
            st.image(message["image"])

# --- PAINEL DA FERRAMENTA SELECIONADA (EXIBIDO ACIMA DO INPUT) ---
if st.session_state.ferramenta_ativa == "video":
    with st.expander("🎬 **Gerador de Vídeo AI**", expanded=True):
        upload_img = st.file_uploader("Imagem de referência (opcional):", type=["png", "jpg", "jpeg"], key="v_img")
        prompt_video = st.text_area("Descrição do vídeo (foco em ações visuais):", key="v_prompt")
        
        col_v1, col_v2 = st.columns([1, 1])
        with col_v1:
            if st.button("🚀 Gerar Vídeo", use_container_width=True):
                if prompt_video:
                    with st.spinner("Gerando vídeo..."):
                        img_bytes = upload_img.getvalue() if upload_img else None
                        
                        # Chamada da função de geração de vídeo
                        # resposta = gerenciar_geracao_video(prompt=prompt_video, imagem_bytes=img_bytes)
                        
                        # Simulação / Estrutura de retorno esperada:
                        resposta = {"sucesso": False, "erros": ["LTX-2.3: Aguardando fila de GPU."]} 
                        
                        if resposta.get("sucesso"):
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": f"🎥 **Vídeo gerado via {resposta['motor']}**",
                                "video": resposta["video"]
                            })
                            st.session_state.ferramenta_ativa = None
                            st.rerun()
                        else:
                            st.error("❌ Nenhum vídeo foi gerado.")
                            if "erros" in resposta and resposta["erros"]:
                                for erro in resposta["erros"]:
                                    st.warning(erro)
                            elif resposta.get("erro"):
                                st.warning(resposta["erro"])
                else:
                    st.warning("Digite uma descrição para gerar o vídeo.")
        
        with col_v2:
            if st.button("❌ Fechar", use_container_width=True, key="close_v"):
                st.session_state.ferramenta_ativa = None
                st.rerun()

elif st.session_state.ferramenta_ativa == "imagem":
    with st.expander("🖼️ **Gerador de Imagem**", expanded=True):
        st.text_input("Descreva a imagem que deseja criar:")
        if st.button("Fechar", key="close_img"):
            st.session_state.ferramenta_ativa = None
            st.rerun()

elif st.session_state.ferramenta_ativa == "arquivo":
    with st.expander("📎 **Anexar Arquivo**", expanded=True):
        st.file_uploader("Envie um documento ou arquivo:")
        if st.button("Fechar", key="close_arq"):
            st.session_state.ferramenta_ativa = None
            st.rerun()

elif st.session_state.ferramenta_ativa == "voz":
    with st.expander("🔊 **Modo Voz**", expanded=True):
        st.info("Envie um áudio ou digite o texto para síntese de voz.")
        if st.button("Fechar", key="close_voz"):
            st.session_state.ferramenta_ativa = None
            st.rerun()

elif st.session_state.ferramenta_ativa == "codigo":
    with st.expander("💻 **Assistente de Código**", expanded=True):
        st.info("Modo focado em geração e refatoração de código ativado.")
        if st.button("Fechar", key="close_cod"):
            st.session_state.ferramenta_ativa = None
            st.rerun()

elif st.session_state.ferramenta_ativa == "personagem":
    with st.expander("🎭 **Seleção de Personagem**", expanded=True):
        st.selectbox("Escolha a personalidade da Alex:", ["Padrão", "Assistente Técnico", "Criativo"])
        if st.button("Fechar", key="close_pers"):
            st.session_state.ferramenta_ativa = None
            st.rerun()

elif st.session_state.ferramenta_ativa == "memoria":
    with st.expander("🧠 **Memória do Sistema**", expanded=True):
        st.write("Histórico de contextos e dados salvos da conversa.")
        if st.button("Fechar", key="close_mem"):
            st.session_state.ferramenta_ativa = None
            st.rerun()

# --- BARRA INFERIOR DE CHAT E FERRAMENTAS ---
st.markdown("---")
col_plus, col_chat = st.columns([1, 6], vertical_alignment="bottom")

with col_plus:
    # Botão de '+' posicionado no canto esquerdo inferior
    with st.popover("➕"):
        st.markdown("### 🧰 Ferramentas da Ultra")
        
        if st.button("🖼️ Imagem", use_container_width=True):
            st.session_state.ferramenta_ativa = "imagem"
            st.rerun()

        if st.button("🎬 Vídeo", use_container_width=True):
            st.session_state.ferramenta_ativa = "video"
            st.rerun()

        if st.button("🔊 Voz", use_container_width=True):
            st.session_state.ferramenta_ativa = "voz"
            st.rerun()

        if st.button("💻 Código", use_container_width=True):
            st.session_state.ferramenta_ativa = "codigo"
            st.rerun()

        if st.button("📎 Arquivo", use_container_width=True):
            st.session_state.ferramenta_ativa = "arquivo"
            st.rerun()

        if st.button("🎭 Personagem", use_container_width=True):
            st.session_state.ferramenta_ativa = "personagem"
            st.rerun()

        if st.button("🧠 Memória", use_container_width=True):
            st.session_state.ferramenta_ativa = "memoria"
            st.rerun()

        st.divider()

        if st.button("🗑️ Limpar chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.ferramenta_ativa = None
            st.rerun()

with col_chat:
    prompt_usuario = st.chat_input("Digite sua mensagem para Alex...")

# --- PROCESSAMENTO DAS MENSAGENS DO CHAT ---
if prompt_usuario:
    st.session_state.messages.append({"role": "user", "content": prompt_usuario})
    
    # Resposta padrão da IA
    resposta_ia = f"Recebido! Em que mais posso ajudar com '{prompt_usuario}'?"
    st.session_state.messages.append({"role": "assistant", "content": resposta_ia})
    st.rerun()
        
