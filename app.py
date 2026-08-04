import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="🤖 Alex IA Ultra",
    page_icon="🤖"
)

st.title("🤖 Alex IA Ultra")
st.write("Sua IA usando OpenRouter")

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

        pergunta = st.text_input("Pergunte alguma coisa:")

        if st.button("Enviar") and pergunta:
            resposta = client.chat.completions.create(
                model="meta-llama/llama-3.3-70b-instruct:free",
                messages=[
                    {"role": "user", "content": pergunta}
                ]
            )

            st.success(resposta.choices[0].message.content)

    except Exception as e:
        st.error(f"Erro: {e}")
