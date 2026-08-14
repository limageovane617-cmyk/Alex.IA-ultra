# ============================================================
# 🖼️ ALEX IA ULTRA — GERENCIADOR DE IMAGENS NVIDIA
# TESTE DE LOCALIZAÇÃO DO ERRO
# Criado por Geovani
# ============================================================

import os
from pathlib import Path

import requests
import streamlit as st


# ============================================================
# 🧪 TESTE DE CARREGAMENTO
# ============================================================

st.sidebar.error("🔥 GERENCIADOR NVIDIA NOVO — TESTE 999")


# ============================================================
# ⚙️ CONFIGURAÇÃO NVIDIA
# ============================================================

NVIDIA_API_URL = (
    "https://ai.api.nvidia.com/v1/genai/"
    "black-forest-labs/flux.1-dev"
)

MODELO_IMAGEM = "black-forest-labs/FLUX.1-dev"


# ============================================================
# 🔐 OBTER CHAVE NVIDIA
# ============================================================

def obter_chave_nvidia():

    try:
        chave = st.secrets.get(
            "NVIDIA_API_KEY",
            ""
        )
    except Exception:
        chave = ""

    if not chave:
        chave = os.environ.get(
            "NVIDIA_API_KEY",
            ""
        )

    return str(chave).strip()


# ============================================================
# 📁 PASTA DAS IMAGENS
# ============================================================

def obter_pasta_imagens():

    pasta = Path(
        "/tmp/alex_ia_ultra_imagens"
    )

    pasta.mkdir(
        parents=True,
        exist_ok=True
    )

    return pasta


# ============================================================
# 💾 GUARDAR ÚLTIMA IMAGEM
# ============================================================

def guardar_ultima_imagem(
    imagem,
    prompt,
    caminho=None,
    motor=None
):

    try:

        st.session_state.ultima_imagem = imagem

        st.session_state.ultima_imagem_caminho = caminho

        st.session_state.ultimo_prompt_imagem = prompt

        st.session_state.ultimo_motor_imagem = motor

        return True

    except Exception:

        return False


# ============================================================
# 🎨 GERAR IMAGEM COM NVIDIA
# ============================================================

def gerar_imagem_nvidia(prompt):

    chave = obter_chave_nvidia()

    if not chave:

        raise RuntimeError(
            "NVIDIA_API_KEY não encontrada "
            "nos Secrets do Streamlit."
        )

    headers = {
        "Authorization": f"Bearer {chave}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    dados = {
        "model": MODELO_IMAGEM,
        "prompt": prompt.strip(),
        "width": 1024,
        "height": 1024,
        "steps": 30,
        "cfg_scale": 5,
        "seed": 0,
    }

    resposta = requests.post(
        NVIDIA_API_URL,
        headers=headers,
        json=dados,
        timeout=180,
    )

    if resposta.status_code != 200:

        raise RuntimeError(
            f"NVIDIA HTTP {resposta.status_code}: "
            f"{resposta.text[:2000]}"
        )

    resultado = resposta.json()

    data = resultado.get(
        "data",
        []
    )

    if not data:

        raise RuntimeError(
            "A NVIDIA respondeu, mas não retornou "
            "dados de imagem."
        )

    primeiro = data[0]

    url_imagem = primeiro.get(
        "url"
    )

    if url_imagem:

        imagem_resposta = requests.get(
            url_imagem,
            timeout=180,
        )

        if imagem_resposta.status_code != 200:

            raise RuntimeError(
                "Não foi possível baixar "
                "a imagem retornada pela NVIDIA."
            )

        bytes_imagem = imagem_resposta.content

    else:

        import base64

        b64 = primeiro.get(
            "b64_json"
        )

        if not b64:

            raise RuntimeError(
                "A resposta da NVIDIA não contém "
                "URL nem imagem base64."
            )

        bytes_imagem = base64.b64decode(
            b64
        )

    caminho = (
        obter_pasta_imagens()
        / "ultima_imagem.png"
    )

    with open(
        caminho,
        "wb"
    ) as arquivo:

        arquivo.write(
            bytes_imagem
        )

    return str(caminho)


# ============================================================
# 🖼️ GERADOR PRINCIPAL
# ============================================================

def gerar_imagem(prompt):

    if not prompt or not prompt.strip():

        return (
            None,
            "❌ O prompt da imagem está vazio."
        )

    try:

        caminho = gerar_imagem_nvidia(
            prompt
        )

        guardar_ultima_imagem(
            imagem=caminho,
            prompt=prompt,
            caminho=caminho,
            motor=(
                "NVIDIA NIM / "
                f"{MODELO_IMAGEM}"
            ),
        )

        return (
            caminho,
            "🖼️ Imagem gerada pela NVIDIA."
        )

    except Exception as erro:

        return (
            None,
            (
                "❌ Erro ao gerar imagem pela NVIDIA:\n\n"
                f"{erro}"
            )
        )


# ============================================================
# 🖼️ MOSTRAR IMAGEM — TESTE
# ============================================================

def mostrar_imagem(prompt):

    st.error(
        "🧪 CHEGUEI NO mostrar_imagem DO NVIDIA"
    )

    st.write(
        f"Prompt recebido: {prompt}"
    )

    return False


# ============================================================
# 🔎 ACESSO À ÚLTIMA IMAGEM
# ============================================================

def obter_ultima_imagem():

    return st.session_state.get(
        "ultima_imagem"
    )


def obter_caminho_ultima_imagem():

    return st.session_state.get(
        "ultima_imagem_caminho"
    )


def obter_prompt_ultima_imagem():

    return st.session_state.get(
        "ultimo_prompt_imagem",
        ""
    )


def obter_motor_ultima_imagem():

    return st.session_state.get(
        "ultimo_motor_imagem",
        ""
    )


# ============================================================
# 🧹 LIMPAR ÚLTIMA IMAGEM
# ============================================================

def limpar_ultima_imagem():

    chaves = [
        "ultima_imagem",
        "ultima_imagem_caminho",
        "ultimo_prompt_imagem",
        "ultimo_motor_imagem",
    ]

    for chave in chaves:

        st.session_state.pop(
            chave,
            None
        )
