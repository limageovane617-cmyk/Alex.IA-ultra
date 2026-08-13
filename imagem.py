# ============================================================
# 🖼️ ALEX IA ULTRA — GERENCIADOR DE IMAGENS
# Pollinations + fallback Gemini
# Criado por Geovani
# ============================================================

import os
from pathlib import Path
from urllib.parse import quote

import requests
import streamlit as st


# ============================================================
# ⚙️ CONFIGURAÇÃO
# ============================================================

POLLINATIONS_URL = "https://gen.pollinations.ai"

# A Alex tenta automaticamente os motores nesta ordem.
MOTORES_IMAGEM = [
    "flux",
    "zimage",
    "qwen-image",
    "seedream",
    "gptimage",
    "nanobanana",
]


# ============================================================
# 🔐 CHAVE DO POLLINATIONS
# ============================================================

def obter_chave_pollinations():

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
# 🎨 GERAR COM POLLINATIONS
# ============================================================

def _gerar_com_pollinations(
    prompt,
    modelo
):

    chave = obter_chave_pollinations()

    if not chave:

        raise RuntimeError(
            "POLLINATIONS_API_KEY não encontrada "
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
        "Authorization": f"Bearer {chave}",
        "Accept": "image/*",
    }

    resposta = requests.get(
        url,
        params=parametros,
        headers=headers,
        timeout=180,
    )

    if resposta.status_code != 200:

        texto = resposta.text[:1500]

        raise RuntimeError(
            f"HTTP {resposta.status_code}: {texto}"
        )

    if not resposta.content:

        raise RuntimeError(
            "O Pollinations não retornou "
            "nenhuma imagem."
        )

    content_type = (
        resposta.headers
        .get("Content-Type", "")
        .lower()
    )

    if "png" in content_type:

        extensao = ".png"

    elif "webp" in content_type:

        extensao = ".webp"

    else:

        extensao = ".jpg"

    caminho = (
        obter_pasta_imagens()
        / f"ultima_imagem{extensao}"
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
# 🤖 FALLBACK GEMINI
# ============================================================

def _gerar_com_gemini(prompt):

    try:

        from google.genai import types

        from servicos import (
            criar_cliente_gemini
        )

        cliente = criar_cliente_gemini()

        if cliente is None:

            raise RuntimeError(
                "Cliente Gemini indisponível."
            )

        modelos_gemini = [
            "gemini-3.1-flash-image",
            "gemini-2.5-flash-image",
        ]

        erros = []

        for modelo in modelos_gemini:

            try:

                resposta = (
                    cliente.models.generate_content(
                        model=modelo,
                        contents=prompt.strip(),
                        config=(
                            types.GenerateContentConfig(
                                response_modalities=[
                                    "TEXT",
                                    "IMAGE"
                                ]
                            )
                        ),
                    )
                )

                candidatos = (
                    getattr(
                        resposta,
                        "candidates",
                        None
                    )
                    or []
                )

                for candidato in candidatos:

                    conteudo = getattr(
                        candidato,
                        "content",
                        None
                    )

                    if not conteudo:
                        continue

                    partes = (
                        getattr(
                            conteudo,
                            "parts",
                            None
                        )
                        or []
                    )

                    for parte in partes:

                        dados = getattr(
                            parte,
                            "inline_data",
                            None
                        )

                        if dados is None:
                            continue

                        imagem_bytes = getattr(
                            dados,
                            "data",
                            None
                        )

                        if not imagem_bytes:
                            continue

                        caminho = (
                            obter_pasta_imagens()
                            / "ultima_imagem_gemini.png"
                        )

                        with open(
                            caminho,
                            "wb"
                        ) as arquivo:

                            arquivo.write(
                                imagem_bytes
                            )

                        return str(caminho)

                erros.append(
                    f"{modelo}: "
                    "não retornou imagem."
                )

            except Exception as erro:

                erros.append(
                    f"{modelo}: {erro}"
                )

        raise RuntimeError(
            " | ".join(erros)
        )

    except Exception as erro:

        raise RuntimeError(
            str(erro)
        )


# ============================================================
# 🖼️ GERADOR AUTOMÁTICO
# ============================================================

def gerar_imagem(prompt):

    if not prompt or not prompt.strip():

        return (
            None,
            "❌ O prompt da imagem está vazio."
        )

    erros = []

    # ========================================================
    # 🌸 POLLINATIONS
    # ========================================================

    chave = obter_chave_pollinations()

    if chave:

        for modelo in MOTORES_IMAGEM:

            try:

                caminho = (
                    _gerar_com_pollinations(
                        prompt=prompt,
                        modelo=modelo
                    )
                )

                guardar_ultima_imagem(
                    imagem=caminho,
                    prompt=prompt,
                    caminho=caminho,
                    motor=(
                        f"Pollinations / "
                        f"{modelo}"
                    ),
                )

                return (
                    caminho,
                    (
                        "🖼️ Imagem gerada pelo "
                        f"Pollinations usando {modelo}."
                    )
                )

            except Exception as erro:

                erros.append(
                    f"Pollinations / "
                    f"{modelo}: {erro}"
                )

                continue

    else:

        erros.append(
            "Pollinations: "
            "POLLINATIONS_API_KEY não configurada."
        )

    # ========================================================
    # 🤖 GEMINI — ÚLTIMO RECURSO
    # ========================================================

    try:

        caminho = _gerar_com_gemini(
            prompt
        )

        guardar_ultima_imagem(
            imagem=caminho,
            prompt=prompt,
            caminho=caminho,
            motor="Gemini (fallback)",
        )

        return (
            caminho,
            "🖼️ Imagem gerada pelo Gemini."
        )

    except Exception as erro:

        erros.append(
            f"Gemini: {erro}"
        )

    # ========================================================
    # ❌ TODOS FALHARAM
    # ========================================================

    return (
        None,
        (
            "❌ Todos os motores de imagem "
            "disponíveis falharam.\n\n"
            + "\n\n".join(erros)
        )
    )


# ============================================================
# 🖼️ MOSTRAR IMAGEM
# ============================================================

def mostrar_imagem(prompt):

    with st.spinner(
        "🎨 Alex IA está criando sua imagem..."
    ):

        imagem, mensagem = (
            gerar_imagem(prompt)
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
