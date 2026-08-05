import streamlit as st
from google import genai

# Configuração da página
st.set_page_config(
    page_title="Alex IA",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Alex IA")
st.caption("Sua inteligência artificial pessoal")

# Campo da chave API
api_key = st.text_input(
    "Digite sua chave da API Gemini:",
    type="password"
)

if api_key:

    try:
        # Conecta ao Gemini
        cliente = genai.Client(api_key=api_key)

        st.success("✅ Gemini conectado com sucesso!")

        # Campo da pergunta
        pergunta = st.text_input(
            "Digite sua pergunta:"
        )

        if st.button("Enviar") and pergunta:

            resposta = cliente.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=pergunta
            )

            st.subheader("🤖 Alex IA respondeu:")
            st.write(resposta.text)

    except Exception as e:
        st.error(f"Erro: {e}")
