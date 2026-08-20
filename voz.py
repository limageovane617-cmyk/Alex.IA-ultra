# ============================================================
# 🔊 ALEX IA ULTRA — SISTEMA DE VOZ (COM BACKUP AUTOMÁTICO)
# Criada por Geovani
# ============================================================

import io
import re
import wave

import streamlit as st
from google import genai
from google.genai import types
from gtts import gTTS

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


def limpar_texto(texto):
    """
    Remove caracteres especiais de formatação Markdown.
    """
    return re.sub(r"[\*\#\`\_\~\-\>]", "", texto).strip()


def gerar_audio_gtts(texto):
    """
    Backup de voz ilimitado via gTTS em Português do Brasil.
    """
    try:
        texto_clean = limpar_texto(texto)
        if len(texto_clean) > 800:
            texto_clean = texto_clean[:800] + "..."

        fp = io.BytesIO()
        tts = gTTS(text=texto_clean, lang="pt", tld="com.br")
        tts.write_to_fp(fp)
        return fp.getvalue(), None
    except Exception as e:
        return None, str(e)


def gerar_audio(texto):
    """
    Gera a voz da Alex. Tenta Gemini (Kore) e usa gTTS como backup.
    """
    if not texto or not texto.strip():
        return None, "O texto está vazio.", "none"

    # 1. TENTA O MODELO GEMINI KORE PRIMEIRO
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        cliente = genai.Client(api_key=api_key)

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
                ),
            ),
        )

        if resposta.candidates:
            partes = resposta.candidates[0].content.parts
            for parte in partes:
                if hasattr(parte, "inline_data") and parte.inline_data:
                    audio_pcm = parte.inline_data.data
                    audio_wav = pcm_para_wav(audio_pcm)
                    return audio_wav, None, "audio/wav"

    except Exception:
        pass  # Se der limite de cota (429) ou erro, cai no backup silenciosamente

    # 2. SE O GEMINI FALHAR, USA O BACKUP PERMANENTE (gTTS)
    audio_backup, erro_backup = gerar_audio_gtts(texto)
    if audio_backup:
        return audio_backup, None, "audio/mp3"

    return None, erro_backup or "Não foi possível gerar áudio.", "none"


def mostrar_audio(texto):
    """
    Gera e mostra o áudio da Alex no Streamlit.
    """
    audio, erro, formato = gerar_audio(texto)

    if erro or not audio:
        return False

    st.audio(audio, format=formato)
    return True
    
