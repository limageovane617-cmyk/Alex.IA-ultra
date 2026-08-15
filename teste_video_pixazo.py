# ============================================================
# 🎬 ALEX IA ULTRA — TESTE DE VÍDEO
# FAL.AI + VIDU IMAGE-TO-VIDEO
# Criado por Geovani
# ============================================================

import os
from pathlib import Path

import streamlit as st


# ============================================================
# ⚙️ CONFIGURAÇÃO
# ============================================================

MODELO = "fal-ai/vidu/image-to-video"

DURACAO_PADRAO = 4
RESOLUCAO_PADRAO = "720p"


# ============================================================
# 🔐 API KEY
# ============================================================

def obter_api_key():

    try:
        chave = st.secrets.get(
            "FAL_KEY",
            ""
        )
    except Exception:
        chave = ""

    if not chave:

        chave = os.environ.get(
            "FAL_KEY",
            ""
        )

    return str(chave).strip()


# ============================================================
# 📁 PASTA
# ============================================================

def obter_pasta():

    pasta = Path(
        "/tmp/alex_ia_ultra_videos"
    )

    pasta.mkdir(
        parents=True,
        exist_ok=True
    )

    return pasta


# ============================================================
# 📦 INSTALAR / IMPORTAR FAL
# ============================================================

def obter_fal():

    try:

        from fal_client import (
            upload_file,
            subscribe
        )

        return upload_file, subscribe

    except Exception as erro:

        raise RuntimeError(
            "A biblioteca fal-client não está instalada.\n\n"
            "Adicione ao requirements.txt:\n\n"
            "fal-client\n\n"
            f"Detalhes: {erro}"
        )


# ============================================================
# 🎬 GERAR VÍDEO
# ============================================================

def gerar_video(
    arquivo,
    prompt,
    duracao,
    resolucao,
    movimento
):

    api_key = obter_api_key()

    if not api_key:

        raise RuntimeError(
            "FAL_KEY não foi encontrada "
            "nos Secrets do Streamlit."
        )

    # --------------------------------------------------------
    # Configurar variável para o fal-client
    # --------------------------------------------------------

    os.environ["FAL_KEY"] = api_key

    upload_file, subscribe = obter_fal()

    # --------------------------------------------------------
    # Upload automático da imagem
    # --------------------------------------------------------

    try:

        imagem_url = upload_file(
            arquivo
        )

    except Exception as erro:

        raise RuntimeError(
            "Não foi possível enviar a imagem "
            "para o fal.ai:\n\n"
            f"{erro}"
        )

    # --------------------------------------------------------
    # Prompt final
    # --------------------------------------------------------

    prompt_final = f"""
{prompt}

MOVIMENTO DE CÂMERA:
{movimento}

CONTINUIDADE DO PERSONAGEM:
Manter o personagem principal como referência visual
durante toda a cena.

Manter consistentes:
- rosto
- cabelo
- aparência
- roupa
- acessórios
- proporções corporais
- identidade visual

Se a câmera se afastar do personagem e depois retornar,
o personagem deve continuar sendo o mesmo personagem,
sem trocar rosto, roupa, cabelo ou características.

Movimentos naturais e cinematográficos.
Evitar deformações.
Evitar mudanças bruscas de identidade.
"""

    # --------------------------------------------------------
    # Dados
    # --------------------------------------------------------

    dados = {
        "prompt": prompt_final.strip(),

        "image_url": imagem_url,

        "duration": int(
            duracao
        ),

        "resolution": resolucao,

        "movement_amplitude": "auto",

        "audio": False,
    }

    # --------------------------------------------------------
    # Gerar
    # --------------------------------------------------------

    try:

        resultado = subscribe(
            MODELO,
            arguments=dados
        )

    except Exception as erro:

        raise RuntimeError(
            "Erro na geração pelo fal.ai:\n\n"
            f"{erro}"
        )

    # --------------------------------------------------------
    # Ler resultado
    # --------------------------------------------------------

    if not isinstance(
        resultado,
        dict
    ):

        raise RuntimeError(
            "O fal.ai retornou uma resposta "
            "em formato inesperado:\n\n"
            f"{resultado}"
        )

    video = resultado.get(
        "video"
    )

    if not video:

        raise RuntimeError(
            "O fal.ai terminou a geração, "
            "mas não retornou o vídeo.\n\n"
            f"Resposta:\n{resultado}"
        )

    video_url = video.get(
        "url"
    )

    if not video_url:

        raise RuntimeError(
            "A URL do vídeo não foi encontrada.\n\n"
            f"Resposta:\n{resultado}"
        )

    # --------------------------------------------------------
    # Baixar vídeo
    # --------------------------------------------------------

    import requests

    try:

        resposta = requests.get(
            video_url,
            timeout=180
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro ao baixar o vídeo:\n{erro}"
        )

    if resposta.status_code != 200:

        raise RuntimeError(
            "Falha ao baixar o vídeo.\n"
            f"HTTP {resposta.status_code}"
        )

    # --------------------------------------------------------
    # Salvar
    # --------------------------------------------------------

    caminho = (
        obter_pasta()
        / "video_fal_vidu.mp4"
    )

    try:

        caminho.write_bytes(
            resposta.content
        )

    except Exception as erro:

        raise RuntimeError(
            f"Não foi possível salvar o vídeo:\n{erro}"
        )

    return str(caminho)


