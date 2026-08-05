import streamlit as st
from google import genai

# Configuração da página
st.set_page_config(
    page_title="Alex IA",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Alex IA")
st.caption("Olá Geovani! Eu sou sua inteligência artificial pessoal. Estou pronto para criar, escrever, programar e ajudar você no quer vc precisa.")

# Campo da chave API
api_key = st.text_input(
    "ola Geovani sua chave da API :",
    type="password"
)

if api_key:

    try:
        # Conecta ao Gemini
        cliente = genai.Client(api_key=api_key)

        st.success("✅ Gemini conectado com sucesso!")

        # Campo da pergunta
        pergunta = st.chat_input("Digite sua mensagem...")
        )

        if pergunta:

            resposta = cliente.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=f"""
Você é o Alex IA, uma inteligência artificial avançada.
Seu objetivo é ajudar o usuário criando textos, roteiros,
ideias, códigos e explicações detalhadas.

Sempre responda em português do Brasil.
Se o usuário pedir um roteiro, crie:
- Título
- Gênero
- Sinopse
- Personagens
- Cenas com diálogos.

Pergunta do usuário:
{pergunta}
"""
            )

            st.subheader("🤖 Alex IA respondeu:")
            st.write(resposta.text)

    except Exception as e:
        st.error(f"Erro: {e}")
