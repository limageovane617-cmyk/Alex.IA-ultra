import streamlit as st
from google import genai

st.title("Teste Gemini")

api_key = st.text_input("Chave Gemini", type="password")

if api_key:
    try:
        client = genai.Client(api_key=api_key)

        st.write("### Modelos disponíveis:")

        for model in client.models.list():
            st.write(model.name)

    except Exception as e:
        st.error(e)
