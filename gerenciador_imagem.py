# ============================================================
# 🖼️ ALEX IA ULTRA — GERENCIADOR DE IMAGENS
# Criado por Geovani
# ============================================================

import os
import uuid
from pathlib import Path

import requests
import streamlit as st


# ============================================================
# ⚙️ CONFIGURAÇÃO
# ============================================================

# Hugging Face
HF_TOKEN = os.getenv("HF_TOKEN", "")

# Pollinations
POLLINATIONS_API_KEY = os.getenv(
    "POLLINATIONS_API_KEY",
    ""
)

# Modelo usado pelo Hugging Face
HF_MODEL = os.getenv(
    "HF_IMAGE_MODEL",
    "black-forest-labs/FLUX.1-schnell"
)


# ============================================================
# 💾 GUARDAR ÚLTIMA IMAGEM
# ============================================================

def guardar_ultima_imagem(
    imagem,
    prompt,
    caminho=None,
    motor=None
):
    """Guarda a última imagem para análise posterior."""

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
# 📁 PASTA DAS IMAGENS
# ============================================================

def obter_pasta_imagens():

    pasta = Path(
        os.path.join(
            "/tmp",
            "alex_ia_ultra_imagens"
        )
    )

    pasta.mkdir(
        parents=True,
        exist_ok=True
    )

    return pasta


# ============================================================
# 🎨 GERAR COM HUGGING FACE
# ============================================================

def _gerar_com_huggingface(prompt):

    if not HF_TOKEN:

        raise RuntimeError(
            "HF_TOKEN não configurado."
        )

    try:

        from huggingface_hub import InferenceClient

    except Exception as erro:

        raise RuntimeError(
            "O pacote huggingface_hub não está instalado."
        ) from erro

    cliente = InferenceClient(
        provider="auto",
        api_key=HF_TOKEN
    )

    imagem = cliente.text_to_image(
        prompt,
        model=HF_MODEL
    )

    if imagem is None:

        raise RuntimeError(
            "Hugging Face não retornou uma imagem."
        )

    pasta = obter_pasta_imagens()

    caminho = (
        pasta /
        f"imagem_{uuid.uuid4().hex}.png"
    )

    imagem.save(
        str(caminho)
    )

    return str(caminho)


# ============================================================
# 🌸 GERAR COM POLLINATIONS
# ============================================================

def _gerar_com_pollinations(prompt):

    if not POLLINATIONS_API_KEY:

        raise RuntimeError(
            "POLLINATIONS_API_KEY não configurada."
        )

    url = (
        "https://gen.pollinations.ai/image/"
        + requests.utils.quote(
            prompt,
            safe=""
        )
    )

    parametros = {
        "model": "flux",
        "width": 1024,
        "height": 1024,
        "nologo": "true",
    }

    cabecalhos = {
        "Authorization":
            f"Bearer {POLLINATIONS_API_KEY}"
    }

    resposta = requests.get(
        url,
        params=parametros,
        headers=cabecalhos,
        timeout=180
    )

    if resposta.status_code != 200:

        raise RuntimeError(
            f"Pollinations retornou "
            f"HTTP {resposta.status_code}: "
            f"{resposta.text[:500]}"
        )

    if not resposta.content:

        raise RuntimeError(
            "Pollinations não retornou dados."
        )

    pasta = obter_pasta_imagens()

    caminho = (
        pasta /
        f"imagem_{uuid.uuid4().hex}.png"
    )

    with open(
        caminho,
        "wb"
    ) as arquivo:

        arquivo.write(
            resposta.content
        )

    return str(caminho)


# ============================================================
# 🖼️ GERAR IMAGEM
# ============================================================

def gerar_imagem(prompt):

    """
    Sistema automático de geração.

    Ordem:

    1️⃣ Hugging Face
    2️⃣ Pollinations

    Se um motor falhar, o próximo é
    acionado automaticamente.
    """

    if not prompt or not prompt.strip():

        return (
            None,
            "❌ O prompt da imagem está vazio."
        )

    prompt = prompt.strip()

    erros = []


    # ========================================================
    # 1️⃣ HUGGING FACE
    # ========================================================

    try:

        caminho = _gerar_com_huggingface(
            prompt
        )

        guardar_ultima_imagem(
            imagem=caminho,
            prompt=prompt,
            caminho=caminho,
            motor="Hugging Face"
        )

        return (
            caminho,
            "🖼️ Imagem gerada pelo Hugging Face."
        )

    except Exception as erro:

        erros.append(
            "Hugging Face: "
            + str(erro)
        )


    # ========================================================
    # 2️⃣ POLLINATIONS
    # ========================================================

    try:

        caminho = _gerar_com_pollinations(
            prompt
        )

        guardar_ultima_imagem(
            imagem=caminho,
            prompt=prompt,
            caminho=caminho,
            motor="Pollinations"
        )

        return (
            caminho,
            "🖼️ Imagem gerada pelo Pollinations."
        )

    except Exception as erro:

        erros.append(
            "Pollinations: "
            + str(erro)
        )


    # ========================================================
    # ❌ TODOS FALHARAM
    # ========================================================

    return (
        None,
        "❌ Todos os motores de imagem "
        "disponíveis falharam.\n\n"
        + "\n\n".join(erros)
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
            "🖼️ Imagem gerada "
            "pela Alex IA Ultra"
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
