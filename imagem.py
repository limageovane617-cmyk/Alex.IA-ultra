# ============================================================
# 🖼️ ALEX IA ULTRA — GERAÇÃO DE IMAGENS
# Criada por Geovani
# ============================================================

import streamlit as st
from huggingface_hub import InferenceClient


MODELO_IMAGEM = "black-forest-labs/FLUX.1-schnell"


def gerar_imagem(prompt):
    """
    Gera uma imagem usando o Hugging Face.
    """

    if not prompt or not prompt.strip():
        return None, "O prompt da imagem está vazio."

    try:

        token = st.secrets["HF_TOKEN"]

        cliente = InferenceClient(
            api_key=token
        )

        imagem = cliente.text_to_image(
            prompt=prompt.strip(),
            model=MODELO_IMAGEM
        )

        return imagem, None

    except Exception as erro:

        return None, str(erro)


def mostrar_imagem(prompt):
    """
    Gera e mostra a imagem no Streamlit.
    """

    imagem, erro = gerar_imagem(prompt)

    if erro:

        st.error(
            f"❌ Erro ao gerar imagem: {erro}"
        )

        return False

    st.image(
        imagem,
        caption="🖼️ Imagem gerada pela Alex IA",
        use_container_width=True
    )

    return True
