# ============================================================
# 🎬 TESTE DE VÍDEO — FAL.AI + VIDU Q3
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

MODELO = "fal-ai/vidu/q3/image-to-video"

PASTA = Path("/tmp/alex_ia_ultra_videos")
PASTA.mkdir(parents=True, exist_ok=True)


# ============================================================
# 🔐 API KEY
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
# 🖼️ CONVERTER IMAGEM PARA BASE64
# ============================================================

def imagem_para_data_uri(arquivo):

    try:

        dados = arquivo.getvalue()

        if not dados:
            raise RuntimeError(
                "O arquivo de imagem está vazio."
            )

        nome = arquivo.name.lower()

        if nome.endswith(".png"):
            mime = "image/png"

        elif nome.endswith(".webp"):
            mime = "image/webp"

        elif nome.endswith(".jpg") or nome.endswith(".jpeg"):
            mime = "image/jpeg"

        else:
            mime = arquivo.type or "image/jpeg"

        encoded = base64.b64encode(
            dados
        ).decode("utf-8")

        return (
            f"data:{mime};base64,{encoded}"
        )

    except Exception as erro:

        raise RuntimeError(
            "Não foi possível preparar "
            f"a imagem: {erro}"
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
    # Converter imagem diretamente para Base64
    # --------------------------------------------------------

    imagem_data_uri = imagem_para_data_uri(
        arquivo
    )

    # --------------------------------------------------------
    # Prompt cinematográfico
    # --------------------------------------------------------

    prompt_final = f"""
{prompt}

Movimento de câmera:
{movimento}

CONTINUIDADE DO PERSONAGEM:

Manter o personagem principal consistente
durante toda a cena.

Preservar:
- rosto
- cabelo
- roupa
- acessórios
- aparência
- proporções corporais
- identidade visual

Se a câmera sair do personagem e depois
voltar para ele, manter exatamente o mesmo
personagem.

Não trocar o rosto.
Não trocar a roupa.
Não alterar cabelo ou aparência.
Evitar deformações.
Evitar mudanças de identidade.

Movimentos naturais e cinematográficos.
"""

    # --------------------------------------------------------
    # Dados da API
    # --------------------------------------------------------

    dados = {
        "prompt": prompt_final.strip(),

        "image_url": imagem_data_uri,

        "duration": int(duracao),

        "resolution": resolucao,

        "audio": False,

        "movement_amplitude": "auto"
    }

    # --------------------------------------------------------
    # Enviar diretamente para fal.ai
    # --------------------------------------------------------

    url = (
        "https://queue.fal.run/"
        "fal-ai/vidu/q3/image-to-video"
    )

    headers = {
        "Authorization": f"Key {api_key}",
        "Content-Type": "application/json"
    }

    try:

        resposta = requests.post(
            url,
            headers=headers,
            json=dados,
            timeout=180
        )

    except Exception as erro:

        raise RuntimeError(
            "Erro de conexão com o fal.ai:\n\n"
            f"{erro}"
        )

    # --------------------------------------------------------
    # Verificar HTTP
    # --------------------------------------------------------

    if resposta.status_code not in [
        200,
        201,
        202
    ]:

        try:
            detalhes = resposta.json()

        except Exception:
            detalhes = resposta.text

        raise RuntimeError(
            f"fal.ai retornou HTTP "
            f"{resposta.status_code}:\n\n"
            f"{detalhes}"
        )

    # --------------------------------------------------------
    # Ler resposta
    # --------------------------------------------------------

    try:

        resultado = resposta.json()

    except Exception as erro:

        raise RuntimeError(
            "O fal.ai não retornou JSON válido:\n\n"
            f"{erro}"
        )

    # --------------------------------------------------------
    # Resultado direto
    # --------------------------------------------------------

    if isinstance(resultado, dict):

        video = resultado.get(
            "video"
        )

        if video:

            video_url = video.get(
                "url"
            )

            if video_url:
                return baixar_video(
                    video_url
                )

        # ----------------------------------------------------
        # Caso seja uma tarefa na fila
        # ----------------------------------------------------

        request_id = (
            resultado.get("request_id")
            or resultado.get("requestId")
        )

        if request_id:

            return acompanhar_fila(
                request_id,
                api_key
            )

    raise RuntimeError(
        "O fal.ai recebeu a solicitação, "
        "mas não retornou um vídeo.\n\n"
        f"Resposta:\n{resultado}"
    )


# ============================================================
# ⏳ ACOMPANHAR FILA
# ============================================================

def acompanhar_fila(
    request_id,
    api_key
):

    import time

    status_url = (
        "https://queue.fal.run/"
        f"{MODELO}/requests/"
        f"{request_id}/status"
    )

    resultado_url = (
        "https://queue.fal.run/"
        f"{MODELO}/requests/"
        f"{request_id}"
    )

    headers = {
        "Authorization": f"Key {api_key}"
    }

    for _ in range(120):

        try:

            resposta = requests.get(
                status_url,
                headers=headers,
                timeout=30
            )

        except Exception as erro:

            raise RuntimeError(
                f"Erro verificando a fila:\n{erro}"
            )

        if resposta.status_code != 200:

            raise RuntimeError(
                "Erro ao consultar a fila:\n"
                f"HTTP {resposta.status_code}\n\n"
                f"{resposta.text}"
            )

        status = resposta.json()

        estado = status.get(
            "status",
            ""
        )

        if estado == "COMPLETED":

            break

        if estado == "FAILED":

            raise RuntimeError(
                f"A geração falhou:\n{status}"
            )

        time.sleep(3)

    else:

        raise RuntimeError(
            "A geração demorou mais do que "
            "o esperado."
        )

    try:

        resposta = requests.get(
            resultado_url,
            headers=headers,
            timeout=60
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro ao buscar resultado:\n{erro}"
        )

    if resposta.status_code != 200:

        raise RuntimeError(
            "Não foi possível obter o resultado:\n"
            f"{resposta.text}"
        )

    resultado = resposta.json()

    video = resultado.get(
        "video"
    )

    if not video:

        raise RuntimeError(
            "Resultado recebido sem vídeo:\n\n"
            f"{resultado}"
        )

    video_url = video.get(
        "url"
    )

    if not video_url:

        raise RuntimeError(
            "URL do vídeo não encontrada."
        )

    return baixar_video(
        video_url
    )


# ============================================================
# 📥 BAIXAR VÍDEO
# ============================================================

def baixar_video(
    video_url
):

    try:

        resposta = requests.get(
            video_url,
            timeout=180
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro ao baixar vídeo:\n{erro}"
        )

    if resposta.status_code != 200:

        raise RuntimeError(
            "Erro ao baixar vídeo:\n"
            f"HTTP {resposta.status_code}"
        )

    caminho = (
        PASTA / "video_vidu_q3.mp4"
    )

    caminho.write_bytes(
        resposta.content
    )

    return str(caminho)


# ============================================================
# 🖥️ INTERFACE
# ============================================================

st.set_page_config(
    page_title="Teste Vidu Q3",
    page_icon="🎬"
)

st.title(
    "🎬 TESTE DE VÍDEO — VIDU Q3"
)

st.write(
    "Teste isolado usando fal.ai."
)

st.info(
    "🎥 Motor: Vidu Q3\n\n"
    "🏢 Provedor: fal.ai\n\n"
    "🖼️ Entrada: imagem + prompt\n\n"
    "📦 Upload: Base64 direto"
)


# ============================================================
# 🖼️ IMAGEM
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
# 📝 PROMPT
# ============================================================

prompt = st.text_area(
    "📝 O que deve acontecer?",
    value=(
        "Um personagem futurista caminha "
        "lentamente por uma cidade cyberpunk "
        "durante a noite. As luzes neon "
        "refletem no chão molhado. "
        "A cena é cinematográfica e realista."
    ),
    height=160
)


# ============================================================
# 🎥 CÂMERA
# ============================================================

movimento = st.selectbox(
    "🎥 Movimento da câmera:",
    [
        "Câmera acompanha o personagem suavemente.",
        "Travelling cinematográfico para frente.",
        "Travelling lateral.",
        "Zoom cinematográfico lento.",
        "Câmera se afasta e retorna ao personagem.",
        "Movimento circular ao redor do personagem.",
        "Câmera estável."
    ]
)


# ============================================================
# ⏱️ DURAÇÃO
# ============================================================

duracao = st.selectbox(
    "⏱️ Duração:",
    [
        1,
        2,
        3,
        4,
        5
    ],
    index=3
)


# ============================================================
# 📺 RESOLUÇÃO
# ============================================================

resolucao = st.selectbox(
    "📺 Resolução:",
    [
        "720p",
        "1080p"
    ]
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

            st.caption(
                "🎥 Motor confirmado: "
                "fal.ai / Vidu Q3"
            )

            with open(
                caminho,
                "rb"
            ) as video:

                st.download_button(
                    "📥 Baixar vídeo",
                    data=video,
                    file_name="video_vidu_q3.mp4",
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
