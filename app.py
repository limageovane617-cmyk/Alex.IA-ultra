import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="🤖 Alex IA Ultra",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Alex IA Ultra")
st.write("Sua inteligência artificial avançada")

api_key = st.text_input(
    "Digite sua chave do OpenRouter:",
    type="password"
)

if api_key:

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        if "mensagens" not in st.session_state:
            st.session_state.mensagens = [
                {
                    "role": "system",
                    "content": "Você é a Alex IA Ultra, uma inteligência artificial avançada criada por Geovani. Responda sempre em português de forma inteligente e útil."
                }
            ]

        if st.sidebar.button("🗑️ Limpar conversa"):
            st.session_state.mensagens = [
                {
                    "role": "system",
                    "content": "Você é a Alex IA Ultra, uma inteligência artificial avançada criada por Geovani."
                }
            ]
            st.rerun()

        for mensagem in st.session_state.mensagens:
            if mensagem["role"] != "system":
                with st.chat_message(mensagem["role"]):
                    st.write(mensagem["content"])

        pergunta = st.chat_input("Converse com a Alex IA Ultra...")

        if pergunta:

            st.session_state.mensagens.append(
                {
                    "role": "user",
                    "content": pergunta
                }
            )

            with st.chat_message("user"):
                st.write(pergunta)

            resposta = client.chat.completions.create(
                model="openrouter/free",
                messages=st.session_state.mensagens
            )

            texto = resposta.choices[0].message.content

            st.session_state.mensagens.append(
                {
                    "role": "assistant",
                    "content": texto
                }
            )

            with st.chat_message("assistant"):
                st.write(texto)

    except Exception as e:
        st.error(f"Erro: {e}")