# ============================================================
# 🖥️ INTERFACE
# ============================================================

st.set_page_config(
    page_title="Teste Vidu — fal.ai",
    page_icon="🎬",
    layout="centered"
)


# ============================================================
# 🎬 CABEÇALHO
# ============================================================

st.title(
    "🎬 TESTE DE VÍDEO — FAL.AI"
)

st.write(
    "Teste isolado de geração de vídeo "
    "usando Vidu Image-to-Video."
)

st.info(
    "🎥 Motor: Vidu Image-to-Video\n\n"
    "🏢 Provedor: fal.ai\n\n"
    f"⏱️ Duração inicial: {DURACAO_PADRAO} segundos\n\n"
    f"📺 Resolução: {RESOLUCAO_PADRAO}"
)


# ============================================================
# 🖼️ IMAGEM
# ============================================================

st.subheader(
    "🖼️ Imagem inicial"
)

arquivo = st.file_uploader(
    "Escolha uma imagem do seu celular:",
    type=[
        "png",
        "jpg",
        "jpeg",
        "webp"
    ]
)

if arquivo:

    st.image(
        arquivo,
        caption="Imagem selecionada",
        use_container_width=True
    )


# ============================================================
# 📝 PROMPT
# ============================================================

st.subheader(
    "📝 Descrição da cena"
)

prompt = st.text_area(
    "O que deve acontecer?",
    value=(
        "Um personagem futurista caminha "
        "lentamente por uma cidade cyberpunk "
        "durante a noite. "
        "As luzes neon refletem no chão molhado. "
        "A cena possui aparência cinematográfica "
        "e realista."
    ),
    height=180
)


# ============================================================
# 🎥 CÂMERA
# ============================================================

st.subheader(
    "🎥 Movimento da câmera"
)

movimento = st.selectbox(
    "Escolha o movimento:",
    [
        "Câmera acompanha o personagem suavemente.",
        "Travelling cinematográfico para frente.",
        "Travelling lateral acompanhando o personagem.",
        "Zoom cinematográfico lento.",
        "Câmera se afasta lentamente e depois retorna ao personagem.",
        "Movimento circular suave ao redor do personagem.",
        "Plano cinematográfico estável."
    ]
)


# ============================================================
# ⏱️ DURAÇÃO
# ============================================================

duracao = st.selectbox(
    "⏱️ Duração:",
    [
        4,
        5,
        6,
        7,
        8
    ],
    index=0
)


# ============================================================
# 📺 RESOLUÇÃO
# ============================================================

resolucao = st.selectbox(
    "📺 Resolução:",
    [
        "720p",
        "1080p"
    ],
    index=0
)


# ============================================================
# 🎬 BOTÃO
# ============================================================

if st.button(
    "🎬 GERAR VÍDEO",
    type="primary",
    use_container_width=True
):

    if arquivo is None:

        st.warning(
            "⚠️ Escolha uma imagem primeiro."
        )

    elif not prompt.strip():

        st.warning(
            "⚠️ Digite uma descrição para o vídeo."
        )

    else:

        try:

            with st.spinner(
                "📤 Enviando imagem..."
            ):

                caminho = gerar_video(
                    arquivo=arquivo,
                    prompt=prompt,
                    duracao=duracao,
                    resolucao=resolucao,
                    movimento=movimento
                )

            st.success(
                "🎉 Vídeo gerado com sucesso!"
            )

            st.video(
                caminho
            )

            st.caption(
                "🎥 Motor utilizado: "
                "fal.ai / Vidu"
            )

            st.download_button(
                label="📥 Baixar vídeo",
                data=Path(
                    caminho
                ).read_bytes(),
                file_name=(
                    "video_fal_vidu.mp4"
                ),
                mime="video/mp4",
                use_container_width=True
            )

        except Exception as erro:

            st.error(
                "❌ Erro ao gerar vídeo:"
            )

            st.code(
                str(erro)
)
