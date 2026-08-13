# ============================================================
# 🖼️ ALEX IA ULTRA — GERENCIADOR DE IMAGENS
# Pollinations API
# Criado por Geovani
# ============================================================

import os
import re
from pathlib import Path
from urllib.parse import quote

import requests
import streamlit as st


# ============================================================
# ⚙️ CONFIGURAÇÃO
# ============================================================

POLLINATIONS_URL = "https://gen.pollinations.ai"

# Modelos de imagem.
# Se um falhar, o próximo será tentado automaticamente.
MOTORES_IMAGEM = [
    "flux",
    "zimage",
    "qwen-image",
    "seedream",
    "gptimage",
    "nanobanana",
]


# ============================================================
# 🔐 OBTER CHAVE
# ============================================================

def obter_chave_pollinations():
    """
    Obtém a chave do Streamlit Secrets ou variável de ambiente.

    A chave NÃO fica dentro do código.
    """

    try:
        chave = st.secrets.get(
            "POLLINATIONS_API_KEY",
            ""
        )
    except Exception:
        chave = ""

    if not chave:
        chave = os.environ.get(
            "POLLINATIONS_API_KEY",
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
    """
    Guarda informações da última imagem gerada.
    """

    try:

        st.session_state.ultima_imagem = imagem

        st.session_state.ultima_imagem_caminho = (
            caminho
        )

        st.session_state.ultimo_prompt_imagem = (
            prompt
        )

        st.session_state.ultimo_motor_imagem = (
            motor
        )

        return True

    except Exception:

        return False


# ============================================================
# 🎨 GERAR IMAGEM COM POLLINATIONS
# ============================================================

def _gerar_com_pollinations(
    prompt,
    modelo
):
    """
    Gera uma imagem através da API oficial
    do Pollinations.
    """

    chave = obter_chave_pollinations()

    if not chave:

        raise RuntimeError(
            "POLLINATIONS_API_KEY não configurada "
            "nos Secrets do Streamlit."
        )

    prompt_codificado = quote(
        prompt.strip(),
        safe=""
    )

    url = (
        f"{POLLINATIONS_URL}/image/"
        f"{prompt_codificado}"
    )

    parametros = {
        "model": modelo,
        "width": 1024,
        "height": 1024,
        "nologo": "true",
    }

    headers = {
        "Authorization": f"Bearer {chave}"
    }

    resposta = requests.get(
        url,
        params=parametros,
        headers=headers,
        timeout=180
    )

    if resposta.status_code != 200:

        texto_erro = resposta.text

        if len(texto_erro) > 1500:
            texto_erro = texto_erro[:1500]

        raise RuntimeError(
            f"HTTP {resposta.status_code}: "
            f"{texto_erro}"
        )

    imagem_bytes = resposta.content

    if not imagem_bytes:

        raise RuntimeError(
            "O Pollinations não retornou dados."
        )

    # --------------------------------------------------------
    # Determina extensão
    # --------------------------------------------------------

    content_type = (
        resposta.headers.get(
            "Content-Type",
            ""
        ).lower()
    )

    if "png" in content_type:

        extensao = ".png"

    elif "webp" in content_type:

        extensao = ".webp"

    else:

        extensao = ".jpg"

    # --------------------------------------------------------
    # Salva arquivo
    # --------------------------------------------------------

    pasta = obter_pasta_imagens()

    caminho = (
        pasta /
        f"ultima_imagem{extensao}"
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
# 🖼️ GERAR IMAGEM
# FALLBACK AUTOMÁTICO
# ============================================================

def gerar_imagem(prompt):
    """
    Tenta vários motores do Pollinations.

    Se um motor falhar, tenta automaticamente
    o próximo.
    """

    if not prompt or not prompt.strip():

        return (
            None,
            "❌ O prompt da imagem está vazio."
        )

    chave = obter_chave_pollinations()

    if not chave:

        return (
            None,
            "❌ A chave POLLINATIONS_API_KEY "
            "não foi encontrada nos Secrets."
        )

    erros = []

    # --------------------------------------------------------
    # Tenta cada motor
    # --------------------------------------------------------

    for modelo in MOTORES_IMAGEM:

        try:

            caminho = _gerar_com_pollinations(
                prompt=prompt,
                modelo=modelo
            )

            guardar_ultima_imagem(
                imagem=caminho,
                prompt=prompt,
                caminho=caminho,
                motor=modelo
            )

            return (
                caminho,
                f"🖼️ Imagem gerada pelo motor {modelo}."
            )

        except Exception as erro:

            mensagem = str(erro)

            erros.append(
                f"{modelo}: {mensagem}"
            )

            # Continua para o próximo motor.
            continue

    # --------------------------------------------------------
    # Todos falharam
    # --------------------------------------------------------

    return (
        None,
        "❌ Todos os motores de imagem "
        "do Pollinations falharam.\n\n"
        +
        "\n\n".join(erros)
    )


# ============================================================
# 🖼️ MOSTRAR IMAGEM
# ============================================================

def mostrar_imagem(prompt):
    """
    Gera e mostra a imagem no Streamlit.
    """

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

    # --------------------------------------------------------
    # Mostra imagem
    # --------------------------------------------------------

    st.image(
        imagem,
        caption=(
            "🖼️ Imagem gerada pela "
            "Alex IA Ultra"
        ),
        use_container_width=True
    )

    # --------------------------------------------------------
    # Mostra motor utilizado
    # --------------------------------------------------------

    motor = st.session_state.get(
        "ultimo_motor_imagem"
    )

    if motor:

        st.caption(
            f"🎨 Motor utilizado: {motor}"
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
