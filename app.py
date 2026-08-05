import streamlit as st
from google import genai

st.set_page_config(
    page_title="🤖 Alex IA Ultra V4",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Alex IA Ultra V4")
st.caption("Criada por Geovani")

api_key = st.sidebar.text_input(
    "🔑 Chave da API Gemini",
    type="password"
)

if api_key:

    try:

        cliente = genai.Client(api_key=api_key)

        pergunta = st.chat_input("Digite sua mensagem...")

        if pergunta:

            with st.chat_message("user"):
                st.write(pergunta)

            resposta = cliente.models.generate_content(
                model="gemini-2.5-flash",
                contents=pergunta
            )

            with st.chat_message("assistant"):
                st.write(resposta.text)

    except Exception as e:
        st.error(f"Erro: {e}")

else:
    st.info("Digite sua chave da API Gemini na barra lateral.")
