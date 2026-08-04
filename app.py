import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="🤖 Alex IA Ultra",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Alex IA Ultra")
st.write("Sua Inteligência Artificial usando OpenRouter")

api_key = st.text_input(
    "Digite sua chave do OpenRouter:",
    type="password"
)

if api_key:

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )

    pergunta = st.text_input("Pergunte qualquer coisa para a Alex IA Ultra:")

    if st.button("Enviar"):

        if pergunta.strip() == "":
            st.warning("Digite uma pergunta.")
        else:
            try:

                resposta = client.chat.completions.create(
                    model="deepseek/deepseek-chat-v3-0324:free",
                    messages=[
                        {
                            "role": "system",
                            "content": "Você é a Alex IA Ultra, uma inteligência artificial avançada criada por Geovani. Responda sempre em português de forma inteligente, útil e educada."
                        },
                        {
                            "role": "user",
                            "content": pergunta
                        }
                    ],
                    temperature=0.7,
                    max_tokens=1500
                )

                st.success(resposta.choices[0].message.content)

            except Exception as e:
                st.error(f"Erro: {e}")
