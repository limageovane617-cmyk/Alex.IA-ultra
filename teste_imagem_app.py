import streamlit as st
import requests

st.title("🔐 Teste Hugging Face")

token = st.secrets["HF_TOKEN"]

headers = {
    "Authorization": f"Bearer {token}"
}

resposta = requests.get(
    "https://huggingface.co/api/whoami-v2",
    headers=headers,
    timeout=30
)

st.write("Código:", resposta.status_code)

if resposta.status_code == 200:
    dados = resposta.json()

    st.success("✅ Token autenticado com sucesso!")
    st.write("Usuário:", dados.get("name"))

else:
    st.error("❌ Hugging Face recusou o token.")
    st.code(resposta.text)
