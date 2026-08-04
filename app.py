import streamlit as st
from google import genai

st.set_page_config(
    page_title="🤖 Alex IA Ultra",
    page_icon="🤖",
)

st.title("🤖 Alex IA Ultra")
st.write("Sua IA pessoal usando o Google Gemini")

api_key = st.text_input(
    "Digite sua chave da API Gemini:",
    type="password"
)

if api_key:
    try:
        client = genai.Client(api_key=api_key)

        pergunta = st.text_input("Pergunte alguma coisa:")

        if st.button("Enviar") and pergunta:
            resposta = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=pergunta
            )

            st.success(resposta.text)

    except Exception as e:
        st.error(f"Erro: {e}")
