# ============================================================
# 🎬 ALEX IA ULTRA — TESTE DE VÍDEO
# PIXAZO / VIDU Q3 TURBO
# Criado por Geovani
# ============================================================

import os
import time
from pathlib import Path

import requests
import streamlit as st


# ============================================================
# ⚙️ CONFIGURAÇÃO
# ============================================================

MODELO_VIDEO = "vidu-q3-turbo"

PIXAZO_URL = (
    "https://gateway.pixazo.ai/"
    "vidu-q3-turbo/v1/image-to-video"
)

STATUS_URL = (
    "https://gateway.pixazo.ai/"
    "v2/requests/status/"
)

DURACAO = 5
RESOLUCAO = "720p"

TEMPO_MAXIMO = 600
INTERVALO_STATUS = 5


# ============================================================
# 🔐 API KEY
# ============================================================

def obter_api_key():

    try:
        chave = st.secrets.get(
            "PIXAZO_API_KEY",
            ""
        )
    except Exception:
        chave = ""

    if not chave:
        chave = os.environ.get(
            "PIXAZO_API_KEY",
            ""
        )

    return str(chave).strip()


# ============================================================
# 📁 PASTA DE VÍDEOS
# ============================================================

def obter_pasta_videos():

    pasta = Path(
        "/tmp/alex_ia_ultra_videos"
    )

    pasta.mkdir(
        parents=True,
        exist_ok=True
    )

    return pasta


# ============================================================
# 🎬 SOLICITAR VÍDEO
# ============================================================

def solicitar_video(
    imagem_url,
    prompt
):

    api_key = obter_api_key()

    if not api_key:
        raise RuntimeError(
            "PIXAZO_API_KEY não foi encontrada "
            "nos Secrets do Streamlit."
        )

    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "Ocp-Apim-Subscription-Key": api_key,
    }

    dados = {
        "start_image": imagem_url,
        "prompt": prompt.strip(),
        "duration": DURACAO,
        "resolution": RESOLUCAO,
        "audio": False,
    }

    try:

        resposta = requests.post(
            PIXAZO_URL,
            headers=headers,
            json=dados,
            timeout=120,
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro de conexão com a Pixazo:\n{erro}"
        )

    if resposta.status_code not in [200, 201, 202]:

        try:
            detalhes = resposta.json()
        except Exception:
            detalhes = resposta.text

        raise RuntimeError(
            f"Pixazo retornou HTTP "
            f"{resposta.status_code}:\n\n"
            f"{detalhes}"
        )

    try:
        resultado = resposta.json()
    except Exception as erro:

        raise RuntimeError(
            f"A Pixazo não retornou JSON válido:\n{erro}"
        )

    request_id = resultado.get(
        "request_id"
    )

    if not request_id:

        raise RuntimeError(
            "A Pixazo não retornou request_id.\n\n"
            f"Resposta recebida:\n{resultado}"
        )

    return request_id


# ============================================================
# ⏳ AGUARDAR GERAÇÃO
# ============================================================

def esperar_video(request_id):

    api_key = obter_api_key()

    headers = {
        "Ocp-Apim-Subscription-Key": api_key,
    }

    inicio = time.time()

    while True:

        if time.time() - inicio > TEMPO_MAXIMO:

            raise RuntimeError(
                "Tempo máximo de espera atingido."
            )

        url = STATUS_URL + request_id

        try:

            resposta = requests.get(
                url,
                headers=headers,
                timeout=60,
            )

        except Exception as erro:

            raise RuntimeError(
                f"Erro ao consultar o status:\n{erro}"
            )

        if resposta.status_code != 200:

            try:
                detalhes = resposta.json()
            except Exception:
                detalhes = resposta.text

            raise RuntimeError(
                f"Erro ao consultar status "
                f"HTTP {resposta.status_code}:\n\n"
                f"{detalhes}"
            )

        try:
            resultado = resposta.json()
        except Exception as erro:

            raise RuntimeError(
                f"Resposta de status inválida:\n{erro}"
            )

        status = str(
            resultado.get(
                "status",
                ""
            )
        ).upper()

        # ----------------------------------------------------
        # CONCLUÍDO
        # ----------------------------------------------------

        if status == "COMPLETED":

            output = resultado.get(
                "output"
            )

            if not isinstance(
                output,
                dict
            ):

                raise RuntimeError(
                    "A geração terminou, "
                    "mas o campo output não foi encontrado."
                )

            media_url = output.get(
                "media_url"
            )

            if not media_url:

                raise RuntimeError(
                    "A geração terminou, "
                    "mas a URL do vídeo não foi encontrada."
                )

            if isinstance(
                media_url,
                list
            ):

                return media_url[0]

            return media_url

        # ----------------------------------------------------
        # ERRO
        # ----------------------------------------------------

        if status in [
            "FAILED",
            "ERROR"
        ]:

            erro = resultado.get(
                "error",
                "Erro desconhecido."
            )

            raise RuntimeError(
                f"A Pixazo informou um erro:\n{erro}"
            )

        time.sleep(
            INTERVALO_STATUS
        )


