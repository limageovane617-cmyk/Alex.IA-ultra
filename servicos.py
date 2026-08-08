# ============================================================
# 🔐 ALEX IA ULTRA — SERVIÇOS E CONEXÕES
# Criada por Geovani
# ============================================================

import streamlit as st
from google import genai
from huggingface_hub import InferenceClient


def obter_chave_gemini():
    """Obtém a chave do Gemini pelos Secrets."""

    try:
        return st.secrets["GEMINI_API_KEY"]

    except Exception:
        return None


def obter_token_huggingface():
    """Obtém o token do Hugging Face pelos Secrets."""

    try:
        return st.secrets["HF_TOKEN"]

    except Exception:
        return None


def criar_cliente_gemini():
    """Cria o cliente do Google Gemini."""

    chave = obter_chave_gemini()

    if not chave:
        return None

    return genai.Client(
        api_key=chave
    )


def criar_cliente_huggingface():
    """Cria o cliente do Hugging Face."""

    token = obter_token_huggingface()

    if not token:
        return None

    return InferenceClient(
        provider="auto",
        api_key=token
    )


def verificar_servicos():
    """
    Verifica se as credenciais principais
    estão configuradas.
    """

    resultado = {
        "gemini": bool(obter_chave_gemini()),
        "huggingface": bool(obter_token_huggingface())
    }

    return resultado
