import streamlit as st

st.title("🔐 Teste do HF_TOKEN")

try:
    token = st.secrets["HF_TOKEN"]

    st.write("Secret encontrado:", True)
    st.write("Começa com hf_:", token.startswith("hf_"))
    st.write("Tem espaços no começo/fim:", token != token.strip())
    st.write("Quantidade de caracteres:", len(token))

except Exception as erro:
    st.error("❌ Não consegui ler HF_TOKEN.")
    st.code(str(erro))
