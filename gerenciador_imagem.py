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
    "https://ai.api.nvidia.com/v1/genai/"
    "black-forest-labs/flux.1-dev"
)

MODELO_IMAGEM = "black-forest-labs/flux.1-dev"


# ============================================================
# 🔐 OBTER CHAVE
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
# 💾 GUARDAR IMAGEM
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
# 🎨 GERAR COM NVIDIA
# ============================================================

def gerar_imagem_nvidia(prompt):

    chave = obter_chave_nvidia()

    if not chave:

        raise RuntimeError(
            "NVIDIA_API_KEY não encontrada nos Secrets."
        )

    headers = {
        "Authorization": f"Bearer {chave}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    dados = {
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

    # --------------------------------------------------------
    # ERROS
    # --------------------------------------------------------

    if resposta.status_code == 401:

        raise RuntimeError(
            "NVIDIA HTTP 401: a chave não foi aceita."
        )

    if resposta.status_code == 403:

        raise RuntimeError(
            "NVIDIA HTTP 403: a NVIDIA recusou "
            "a autorização da chave."
        )

    if resposta.status_code == 404:

        raise RuntimeError(
            "NVIDIA HTTP 404: o endpoint/modelo "
            "FLUX.1-dev não está disponível nesse endereço."
        )

    if resposta.status_code == 405:

        raise RuntimeError(
            "NVIDIA HTTP 405: método HTTP não permitido "
            "nesse endpoint."
        )

    if resposta.status_code != 200:

        raise RuntimeError(
            f"NVIDIA HTTP {resposta.status_code}: "
            f"{resposta.text[:2000]}"
        )

    # --------------------------------------------------------
    # RESPOSTA
    # --------------------------------------------------------

    try:
        resultado = resposta.json()

    except Exception:

        raise RuntimeError(
            "A NVIDIA respondeu, mas a resposta "
            "não está em JSON."
        )

    data = resultado.get(
        "data",
        []
    )

    if not data:

        raise RuntimeError(
            "A NVIDIA respondeu sem retornar "
            "uma imagem."
        )

    primeiro = data[0]

    # --------------------------------------------------------
    # URL
    # --------------------------------------------------------

    url = primeiro.get(
        "url"
    )

    if url:

        download = requests.get(
            url,
            timeout=180
        )

        if download.status_code != 200:

            raise RuntimeError(
                "Não foi possível baixar "
                "a imagem retornada."
            )

        imagem_bytes = download.content

    # --------------------------------------------------------
    # BASE64
    # --------------------------------------------------------

    else:

        b64 = primeiro.get(
            "b64_json"
        )

        if not b64:

            raise RuntimeError(
                "A resposta não contém "
                "URL nem b64_json."
            )

        try:

            imagem_bytes = base64.b64decode(
                b64
            )

        except Exception:

            raise RuntimeError(
                "Não foi possível decodificar "
                "a imagem retornada."
            )

    # --------------------------------------------------------
    # SALVAR
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
            motor=MODELO_IMAGEM
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
        caption="🖼️ Imagem gerada pela Alex IA Ultra",
        use_container_width=True
    )

    motor = st.session_state.get(
        "ultimo_motor_imagem",
        ""
    )

    if motor:

        st.caption(
            f"🎨 Motor: NVIDIA / {motor}"
        )

    return True


# ============================================================
# 🔎 ÚLTIMA IMAGEM
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
