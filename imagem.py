# ============================================================
# 🖼️ ALEX IA ULTRA — GERAÇÃO DE IMAGENS
# Criada por Geovani
# ============================================================

import os
import streamlit as st
from gradio_client import Client


# ============================================================
# 🎨 CONFIGURAÇÃO DO MOTOR
# ============================================================

SPACE_IMAGEM = "mrfakename/Z-Image-Turbo"


# ============================================================
# 🖼️ GERAR IMAGEM
# ============================================================

def gerar_imagem(prompt):
    """
    Gera uma imagem usando o Z Image Turbo
    através do Gradio Client.
    """

    if not prompt or not prompt.strip():

        return (
            None,
            "❌ O prompt da imagem está vazio."
        )

    try:

        cliente = Client(
            SPACE_IMAGEM
        )

        resultado = cliente.predict(
            prompt.strip(),
            1024,
            1024,
            9,
            42,
            True,
            api_name="/generate_image"
        )

        if isinstance(resultado, tuple):

            imagem = resultado[0]

        else:

            imagem = resultado

        if not imagem:

            return (
                None,
                "❌ O gerador terminou, mas não retornou uma imagem."
            )

        return (
            imagem,
            None
        )

    except Exception as erro:

        return (
            None,
            f"❌ Erro ao gerar imagem: {erro}"
        )


# ============================================================
# 💾 GUARDAR ÚLTIMA IMAGEM
# ============================================================

def guardar_ultima_imagem(imagem, prompt):
    """
    Guarda a última imagem gerada na sessão.

    Isso permite que a Alex analise a imagem
    posteriormente.
    """

    try:

        st.session_state.ultima_imagem = imagem
        st.session_state.ultimo_prompt_imagem = prompt

        return True

    except Exception:

        return False


# ============================================================
# 🖼️ MOSTRAR IMAGEM
# ============================================================

def mostrar_imagem(prompt):
    """
    Gera, guarda e mostra a imagem no Streamlit.
    """

    with st.spinner(
        "🎨 Alex IA está criando sua imagem..."
    ):

        imagem, erro = gerar_imagem(
            prompt
        )

    if erro:

        st.error(
            erro
        )

        return False

    # --------------------------------------------------------
    # Guarda a imagem para análise posterior
    # --------------------------------------------------------

    guardar_ultima_imagem(
        imagem,
        prompt
    )

    # --------------------------------------------------------
    # Mostra a imagem
    # --------------------------------------------------------

    st.image(
        imagem,
        caption="🖼️ Imagem gerada pela Alex IA Ultra",
        use_container_width=True
    )

    return True
