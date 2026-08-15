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
# 📁 PASTA DO VÍDEO
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
# 🎬 ENVIAR GERAÇÃO
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
        "prompt": prompt,
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
# ⏳ CONSULTAR STATUS
# ============================================================

def esperar_video(request_id):

    api_key = obter_api_key()

    if not api_key:

        raise RuntimeError(
            "PIXAZO_API_KEY não foi encontrada."
        )

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
                f"Erro ao consultar geração "
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

            urls = output.get(
                "media_url"
            )

            if not urls:

                raise RuntimeError(
                    "A geração terminou, "
                    "mas a URL do vídeo não foi encontrada."
                )

            if isinstance(
                urls,
                list
            ):

                video_url = urls[0]

            else:

                video_url = urls

            return video_url

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

        # ----------------------------------------------------
        # PROCESSANDO
        # ----------------------------------------------------

        if status in [
            "QUEUED",
            "PROCESSING"
        ]:

            time.sleep(
                INTERVALO_STATUS
            )

            continue

        # ----------------------------------------------------
        # STATUS DESCONHECIDO
        # ----------------------------------------------------

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
# 🎬 GERAR VÍDEO COMPLETO
# ============================================================

def gerar_video(
    imagem_url,
    prompt
):

    request_id = solicitar_video(
        imagem_url,
        prompt
    )

    video_url = esperar_video(
        request_id
    )

    caminho = baixar_video(
        video_url
    )

    return caminho


# ============================================================
# 🖥️ INTERFACE
# ============================================================

st.set_page_config(
    page_title="Teste Vídeo Pixazo",
    page_icon="🎬",
    layout="centered"
)


# ============================================================
# 🎬 CABEÇALHO
# ============================================================

st.title(
    "🎬 Teste de Vídeo — Pixazo"
)

st.write(
    "Teste isolado de geração de vídeo "
    "usando Vidu Q3 Turbo."
)

st.info(
    f"🎥 Motor: Vidu Q3 Turbo\n\n"
    f"⏱️ Duração: {DURACAO} segundos\n\n"
    f"📺 Resolução: {RESOLUCAO}"
)


# ============================================================
# 🖼️ IMAGEM
# ============================================================

st.subheader(
    "🖼️ Imagem inicial"
)

imagem_url = st.text_input(
    "Cole a URL pública da imagem:",
    placeholder="https://exemplo.com/personagem.png"
)

st.caption(
    "A imagem precisa estar disponível por uma URL pública."
)


# ============================================================
# 📝 PROMPT
# ============================================================

st.subheader(
    "🎥 Movimento"
)

prompt = st.text_area(
    "Descreva o movimento do vídeo:",
    value=(
        "O personagem começa parado e depois "
        "caminha lentamente em direção à câmera. "
        "A câmera faz um movimento cinematográfico "
        "suave, mantendo o personagem como referência "
        "visual principal. O rosto, cabelo, roupa e "
        "características do personagem permanecem "
        "consistentes durante toda a cena. "
        "Iluminação cinematográfica profissional, "
        "movimento natural e realista."
    ),
    height=180
)


# ============================================================
# 🎥 BOTÃO
# ============================================================

if st.button(
    "🎬 Gerar vídeo",
    type="primary",
    use_container_width=True
):

    if not imagem_url.strip():

        st.warning(
            "⚠️ Cole primeiro a URL pública "
            "da imagem inicial."
        )

    elif not prompt.strip():

        st.warning(
            "⚠️ Digite o movimento do vídeo."
        )

    else:

        try:

            with st.spinner(
                "🎬 Enviando vídeo para a Pixazo..."
            ):

                request_id = solicitar_video(
                    imagem_url,
                    prompt
                )

            st.success(
                "✅ Pedido enviado!"
            )

            st.caption(
                f"ID da geração: {request_id}"
            )

            with st.spinner(
                "⏳ Gerando vídeo... "
                "Isso pode levar alguns minutos."
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
                "🎥 Motor utilizado: "
                "Pixazo / Vidu Q3 Turbo"
            )

            st.download_button(
                label="📥 Baixar vídeo",
                data=Path(caminho).read_bytes(),
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
