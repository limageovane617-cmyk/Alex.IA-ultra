# ============================================================
# 🎬 TESTE DE VÍDEO — FAL.AI + VIDU
# ============================================================

import os
from pathlib import Path

import requests
import streamlit as st


# ============================================================
# CONFIGURAÇÃO
# ============================================================

MODELO = "fal-ai/vidu/image-to-video"

PASTA = Path("/tmp/alex_ia_ultra_videos")
PASTA.mkdir(parents=True, exist_ok=True)


# ============================================================
# API KEY
# ============================================================

def obter_api_key():

    try:
        chave = st.secrets.get("FAL_KEY", "")
    except Exception:
        chave = ""

    if not chave:
        chave = os.environ.get("FAL_KEY", "")

    return str(chave).strip()


# ============================================================
# GERAR VÍDEO
# ============================================================

def gerar_video(
    arquivo,
    prompt,
    duracao,
    resolucao,
    movimento
):

    chave = obter_api_key()

    if not chave:
        raise RuntimeError(
            "FAL_KEY não foi encontrada nos Secrets."
        )

    os.environ["FAL_KEY"] = chave

    # --------------------------------------------------------
    # Importar fal-client
    # --------------------------------------------------------

    try:

        import fal_client

    except Exception as erro:

        raise RuntimeError(
            "A biblioteca fal-client não está instalada.\n\n"
            "Adicione ao requirements.txt:\n"
            "fal-client\n\n"
            f"Detalhes: {erro}"
        )

    # --------------------------------------------------------
    # SALVAR UPLOADED FILE
    # --------------------------------------------------------

    try:

        extensao = Path(
            arquivo.name
        ).suffix.lower()

        if extensao not in [
            ".png",
            ".jpg",
            ".jpeg",
            ".webp"
        ]:

            extensao = ".png"

        caminho_imagem = (
            PASTA / f"imagem_entrada{extensao}"
        )

        with open(
            caminho_imagem,
            "wb"
        ) as f:

            f.write(
                arquivo.getbuffer()
            )

    except Exception as erro:

        raise RuntimeError(
            "Não foi possível salvar a imagem "
            "temporariamente:\n\n"
            f"{erro}"
        )

    # --------------------------------------------------------
    # UPLOAD PARA FAL.AI
    # --------------------------------------------------------

    try:

        imagem_url = fal_client.upload_file(
            str(caminho_imagem)
        )

    except Exception as erro:

        raise RuntimeError(
            "Não foi possível enviar a imagem "
            "para o fal.ai:\n\n"
            f"{erro}"
        )

    # --------------------------------------------------------
    # PROMPT
    # --------------------------------------------------------

    prompt_final = f"""
{prompt}

Movimento da câmera:
{movimento}

CONTINUIDADE DO PERSONAGEM:

Manter o personagem principal consistente
durante todo o vídeo.

Preservar:
- rosto
- cabelo
- roupa
- acessórios
- aparência
- proporções
- identidade visual

Se a câmera sair do personagem e depois
voltar para ele, ele deve continuar sendo
exatamente o mesmo personagem.

Evitar:
- troca de rosto
- troca de roupa
- deformações
- mudanças de identidade
- alterações bruscas de aparência

Movimentos naturais e cinematográficos.
"""

    # --------------------------------------------------------
    # DADOS
    # --------------------------------------------------------

    dados = {
        "prompt": prompt_final.strip(),
        "image_url": imagem_url,
        "duration": int(duracao),
        "resolution": resolucao
    }

    # --------------------------------------------------------
    # GERAR
    # --------------------------------------------------------

    try:

        resultado = fal_client.subscribe(
            MODELO,
            arguments=dados
        )

    except Exception as erro:

        raise RuntimeError(
            "Erro na geração pelo fal.ai:\n\n"
            f"{erro}"
        )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    if not isinstance(
        resultado,
        dict
    ):

        raise RuntimeError(
            "Resposta inesperada do fal.ai:\n\n"
            f"{resultado}"
        )

    video = resultado.get(
        "video"
    )

    if not video:

        raise RuntimeError(
            "O fal.ai terminou a solicitação, "
            "mas não retornou o vídeo.\n\n"
            f"Resposta:\n{resultado}"
        )

    video_url = video.get(
        "url"
    )

    if not video_url:

        raise RuntimeError(
            "A URL do vídeo não foi encontrada."
        )

    # --------------------------------------------------------
    # BAIXAR VÍDEO
    # --------------------------------------------------------

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
    # SALVAR
    # --------------------------------------------------------

    caminho_video = (
        PASTA / "video_vidu.mp4"
    )

    caminho_video.write_bytes(
        resposta.content
    )

    return str(caminho_video)


# ============================================================
# INTERFACE
# ============================================================

st.set_page_config(
    page_title="Teste Vidu — fal.ai",
    page_icon="🎬"
)

st.title(
    "🎬 TESTE DE VÍDEO — FAL.AI"
)

st.write(
    "Teste isolado do Vidu Image-to-Video."
)

st.info(
    "🎥 Motor: Vidu\n"
    "🏢 Provedor: fal.ai"
)


# ============================================================
# IMAGEM
# ============================================================

arquivo = st.file_uploader(
    "🖼️ Escolha uma imagem:",
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
# PROMPT
# ============================================================

prompt = st.text_area(
    "📝 O que deve acontecer no vídeo?",
    value=(
        "Um personagem futurista caminhando "
        "lentamente por uma cidade cyberpunk "
        "à noite, com luzes neon refletindo "
        "no chão molhado. Movimento natural "
        "e aparência cinematográfica."
    ),
    height=160
)


# ============================================================
# CÂMERA
# ============================================================

movimento = st.selectbox(
    "🎥 Movimento da câmera:",
    [
        "Câmera acompanha o personagem suavemente.",
        "Travelling para frente.",
        "Travelling lateral.",
        "Zoom cinematográfico lento.",
        "Câmera se afasta e depois retorna ao personagem.",
        "Movimento circular ao redor do personagem.",
        "Câmera estável."
    ]
)


# ============================================================
# DURAÇÃO
# ============================================================

duracao = st.selectbox(
    "⏱️ Duração:",
    [4, 5, 6, 7, 8]
)


# ============================================================
# RESOLUÇÃO
# ============================================================

resolucao = st.selectbox(
    "📺 Resolução:",
    [
        "720p",
        "1080p"
    ]
)


# ============================================================
# GERAR
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
            "⚠️ Digite o que deve acontecer."
        )

    else:

        try:

            with st.spinner(
                "🎬 Gerando vídeo..."
            ):

                caminho = gerar_video(
                    arquivo,
                    prompt,
                    duracao,
                    resolucao,
                    movimento
                )

            st.success(
                "🎉 Vídeo gerado com sucesso!"
            )

            st.video(
                caminho
            )

            with open(
                caminho,
                "rb"
            ) as arquivo_video:

                st.download_button(
                    "📥 Baixar vídeo",
                    data=arquivo_video,
                    file_name="video_vidu.mp4",
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
