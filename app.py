import streamlit as st
from openai import OpenAI
from config import OPENROUTER_URL, DEFAULT_MODEL, SYSTEM_PROMPT

st.set_page_config(
    page_title="🤖 Alex IA Ultra V4",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Alex IA Ultra V4")
st.caption("Criada por Geovani")

# Barra lateral
st.sidebar.title("Configurações")

api_key = st.sidebar.text_input(
    "Chave da OpenRouter",
    type="password"
)

modelo = st.sidebar.text_input(
    "Modelo",
    value=DEFAULT_MODEL
)

# Memória da conversa
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

# Mostrar conversa
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Entrada do usuário
pergunta = st.chat_input("Digite sua mensagem...")

if pergunta:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": pergunta
        }
    )

    with st.chat_message("user"):
        st.markdown(pergunta)

    if api_key:

        try:

            cliente = OpenAI(
                api_key=api_key,
                base_url=OPENROUTER_URL
            )

            resposta = cliente.chat.completions.create(
                model=modelo,
                messages=st.session_state.messages
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
