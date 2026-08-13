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
# ⚙️ CONFIGURAÇÃO NVIDIA
# ============================================================

NVIDIA_URL = "https://integrate.api.nvidia.com/v1/images/generations"

MOTORES_IMAGEM = [
    "flux.2-klein-4b",
    "qwen-image",
    "flux.1-schnell",
    "stable-diffusion-3.5-large",
]


# ============================================================
# 🔐 CHAVE NVIDIA
# ============================================================

def obter_chave_nvidia():

    try:
        chave = st.secrets["NVIDIA_API_KEY"]

        if chave:
            return str(chave).strip()

    except Exception:
        pass

    return None


# ============================================================
# 📁 PASTA DAS IMAGENS
# ============================================================

def obter_pasta_imagens():

    pasta = Path("/tmp/alex_ia_ultra_imagens")

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

def _gerar_com_nvidia(prompt, modelo):

    chave = obter_chave_nvidia()

    if not chave:

        raise RuntimeError(
            "A chave NVIDIA_API_KEY não foi encontrada "
            "nos Secrets do Streamlit."
        )

    headers = {
        "Authorization": f"Bearer {chave}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    dados = {
        "model": modelo,
        "prompt": prompt,
        "size": "1024x1024",
        "n": 1,
    }

    resposta = requests.post(
        NVIDIA_URL,
        headers=headers,
        json=dados,
        timeout=180,
    )

    if resposta.status_code != 200:

        raise RuntimeError(
            f"HTTP {resposta.status_code}: "
            f"{resposta.text}"
        )

    resultado = resposta.json()

    imagens = resultado.get("data", [])

    if not imagens:

        raise RuntimeError(
            "A NVIDIA respondeu, mas não retornou "
            "nenhuma imagem."
        )

    imagem = imagens[0]

    # --------------------------------------------------------
    # URL
    # --------------------------------------------------------

    url = imagem.get("url")

    if url:

        imagem_resposta = requests.get(
            url,
            timeout=180
        )

        imagem_resposta.raise_for_status()

        imagem_bytes = imagem_resposta.content

    # --------------------------------------------------------
    # BASE64
    # --------------------------------------------------------

    else:

        b64 = imagem.get("b64_json")

        if not b64:

            raise RuntimeError(
                "A resposta da NVIDIA não contém "
                "URL nem b64_json."
            )

        imagem_bytes = base64.b64decode(b64)

    # --------------------------------------------------------
    # SALVAR
    # --------------------------------------------------------

    pasta = obter_pasta_imagens()

    caminho = pasta / "ultima_imagem.png"

    with open(caminho, "wb") as arquivo:

        arquivo.write(imagem_bytes)

    return str(caminho)


# ============================================================
# 🖼️ GERAR IMAGEM — FALLBACK
# ============================================================

def gerar_imagem(prompt):

    if not prompt or not prompt.strip():

        return (
            None,
            "❌ O prompt da imagem está vazio."
        )

    erros = []

    for modelo in MOTORES_IMAGEM:

        try:

            caminho = _gerar_com_nvidia(
                prompt.strip(),
                modelo
            )

            guardar_ultima_imagem(
                imagem=caminho,
                prompt=prompt,
                caminho=caminho,
                motor=modelo
            )

            return (
                caminho,
                f"🖼️ Imagem gerada pela NVIDIA "
                f"com {modelo}."
            )

        except Exception as erro:

            erros.append(
                f"{modelo}: {erro}"
            )

            continue

    return (
        None,
        "❌ Todos os motores de imagem NVIDIA "
        "falharam.\n\n"
        + "\n\n".join(erros)
    )


# ============================================================
# 🖼️ MOSTRAR IMAGEM
# ============================================================

def mostrar_imagem(prompt):

    with st.spinner(
        "🎨 Alex IA está criando sua imagem..."
    ):

        imagem, mensagem = gerar_imagem(prompt)

    if imagem is None:

        st.error(mensagem)

        return False

    st.image(
        imagem,
        caption="🖼️ Imagem gerada pela Alex IA Ultra",
        use_container_width=True,
    )

    motor = st.session_state.get(
        "ultimo_motor_imagem"
    )

    if motor:

        st.caption(
            f"🎨 Motor utilizado: NVIDIA / {motor}"
        )

    return True


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


# ============================================================
# 🧹 LIMPAR ÚLTIMA IMAGEM
# ============================================================

def limpar_ultima_imagem():

    for chave in [
        "ultima_imagem",
        "ultima_imagem_caminho",
        "ultimo_prompt_imagem",
        "ultimo_motor_imagem",
    ]:

        st.session_state.pop(
            chave,
            None
    )
