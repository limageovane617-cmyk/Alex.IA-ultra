# ============================================================
# 🎬 ALEX IA ULTRA — SISTEMA DE VÍDEO
# Criada por Geovani
# ============================================================

import streamlit as st


# Configurações cinematográficas disponíveis
CAMERAS = [
    "Sony FX5",
    "Sony FX6",
    "Canon EOS C80",
    "ARRI Alexa Mini LF"
]


def preparar_prompt_video(
    descricao,
    camera="ARRI Alexa Mini LF",
    proporcao="16:9",
    duracao=8
):
    """
    Prepara um prompt cinematográfico para geração de vídeo.
    """

    if not descricao or not descricao.strip():
        return None

    if camera not in CAMERAS:
        camera = "ARRI Alexa Mini LF"

    prompt = f"""
Crie um vídeo cinematográfico baseado na seguinte descrição:

{descricao.strip()}

Configurações cinematográficas:

Câmera:
{camera}

Proporção:
{proporcao}

Duração aproximada:
{duracao} segundos

Mantenha consistência visual dos personagens,
ambiente, roupas e elementos importantes da cena.

Não altere características importantes do personagem
sem uma instrução explícita do usuário.

Estilo:
cinematográfico, detalhado e visualmente coerente.
"""

    return prompt.strip()


def gerar_video(
    descricao,
    camera="ARRI Alexa Mini LF",
    proporcao="16:9",
    duracao=8
):
    """
    Ponto de entrada para o sistema de geração de vídeo.

    A integração com o modelo de vídeo será adicionada
    depois que definirmos o provedor e o modelo.
    """

    prompt = preparar_prompt_video(
        descricao,
        camera,
        proporcao,
        duracao
    )

    if not prompt:
        return None, "A descrição do vídeo está vazia."

    return None, (
        "O módulo de vídeo está preparado. "
        "A integração com o gerador de vídeo "
        "será conectada na próxima etapa."
    )


def mostrar_configuracao_video():
    """
    Mostra as opções cinematográficas no Streamlit.
    """

    camera = st.selectbox(
        "🎥 Câmera cinematográfica",
        CAMERAS
    )

    proporcao = st.selectbox(
        "📐 Proporção",
        ["16:9", "9:16", "1:1"]
    )

    duracao = st.slider(
        "⏱️ Duração aproximada",
        min_value=4,
        max_value=30,
        value=8,
        step=1
    )

    return camera, proporcao, duracao
