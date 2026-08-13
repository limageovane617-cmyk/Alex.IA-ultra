# ============================================================
# 🖼️ ALEX IA ULTRA — GERENCIADOR DE IMAGENS
# Criada por Geovani
# ============================================================

import io
import os
import time
from pathlib import Path

import streamlit as st
from PIL import Image
from gradio_client import Client

from servicos import criar_cliente_gemini


# ============================================================
# ⚙️ CONFIGURAÇÕES
# ============================================================

# Motor principal atual
SPACE_Z_IMAGE = "mrfakename/Z-Image-Turbo"

# Motor de imagem do Gemini
MODELO_GEMINI_IMAGEM = "gemini-3.1-flash-image"


# ============================================================
# 📁 PASTA TEMPORÁRIA
# ============================================================

def obter_pasta_imagens():

    pasta = (
        Path(
            os.environ.get(
                "TMPDIR",
                "/tmp"
            )
        )
        / "alex_ia_ultra"
        / "imagens"
    )

    pasta.mkdir(
        parents=True,
        exist_ok=True
    )

    return pasta


# ============================================================
# 💾 GUARDAR IMAGEM
# ============================================================

def guardar_imagem(
    imagem,
    prompt,
    motor
):
    """
    Guarda a última imagem gerada
    na sessão da Alex.
    """

    try:

        st.session_state.ultima_imagem = imagem

        st.session_state.ultimo_prompt_imagem = prompt

        st.session_state.ultimo_motor_imagem = motor

        caminho = None

        # ----------------------------------------------------
        # PIL Image
        # ----------------------------------------------------

        if isinstance(
            imagem,
            Image.Image
        ):

            caminho = (
                obter_pasta_imagens()
                / "ultima_imagem.png"
            )

            imagem.save(
                caminho,
                format="PNG"
            )

        # ----------------------------------------------------
        # Caminho de arquivo
        # ----------------------------------------------------

        elif isinstance(
            imagem,
            str
        ):

            if os.path.exists(imagem):

                caminho = imagem

                try:

                    imagem_pil = Image.open(
                        imagem
                    )

                    st.session_state.ultima_imagem = (
                        imagem_pil
                    )

                except Exception:
                    pass

        # ----------------------------------------------------
        # Objeto com .path
        # ----------------------------------------------------

        elif hasattr(
            imagem,
            "path"
        ):

            caminho = imagem.path

        st.session_state.ultima_imagem_caminho = (
            str(caminho)
            if caminho
            else None
        )

        return True

    except Exception:

        st.session_state.ultima_imagem = imagem

        st.session_state.ultimo_prompt_imagem = prompt

        st.session_state.ultimo_motor_imagem = motor

        st.session_state.ultima_imagem_caminho = None

        return False


# ============================================================
# 🥇 MOTOR 1 — Z IMAGE TURBO
# ============================================================

def gerar_z_image(
    prompt
):
    """
    Tenta gerar uma imagem pelo
    Z-Image-Turbo.
    """

    try:

        cliente = Client(
            SPACE_Z_IMAGE
        )

        resultado = cliente.predict(
            prompt.strip(),
            1024,
            1024,
            9,
            42,
            True,
            api_name="/generate_image"
        )

        if isinstance(
            resultado,
            tuple
        ):

            imagem = resultado[0]

        else:

            imagem = resultado

        if not imagem:

            raise RuntimeError(
                "O Z-Image-Turbo não retornou imagem."
            )

        return (
            imagem,
            None
        )

    except Exception as erro:

        return (
            None,
            str(erro)
        )


# ============================================================
# 🥈 MOTOR 2 — GEMINI IMAGE
# ============================================================

def gerar_gemini_image(
    prompt
):
    """
    Tenta gerar imagem pelo Gemini.
    """

    try:

        cliente = criar_cliente_gemini()

        if cliente is None:

            return (
                None,
                "Cliente Gemini indisponível."
            )

        resposta = cliente.models.generate_content(
            model=MODELO_GEMINI_IMAGEM,
            contents=prompt.strip(),
            config={
                "response_modalities": [
                    "IMAGE"
                ]
            }
        )

        if not resposta:

            return (
                None,
                "Gemini não retornou resposta."
            )

        candidatos = getattr(
            resposta,
            "candidates",
            []
        )

        for candidato in candidatos:

            conteudo = getattr(
                candidato,
                "content",
                None
            )

            if not conteudo:
                continue

            partes = getattr(
                conteudo,
                "parts",
                []
            )

            for parte in partes:

                dados = getattr(
                    parte,
                    "inline_data",
                    None
                )

                if not dados:
                    continue

                bytes_imagem = getattr(
                    dados,
                    "data",
                    None
                )

                if not bytes_imagem:
                    continue

                imagem = Image.open(
                    io.BytesIO(
                        bytes_imagem
                    )
                )

                return (
                    imagem,
                    None
                )

        return (
            None,
            "Gemini terminou sem retornar imagem."
        )

    except Exception as erro:

        return (
            None,
            str(erro)
        )


# ============================================================
# 🔎 DETECTAR ERRO DE COTA
# ============================================================

def erro_de_cota(
    mensagem
):
    """
    Detecta erros conhecidos de limite/quota.
    """

    if not mensagem:
        return False

    texto = str(
        mensagem
    ).lower()

    palavras = (
        "quota",
        "zerogpu",
        "resource_exhausted",
        "rate limit",
        "rate_limit",
        "too many requests",
        "exceeded",
        "limit exceeded",
        "429",
    )

    return any(
        palavra in texto
        for palavra in palavras
    )


# ============================================================
# 🎯 GERADOR AUTOMÁTICO
# ============================================================

def gerar_imagem_automatica(
    prompt
):
    """
    Tenta vários motores automaticamente.

    Ordem:

    1. Z-Image-Turbo
    2. Gemini Image
    """

    if not prompt or not prompt.strip():

        return (
            None,
            "❌ O prompt da imagem está vazio.",
            None
        )

    motores = [
        (
            "Z-Image-Turbo",
            gerar_z_image
        ),
        (
            "Gemini Image",
            gerar_gemini_image
        ),
    ]

    erros = []

    for nome_motor, funcao in motores:

        st.info(
            f"🎨 Tentando motor: {nome_motor}"
        )

        imagem, erro = funcao(
            prompt
        )

        if imagem is not None:

            guardar_imagem(
                imagem,
                prompt,
                nome_motor
            )

            return (
                imagem,
                None,
                nome_motor
            )

        erros.append(
            f"{nome_motor}: {erro}"
        )

        # ----------------------------------------------------
        # Se falhou, tenta automaticamente o próximo.
        # ----------------------------------------------------

        continue

    mensagem = (
        "❌ Todos os motores de imagem "
        "disponíveis falharam.\n\n"
        + "\n".join(erros)
    )

    return (
        None,
        mensagem,
        None
    )


# ============================================================
# 🖼️ MOSTRAR IMAGEM
# ============================================================

def mostrar_imagem_automatica(
    prompt
):
    """
    Gera imagem usando fallback automático.
    """

    with st.spinner(
        "🎨 Alex IA está escolhendo "
        "o melhor motor de imagem..."
    ):

        imagem, erro, motor = (
            gerar_imagem_automatica(
                prompt
            )
        )

    if erro:

        st.error(
            erro
        )

        return False

    st.image(
        imagem,
        caption=(
            "🖼️ Imagem gerada pela Alex IA Ultra "
            f"• Motor: {motor}"
        ),
        use_container_width=True
    )

    st.success(
        f"✅ Imagem criada usando {motor}."
    )

    return True
