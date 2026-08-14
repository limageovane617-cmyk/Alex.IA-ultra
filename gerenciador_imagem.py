# ============================================================
# 🖼️ ALEX IA ULTRA — GERENCIADOR DE IMAGENS NVIDIA
# FLUX.1-dev / NVIDIA NIM
# Criado por Geovani
# ============================================================

import os
import base64
from pathlib import Path

import requests
import streamlit as st


# ============================================================
# ⚙️ CONFIGURAÇÃO
# ============================================================

NVIDIA_API_URL = (
    "https://ai.api.nvidia.com/v1/genai/"
    "black-forest-labs/flux.1-dev"
)

MODELO_IMAGEM = "black-forest-labs/flux.1-dev"


# ============================================================
# 🔐 CHAVE NVIDIA
# ============================================================

def obter_chave_nvidia():

    try:
        chave = st.secrets.get(
            "NVIDIA_API_KEY",
            ""
        )

        if chave:
            return str(chave).strip()

    except Exception:
        pass

    chave = os.environ.get(
        "NVIDIA_API_KEY",
        ""
    )

    return str(chave).strip()


# ============================================================
# 📁 PASTA
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

    st.session_state.ultima_imagem = imagem

    st.session_state.ultima_imagem_caminho = caminho

    st.session_state.ultimo_prompt_imagem = prompt

    st.session_state.ultimo_motor_imagem = motor


# ============================================================
# 🎨 GERAR IMAGEM
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

    # ========================================================
    # PAYLOAD FLUX.1-dev
    # ========================================================

    dados = {
        "prompt": prompt.strip(),
        "width": 1024,
        "height": 1024,
        "steps": 30,
        "cfg_scale": 5,
        "seed": 0,
        "samples": 1,
    }

    # ========================================================
    # POST NVIDIA
    # ========================================================

    resposta = requests.post(
        NVIDIA_API_URL,
        headers=headers,
        json=dados,
        timeout=300,
    )

    # ========================================================
    # ERRO
    # ========================================================

    if resposta.status_code != 200:

        try:
            detalhe = resposta.json()
        except Exception:
            detalhe = resposta.text

        raise RuntimeError(
            f"NVIDIA HTTP {resposta.status_code}:\n"
            f"{detalhe}"
        )

    # ========================================================
    # JSON
    # ========================================================

    try:

        resultado = resposta.json()

    except Exception:

        raise RuntimeError(
            "A NVIDIA respondeu, mas não retornou "
            "JSON válido."
        )

    # ========================================================
    # ARTIFACTS
    # ========================================================

    artifacts = resultado.get(
        "artifacts",
        []
    )

    if not artifacts:

        raise RuntimeError(
            "A NVIDIA respondeu, mas não retornou "
            "nenhuma imagem."
        )

    primeiro = artifacts[0]

    # ========================================================
    # BASE64
    # ========================================================

    imagem_base64 = primeiro.get(
        "base64"
    )

    if not imagem_base64:

        raise RuntimeError(
            "A NVIDIA retornou o resultado, "
            "mas não encontrou a imagem em base64."
        )

    try:

        imagem_bytes = base64.b64decode(
            imagem_base64
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro ao decodificar imagem: {erro}"
        )

    # ========================================================
    # SALVAR
    # ========================================================

    caminho = (
        obter_pasta_imagens()
        / "ultima_imagem.png"
    )

    with open(
        caminho,
        "wb"
    ) as arquivo:

        arquivo.write(
            imagem_bytes
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
            )
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
# 🖼️ MOSTRAR IMAGEM
# ============================================================

def mostrar_imagem(prompt):

    with st.spinner(
        "🎨 Alex IA está criando sua imagem..."
    ):

        imagem, mensagem = gerar_imagem(
            prompt
        )

    if imagem is None:

        st.error(
            mensagem
        )

        return False

    st.image(
        imagem,
        caption=(
            "🖼️ Imagem gerada pela "
            "Alex IA Ultra"
        ),
        use_container_width=True
    )

    motor = st.session_state.get(
        "ultimo_motor_imagem"
    )

    if motor:

        st.caption(
            f"🎨 Motor utilizado: {motor}"
        )

    return True


# ============================================================
# 🔎 FUNÇÕES DE ACESSO
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
# 🧹 LIMPAR
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
