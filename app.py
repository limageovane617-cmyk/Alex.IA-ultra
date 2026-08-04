import streamlit as st
import google.generativeai as genai

st.set_page_config(
    page_title="🤖 Alex IA Ultra",
    page_icon="🤖"
)

st.title("🤖 Alex IA Ultra")
st.write("Sua IA pessoal usando a API do Google Gemini")

api_key = st.text_input(
    "Digite sua chave da API Gemini:",
    type="password"
)

if api_key:
    try:
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel("gemini-1.5-flash")

        pergunta = st.text_input("Pergunte alguma coisa:")

        if st.button("Enviar") and pergunta:
            resposta = model.generate_content(pergunta)
            st.success(resposta.text)

    except Exception as e:
        st.error(f"Erro: {e}")
