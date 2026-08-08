# ============================================================
# 🔊 ALEX IA ULTRA — SISTEMA DE VOZ
# Criada por Geovani
# ============================================================

import streamlit as st
from google import genai


def gerar_audio(texto):
    """
    Gera áudio a partir do texto da Alex.

    A chave do Gemini será obtida pelos Secrets
    do Streamlit.
    """

    if not texto or not texto.strip():
        return None, "O texto está vazio."

    try:

        api_key = st.secrets["GEMINI_API_KEY"]

        cliente = genai.Client(
            api_key=api_key
        )

        resposta = cliente.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=texto.strip(),
            config={
                "response_modalities": ["AUDIO"]
            }
        )

        if not resposta.candidates:
            return None, "O Gemini não retornou áudio."

        partes = resposta.candidates[0].content.parts

        for parte in partes:

            if hasattr(parte, "inline_data") and parte.inline_data:

                return parte.inline_data.data, None

        return None, "Nenhum áudio foi encontrado na resposta."

    except Exception as erro:

        return None, str(erro)


def mostrar_audio(texto):
    """
    Gera e mostra o áudio no Streamlit.
    """

    audio, erro = gerar_audio(texto)

    if erro:

        st.error(
            f"❌ Erro ao gerar voz: {erro}"
        )

        return False

    st.audio(
        audio,
        format="audio/wav"
    )

    return True
