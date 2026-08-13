# ============================================================
# 🖼️ ALEX IA ULTRA — GERAÇÃO DE IMAGENS
# Criada por Geovani
# ============================================================

import io
import os

import streamlit as st
from PIL import Image

from servicos import criar_cliente_gemini


# ============================================================
# 🎨 CONFIGURAÇÃO DO MOTOR
# ============================================================

MODELO_IMAGEM = "gemini-3.1-flash-image"


# ============================================================
# 🖼️ GERAR IMAGEM
# ============================================================

def gerar_imagem(prompt):
    """
    Gera uma imagem usando o Gemini 3.1 Flash Image.
    """

    if not prompt or not prompt.strip():

        return (
            None,
            "❌ O prompt da imagem está vazio."
        )

    try:

        cliente = criar_cliente_gemini()

        if cliente is None:

            return (
                None,
                "❌ Não foi possível conectar ao Gemini. "
                "Verifique GEMINI_API_KEY nos Secrets."
            )

        resposta = cliente.models.generate_content(
            model=MODELO_IMAGEM,
            contents=prompt.strip(),
            config={
                "response_modalities": ["IMAGE"],
            }
        )

        if not resposta or not resposta.candidates:

            return (
                None,
                "❌ O Gemini não retornou uma resposta."
            )

        # ----------------------------------------------------
        # 🔎 Procurar a imagem na resposta
        # ----------------------------------------------------

        for candidato in resposta.candidates:

            conteudo = getattr(
                candidato,
                "content",
                None
            )

            if not conteudo:
                continue

            partes = getattr(
                conteudo,
                "parts",
                []
            )

            for parte in partes:

                dados_imagem = getattr(
                    parte,
                    "inline_data",
                    None
                )

                if dados_imagem:

                    mime_type = getattr(
                        dados_imagem,
                        "mime_type",
                        "image/png"
                    )

                    dados = getattr(
                        dados_imagem,
                        "data",
                        None
                    )

                    if dados:

                        imagem = Image.open(
                            io.BytesIO(dados)
                        )

                        return (
                            imagem,
                            None
                        )

        return (
            None,
            "❌ O Gemini terminou, mas não retornou uma imagem."
        )

    except Exception as erro:

        return (
            None,
            f"❌ Erro ao gerar imagem: {erro}"
        )


# ============================================================
# 💾 GUARDAR ÚLTIMA IMAGEM
# ============================================================

def guardar_ultima_imagem(
    imagem,
    prompt
):
    """
    Guarda a última imagem gerada na sessão.

    Isso permite que a Alex possa analisar
    posteriormente a imagem criada.
    """

    try:

        # Guarda a imagem diretamente.
        st.session_state.ultima_imagem = imagem

        # Guarda o prompt utilizado.
        st.session_state.ultimo_prompt_imagem = prompt

        # ----------------------------------------------------
        # 💾 Salvar também em arquivo temporário
        # ----------------------------------------------------

        caminho = None

        if isinstance(imagem, Image.Image):

            pasta = os.path.join(
                "/tmp",
                "alex_ia_ultra"
            )

            os.makedirs(
                pasta,
                exist_ok=True
            )

            caminho = os.path.join(
                pasta,
                "ultima_imagem.png"
            )

            imagem.save(
                caminho,
                format="PNG"
            )

        st.session_state.ultima_imagem_caminho = caminho

        return True

    except Exception:

        st.session_state.ultima_imagem = imagem
        st.session_state.ultimo_prompt_imagem = prompt
        st.session_state.ultima_imagem_caminho = None

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
