import streamlit as st
from openai import OpenAI

from config import (
    OPENROUTER_URL,
    DEFAULT_MODEL,
    SYSTEM_PROMPT,
)

st.set_page_config(
    page_title="🤖 Alex IA Ultra V4",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Alex IA Ultra V4")
st.caption("Criada por Geovani")

# ============================
# SIDEBAR
# ============================

st.sidebar.title("⚙️ Configurações")

api_key = st.sidebar.text_input(
    "Chave da OpenRouter",
    type="password"
)

modelo = st.sidebar.text_input(
    "Modelo",
    value=DEFAULT_MODEL
)

temperatura = st.sidebar.slider(
    "Criatividade",
    0.0,
    2.0,
    0.7,
    0.1
)

max_tokens = st.sidebar.slider(
    "Máximo de Tokens",
    100,
    4000,
    1200,
    100
)

st.sidebar.divider()

st.sidebar.subheader("📂 Recursos")

st.sidebar.info(
    "Os módulos serão ativados automaticamente."
)

# ============================
# MEMÓRIA
# ============================

if "messages" not in st.session_state:

    st.session_state.messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

if "arquivo_texto" not in st.session_state:
    st.session_state.arquivo_texto = ""

# ============================
# LIMPAR
# ============================

if st.sidebar.button("🗑 Limpar conversa"):

    st.session_state.messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    st.session_state.arquivo_texto = ""

    st.rerun()

# ============================
# MOSTRAR CHAT
# ============================

for mensagem in st.session_state.messages:

    if mensagem["role"] != "system":

        with st.chat_message(mensagem["role"]):

            st.markdown(mensagem["content"])

# ============================
# CONEXÃO OPENROUTER
# ============================

cliente = None

if api_key:

    cliente = OpenAI(
        api_key=api_key,
        base_url=OPENROUTER_URL
    )

# ============================
# CHAT
# ============================

pergunta = st.chat_input(
    "Pergunte qualquer coisa..."
)

if pergunta:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": pergunta
        }
    )

    with st.chat_message("user"):
        st.markdown(pergunta)

    if cliente:

        try:

            resposta = cliente.chat.completions.create(
                model=modelo,
                messages=st.session_state.messages,
                temperature=temperatura,
                max_tokens=max_tokens,
            )

            texto = resposta.choices[0].message.content

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": texto
                }
            )

            with st.chat_message("assistant"):
                st.markdown(texto)

        except Exception as erro:

            st.error(f"Erro: {erro}")

    else:

        st.warning("Digite sua chave da OpenRouter.")
