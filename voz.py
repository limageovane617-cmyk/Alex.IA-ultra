# ============================================================
# 🔊 ALEX IA ULTRA — SISTEMA DE VOZ
# Criada por Geovani
# ============================================================

import io
import wave

import streamlit as st
from google import genai
from google.genai import types


# Modelo atual de voz
MODELO_VOZ = "gemini-3.1-flash-tts-preview"

# Voz da Alex
VOZ_ALEX = "Kore"


def pcm_para_wav(audio_pcm):
    """
    Converte o áudio PCM retornado pelo Gemini
    para um arquivo WAV reproduzível pelo navegador.
    """

    arquivo = io.BytesIO()

    with wave.open(arquivo, "wb") as wav:

        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)

        wav.writeframes(audio_pcm)

    return arquivo.getvalue()


def gerar_audio(texto):
    """
    Gera a voz da Alex a partir de um texto.
    """

    if not texto or not texto.strip():
        return None, "O texto está vazio."

    try:

        api_key = st.secrets["GEMINI_API_KEY"]

        cliente = genai.Client(
            api_key=api_key
        )

        resposta = cliente.models.generate_content(
            model=MODELO_VOZ,
            contents=texto.strip(),
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=VOZ_ALEX
                        )
                    )
                )
            )
        )

        if not resposta.candidates:
            return None, "O Gemini não retornou áudio."

        partes = resposta.candidates[0].content.parts

        for parte in partes:

            if hasattr(parte, "inline_data") and parte.inline_data:

                audio_pcm = parte.inline_data.data

                audio_wav = pcm_para_wav(
                    audio_pcm
                )

                return audio_wav, None

        return None, "Nenhum áudio foi encontrado."

    except Exception as erro:

        return None, str(erro)


def mostrar_audio(texto):
    """
    Gera e mostra o áudio da Alex no Streamlit.
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
