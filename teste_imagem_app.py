import streamlit as st
import requests

st.set_page_config(
    page_title="Teste FLUX",
    page_icon="🖼️"
)

st.title("🖼️ Teste FLUX")
st.write("Teste de autenticação do Hugging Face.")

prompt = st.text_area(
    "📝 Descrição da imagem",
    "Uma cidade futurista à noite, ruas molhadas refletindo luzes neon."
)

if st.button("🖼️ Testar imagem", type="primary"):

    try:
        token = st.secrets["HF_TOKEN"]

        headers = {
            "Authorization": f"Bearer {token}"
        }

        resposta = requests.get(
            "https://huggingface.co/api/whoami-v2",
            headers=headers,
            timeout=30
        )

        st.write("Código de resposta:", resposta.status_code)

        if resposta.status_code == 200:
            st.success("✅ O token do Hugging Face está válido!")

            dados = resposta.json()

            st.write(
                "Conta autenticada:",
                dados.get("name", "desconhecida")
            )

        else:
            st.error("❌ O token foi recusado pelo Hugging Face.")
            st.code(resposta.text)

    except Exception as erro:
        st.error("❌ Erro no teste.")
        st.code(str(erro))
