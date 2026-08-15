# ============================================================
# 🎬 TESTE DE VÍDEO — HUGGING FACE
# IMAGE-TO-VIDEO
# Criado por Geovani
# ============================================================

import os
from pathlib import Path

import streamlit as st


# ============================================================
# ⚙️ CONFIGURAÇÃO
# ============================================================

MODELO_VIDEO = "Wan-AI/Wan2.1-I2V-14B-480P"

PASTA_VIDEOS = Path(
    "/tmp/alex_ia_ultra_videos"
)

PASTA_VIDEOS.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 🔐 TOKEN HUGGING FACE
# ============================================================

def obter_token():

    try:
        token = st.secrets.get(
            "HF_TOKEN",
            ""
        )
    except Exception:
        token = ""

    if not token:
        token = os.environ.get(
            "HF_TOKEN",
            ""
        )

    return str(token).strip()


# ============================================================
# 🎬 GERAR VÍDEO
# ============================================================

def gerar_video(
    imagem,
    prompt
):

    token = obter_token()

    if not token:

        raise RuntimeError(
            "HF_TOKEN não foi encontrado "
            "nos Secrets do Streamlit."
        )

    # --------------------------------------------------------
    # Importar Hugging Face
    # --------------------------------------------------------

    try:

        from huggingface_hub import InferenceClient

    except Exception as erro:

        raise RuntimeError(
            "A biblioteca huggingface_hub "
            "não está instalada.\n\n"
            "Adicione ao requirements.txt:\n\n"
            "huggingface_hub\n\n"
            f"Detalhes: {erro}"
        )

    # --------------------------------------------------------
    # Criar cliente
    # --------------------------------------------------------

    try:

        cliente = InferenceClient(
            api_key=token
        )

    except Exception as erro:

        raise RuntimeError(
            "Não foi possível iniciar "
            f"o Hugging Face:\n{erro}"
        )

    # --------------------------------------------------------
    # Salvar imagem temporariamente
    # --------------------------------------------------------

    caminho_imagem = (
        PASTA_VIDEOS
        / "imagem_entrada.png"
    )

    try:

        dados_imagem = imagem.getvalue()

        caminho_imagem.write_bytes(
            dados_imagem
        )

    except Exception as erro:

        raise RuntimeError(
            "Não foi possível preparar "
            f"a imagem:\n{erro}"
        )

    # --------------------------------------------------------
    # Gerar vídeo
    # --------------------------------------------------------

    try:

        resultado = cliente.image_to_video(
            image=str(caminho_imagem),
            prompt=prompt.strip(),
            model=MODELO_VIDEO
        )

    except Exception as erro:

        raise RuntimeError(
            "Erro na geração de vídeo "
            "pelo Hugging Face:\n\n"
            f"{erro}"
        )

    # --------------------------------------------------------
    # Verificar resultado
    # --------------------------------------------------------

    if resultado is None:

        raise RuntimeError(
            "O Hugging Face não retornou "
            "um vídeo."
        )

    # --------------------------------------------------------
    # Salvar vídeo
    # --------------------------------------------------------

    caminho_video = (
        PASTA_VIDEOS
        / "video_huggingface.mp4"
    )

    try:

        if isinstance(
            resultado,
            bytes
        ):

            caminho_video.write_bytes(
                resultado
            )

        elif hasattr(
            resultado,
            "read"
        ):

            conteudo = resultado.read()

            caminho_video.write_bytes(
                conteudo
            )

        elif isinstance(
            resultado,
            str
        ):

            # Caso a API retorne uma URL
            import requests

            resposta = requests.get(
                resultado,
                timeout=180
            )

            if resposta.status_code != 200:

                raise RuntimeError(
                    "Não foi possível baixar "
                    "o vídeo."
                )

            caminho_video.write_bytes(
                resposta.content
            )

        else:

            raise RuntimeError(
                "Formato de vídeo retornado "
                "não reconhecido:\n"
                f"{type(resultado)}"
            )

    except Exception as erro:

        raise RuntimeError(
            "Não foi possível salvar "
            f"o vídeo:\n{erro}"
        )

    return str(caminho_video)


# ============================================================
# 🖥️ INTERFACE
# ============================================================

st.set_page_config(
    page_title="Teste Vídeo Hugging Face",
    page_icon="🎬"
)


st.title(
    "🎬 TESTE DE VÍDEO"
)

st.subheader(
    "Hugging Face — Image to Video"
)

st.info(
    f"🎥 Modelo: {MODELO_VIDEO}"
)


# ============================================================
# 🖼️ IMAGEM
# ============================================================

imagem = st.file_uploader(
    "🖼️ Escolha uma imagem:",
    type=[
        "png",
        "jpg",
        "jpeg",
        "webp"
    ]
)

if imagem:

    st.image(
        imagem,
        caption="Imagem de entrada",
        use_container_width=True
    )


# ============================================================
# 📝 PROMPT
# ============================================================

prompt = st.text_area(
    "📝 Descreva o movimento:",
    value=(
        "O personagem começa a caminhar "
        "lentamente para frente. "
        "A câmera acompanha suavemente "
        "o personagem em um movimento "
        "cinematográfico. "
        "Manter o mesmo rosto, cabelo, "
        "roupa e aparência durante toda "
        "a cena."
    ),
    height=180
)


# ============================================================
# 🎬 GERAR
# ============================================================

if st.button(
    "🎬 GERAR VÍDEO",
    type="primary",
    use_container_width=True
):

    if imagem is None:

        st.warning(
            "⚠️ Escolha uma imagem primeiro."
        )

    elif not prompt.strip():

        st.warning(
            "⚠️ Digite um prompt."
        )

    else:

        try:

            with st.spinner(
                "🎬 Gerando vídeo... "
                "Isso pode demorar alguns minutos."
            ):

                caminho = gerar_video(
                    imagem,
                    prompt
                )

            st.success(
                "🎉 Vídeo gerado!"
            )

            st.video(
                caminho
            )

            st.caption(
                "🎥 Motor: Hugging Face / "
                "Wan2.1 I2V"
            )

        except Exception as erro:

            st.error(
                "❌ Erro ao gerar vídeo:"
            )

            st.code(
                str(erro)
            )
