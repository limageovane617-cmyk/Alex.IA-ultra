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

        # ----------------------------------------------------
        # 📦 Resultado da Space
        # ----------------------------------------------------

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
    Guarda a última imagem gerada para que a Alex
    possa analisá-la posteriormente.
    """

    try:

        caminho_imagem = None

        # ----------------------------------------------------
        # 📁 Quando o Gradio retorna um caminho
        # ----------------------------------------------------

        if isinstance(imagem, str):

            caminho_imagem = imagem

        # ----------------------------------------------------
        # 📁 Quando o resultado possui atributo path
        # ----------------------------------------------------

        elif hasattr(imagem, "path"):

            caminho_imagem = imagem.path

        # ----------------------------------------------------
        # 🧠 Guardar informações na sessão
        # ----------------------------------------------------

        st.session_state.ultima_imagem = imagem

        st.session_state.ultima_imagem_caminho = (
            caminho_imagem
        )

        st.session_state.ultimo_prompt_imagem = prompt

        return True

    except Exception:

        st.session_state.ultima_imagem = imagem

        st.session_state.ultima_imagem_caminho = None

        st.session_state.ultimo_prompt_imagem = prompt

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

    # --------------------------------------------------------
    # ❌ Erro
    # --------------------------------------------------------

    if erro:

        st.error(
            erro
        )

        return False

    # --------------------------------------------------------
    # 💾 Guardar imagem
    # --------------------------------------------------------

    guardar_ultima_imagem(
        imagem,
        prompt
    )

    # --------------------------------------------------------
    # 🖼️ Mostrar imagem
    # --------------------------------------------------------

    st.image(
        imagem,
        caption="🖼️ Imagem gerada pela Alex IA Ultra",
        use_container_width=True
    )

    return True