# ============================================================
# 📥 BAIXAR VÍDEO
# ============================================================

def baixar_video(video_url):

    try:

        resposta = requests.get(
            video_url,
            timeout=180,
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro ao baixar o vídeo:\n{erro}"
        )

    if resposta.status_code != 200:

        raise RuntimeError(
            "Não foi possível baixar o vídeo.\n"
            f"HTTP {resposta.status_code}"
        )

    caminho = (
        obter_pasta_videos()
        / "video_pixazo.mp4"
    )

    caminho.write_bytes(
        resposta.content
    )

    return str(caminho)


# ============================================================
# 🖥️ CONFIGURAÇÃO DA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Teste Vídeo Pixazo",
    page_icon="🎬",
    layout="centered"
)


# ============================================================
# 🎬 TÍTULO
# ============================================================

st.title(
    "🎬 Teste de Vídeo — Pixazo"
)

st.write(
    "Teste isolado do Vidu Q3 Turbo "
    "através da API da Pixazo."
)

st.info(
    f"🎥 Motor: Vidu Q3 Turbo\n\n"
    f"⏱️ Duração: {DURACAO} segundos\n\n"
    f"📺 Resolução: {RESOLUCAO}"
)


# ============================================================
# 🖼️ UPLOAD LOCAL
# ============================================================

st.subheader(
    "🖼️ Imagem do personagem"
)

arquivo_imagem = st.file_uploader(
    "Escolha uma imagem do seu celular:",
    type=[
        "png",
        "jpg",
        "jpeg",
        "webp"
    ]
)

if arquivo_imagem:

    st.image(
        arquivo_imagem,
        caption="Imagem selecionada",
        use_container_width=True
    )


# ============================================================
# 🌐 URL PÚBLICA
# ============================================================

st.subheader(
    "🌐 URL pública da imagem"
)

imagem_url = st.text_input(
    "Cole aqui a URL pública:",
    placeholder="https://site.com/imagem.png"
)

st.caption(
    "A Pixazo precisa conseguir acessar a imagem "
    "pela internet. O upload acima serve para "
    "você visualizar a imagem, mas o Vidu precisa "
    "receber uma URL pública."
)


# ============================================================
# 📝 PROMPT
# ============================================================

st.subheader(
    "🎥 Movimento da cena"
)

prompt = st.text_area(
    "Descreva o que deve acontecer:",
    value=(
        "O personagem começa parado e depois "
        "caminha lentamente para frente. "
        "A câmera faz um movimento cinematográfico "
        "suave, mantendo o personagem como referência "
        "visual principal. "
        "Manter exatamente o mesmo rosto, cabelo, "
        "roupa, aparência e características do personagem "
        "durante toda a cena. "
        "Movimentos naturais e realistas, "
        "iluminação cinematográfica profissional."
    ),
    height=200
)


# ============================================================
# 🎥 GERAR
# ============================================================

if st.button(
    "🎬 Gerar vídeo",
    type="primary",
    use_container_width=True
):

    if not imagem_url.strip():

        st.warning(
            "⚠️ Para este primeiro teste, "
            "precisamos de uma URL pública da imagem."
        )

    elif not prompt.strip():

        st.warning(
            "⚠️ Digite o movimento do vídeo."
        )

    else:

        try:

            with st.spinner(
                "🎬 Enviando pedido para a Pixazo..."
            ):

                request_id = solicitar_video(
                    imagem_url,
                    prompt
                )

            st.success(
                "✅ Pedido enviado para a Pixazo!"
            )

            st.caption(
                f"ID: {request_id}"
            )

            with st.spinner(
                "⏳ Gerando vídeo... aguarde."
            ):

                video_url = esperar_video(
                    request_id
                )

            st.success(
                "🎉 Vídeo gerado com sucesso!"
            )

            with st.spinner(
                "📥 Baixando vídeo..."
            ):

                caminho = baixar_video(
                    video_url
                )

            st.video(
                caminho
            )

            st.caption(
                "🎥 Pixazo / Vidu Q3 Turbo"
            )

            st.download_button(
                "📥 Baixar vídeo",
                data=Path(
                    caminho
                ).read_bytes(),
                file_name="video_pixazo.mp4",
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
