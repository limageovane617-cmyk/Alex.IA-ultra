# ============================================================
# 🖼️ ALEX IA ULTRA — GERENCIADOR DE IMAGENS NVIDIA
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
    "https://integrate.api.nvidia.com/v1/images/generations"
)

MODELO_IMAGEM = "flux.1-dev"


# ============================================================
# 🔐 CHAVE NVIDIA
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

    st.session_state.ultima_imagem = imagem
    st.session_state.ultima_imagem_caminho = caminho
    st.session_state.ultimo_prompt_imagem = prompt
    st.session_state.ultimo_motor_imagem = motor


# ============================================================
# 🎨 GERAR IMAGEM NVIDIA
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
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    dados = {
        "model": MODELO_IMAGEM,
        "prompt": prompt.strip(),
        "size": "1024x1024",
        "n": 1,
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
            f"{resposta.text[:3000]}"
        )

    resultado = resposta.json()

    data = resultado.get(
        "data",
        []
    )

    if not data:
        raise RuntimeError(
            "A NVIDIA respondeu, mas não "
            "retornou nenhuma imagem."
        )

    primeira = data[0]

    # --------------------------------------------------------
    # URL DA IMAGEM
    # --------------------------------------------------------

    url = primeira.get("url")

    if url:

        imagem_resposta = requests.get(
            url,
            timeout=180
        )

        if imagem_resposta.status_code != 200:
            raise RuntimeError(
                "Não foi possível baixar "
                "a imagem da NVIDIA."
            )

        imagem_bytes = imagem_resposta.content

    # --------------------------------------------------------
    # BASE64
    # --------------------------------------------------------

    else:

        b64 = primeira.get(
            "b64_json"
        )

        if not b64:
            raise RuntimeError(
                "A resposta da NVIDIA não contém "
                "URL nem b64_json."
            )

        imagem_bytes = base64.b64decode(
            b64
        )

    # --------------------------------------------------------
    # SALVAR IMAGEM
    # --------------------------------------------------------

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
        use_container_width=True,
    )

    motor = st.session_state.get(
        "ultimo_motor_imagem",
        ""
    )

    if motor:

        st.caption(
            f"🎨 Motor utilizado: {motor}"
        )

    return True


# ============================================================
# 🔎 ACESSAR ÚLTIMA IMAGEM
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
