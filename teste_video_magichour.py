# ============================================================
# 🎬 TESTE DE VÍDEO — MAGIC HOUR
# IMAGE-TO-VIDEO / LTX 2.3
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

API_URL = "https://api.magichour.ai/v1"

MODELO = "ltx-2.3"

PASTA = Path("/tmp/alex_ia_ultra_magichour")

PASTA.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 🔐 API KEY
# ============================================================

def obter_api_key():

    try:
        chave = st.secrets.get(
            "MAGIC_HOUR_API_KEY",
            ""
        )
    except Exception:
        chave = ""

    if not chave:
        chave = os.environ.get(
            "MAGIC_HOUR_API_KEY",
            ""
        )

    return str(chave).strip()


# ============================================================
# 📤 UPLOAD DA IMAGEM
# ============================================================

def enviar_imagem(
    imagem_bytes,
    nome_arquivo
):

    api_key = obter_api_key()

    if not api_key:

        raise RuntimeError(
            "MAGIC_HOUR_API_KEY não foi encontrada "
            "nos Secrets do Streamlit."
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    arquivos = {
        "file": (
            nome_arquivo,
            imagem_bytes,
            "image/png"
        )
    }

    try:

        resposta = requests.post(
            f"{API_URL}/files",
            headers=headers,
            files=arquivos,
            timeout=120
        )

    except Exception as erro:

        raise RuntimeError(
            "Erro de conexão ao enviar "
            f"a imagem:\n{erro}"
        )

    if resposta.status_code not in (
        200,
        201
    ):

        try:
            detalhes = resposta.json()
        except Exception:
            detalhes = resposta.text

        raise RuntimeError(
            f"Magic Hour retornou HTTP "
            f"{resposta.status_code} ao enviar a imagem:\n\n"
            f"{detalhes}"
        )

    try:

        dados = resposta.json()

    except Exception as erro:

        raise RuntimeError(
            "A resposta do upload não é JSON válido:\n"
            f"{erro}"
        )

    # Tentar localizar o caminho retornado
    caminho = (
        dados.get("file_path")
        or dados.get("path")
        or dados.get("id")
    )

    if not caminho:

        raise RuntimeError(
            "A imagem foi enviada, mas não encontramos "
            "o file_path na resposta:\n\n"
            f"{dados}"
        )

    return caminho


# ============================================================
# 🎬 CRIAR VÍDEO
# ============================================================

def criar_video(
    image_path,
    prompt
):

    api_key = obter_api_key()

    if not api_key:

        raise RuntimeError(
            "MAGIC_HOUR_API_KEY não foi encontrada."
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    dados = {
        "name": "Teste Alex IA Ultra",
        "end_seconds": 5,
        "model": MODELO,
        "resolution": "480p",
        "assets": {
            "image_file_path": image_path
        },
        "style": {
            "prompt": prompt
        }
    }

    try:

        resposta = requests.post(
            f"{API_URL}/image-to-video",
            headers=headers,
            json=dados,
            timeout=120
        )

    except Exception as erro:

        raise RuntimeError(
            "Erro de conexão com o Magic Hour:\n"
            f"{erro}"
        )

    if resposta.status_code not in (
        200,
        201,
        202
    ):

        try:
            detalhes = resposta.json()
        except Exception:
            detalhes = resposta.text

        raise RuntimeError(
            f"Magic Hour retornou HTTP "
            f"{resposta.status_code}:\n\n"
            f"{detalhes}"
        )

    try:

        resultado = resposta.json()

    except Exception as erro:

        raise RuntimeError(
            "Resposta inválida do Magic Hour:\n"
            f"{erro}"
        )

    return resultado


# ============================================================
# 🔎 ENCONTRAR ID DO PROJETO
# ============================================================

def encontrar_id(resultado):

    if not isinstance(
        resultado,
        dict
    ):
        return None

    return (
        resultado.get("id")
        or resultado.get("project_id")
        or resultado.get("video_id")
    )


# ============================================================
# ⏳ CONSULTAR VÍDEO
# ============================================================

def consultar_video(
    projeto_id
):

    api_key = obter_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    # Endpoint de projeto
    url = (
        f"{API_URL}/image-to-video/"
        f"{projeto_id}"
    )

    try:

        resposta = requests.get(
            url,
            headers=headers,
            timeout=60
        )

    except Exception as erro:

        raise RuntimeError(
            "Erro ao consultar o vídeo:\n"
            f"{erro}"
        )

    if resposta.status_code != 200:

        try:
            detalhes = resposta.json()
        except Exception:
            detalhes = resposta.text

        raise RuntimeError(
            f"Magic Hour retornou HTTP "
            f"{resposta.status_code} ao consultar:\n\n"
            f"{detalhes}"
        )

    try:

        return resposta.json()

    except Exception as erro:

        raise RuntimeError(
            "Resposta inválida ao consultar vídeo:\n"
            f"{erro}"
        )


# ============================================================
# 🔗 PROCURAR URL DO VÍDEO
# ============================================================

def encontrar_url_video(dados):

    if not isinstance(
        dados,
        dict
    ):
        return None

    # Possíveis campos
    candidatos = [
        dados.get("video_url"),
        dados.get("url"),
        dados.get("download_url"),
        dados.get("output_url"),
    ]

    # Procurar dentro de output
    output = dados.get("output")

    if isinstance(
        output,
        dict
    ):

        candidatos.extend([
            output.get("url"),
            output.get("video_url"),
            output.get("download_url"),
        ])

    if isinstance(
        output,
        list
    ):

        for item in output:

            if isinstance(
                item,
                str
            ):
                candidatos.append(item)

            elif isinstance(
                item,
                dict
            ):

                candidatos.extend([
                    item.get("url"),
                    item.get("video_url"),
                    item.get("download_url"),
                ])

    for candidato in candidatos:

        if isinstance(
            candidato,
            str
        ) and candidato.startswith(
            "http"
        ):

            return candidato

    return None


# ============================================================
# 💾 BAIXAR VÍDEO
# ============================================================

def baixar_video(url):

    caminho = (
        PASTA /
        "video_magichour.mp4"
    )

    try:

        resposta = requests.get(
            url,
            timeout=180
        )

    except Exception as erro:

        raise RuntimeError(
            "Erro ao baixar o vídeo:\n"
            f"{erro}"
        )

    if resposta.status_code != 200:

        raise RuntimeError(
            "Não foi possível baixar o vídeo.\n"
            f"HTTP {resposta.status_code}"
        )

    caminho.write_bytes(
        resposta.content
    )

    return str(caminho)


# ============================================================
# 🖥️ INTERFACE
# ============================================================

st.set_page_config(
    page_title="Teste Magic Hour",
    page_icon="🎬"
)

st.title(
    "🎬 TESTE DE VÍDEO — MAGIC HOUR"
)

st.caption(
    "Image-to-Video • LTX 2.3"
)

st.info(
    "Motor de teste: Magic Hour / LTX 2.3"
)


# ============================================================
# 🖼️ IMAGEM
# ============================================================

imagem = st.file_uploader(
    "🖼️ Escolha uma imagem",
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
    "📝 Movimento do personagem",
    value=(
        "O personagem começa a caminhar "
        "lentamente para frente. "
        "A câmera acompanha suavemente "
        "o personagem em um movimento "
        "cinematográfico. "
        "Manter a identidade, rosto, "
        "cabelo, roupa e aparência "
        "consistentes durante toda a cena."
    ),
    height=180
)


# ============================================================
# 🎬 BOTÃO
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

        st.stop()

    if not prompt.strip():

        st.warning(
            "⚠️ Digite o movimento."
        )

        st.stop()

    try:

        # ----------------------------------------------------
        # Upload
        # ----------------------------------------------------

        with st.spinner(
            "📤 Enviando imagem..."
        ):

            image_path = enviar_imagem(
                imagem.getvalue(),
                imagem.name
            )

        st.success(
            "✅ Imagem enviada."
        )

        # ----------------------------------------------------
        # Criar projeto
        # ----------------------------------------------------

        with st.spinner(
            "🎬 Criando vídeo..."
        ):

            resultado = criar_video(
                image_path,
                prompt
            )

        st.write(
            "📡 Resposta inicial:"
        )

        st.json(resultado)

        projeto_id = encontrar_id(
            resultado
        )

        if not projeto_id:

            st.error(
                "❌ Não encontramos o ID "
                "do projeto na resposta."
            )

            st.stop()

        st.info(
            f"🎬 Projeto criado: {projeto_id}"
        )

        # ----------------------------------------------------
        # Aguardar processamento
        # ----------------------------------------------------

        progresso = st.progress(0)

        video_url = None

        for tentativa in range(60):

            time.sleep(5)

            dados = consultar_video(
                projeto_id
            )

            progresso.progress(
                min(
                    (tentativa + 1) / 60,
                    1.0
                )
            )

            status = str(
                dados.get(
                    "status",
                    ""
                )
            ).lower()

            st.caption(
                f"⏳ Status: {status or 'processando'}"
            )

            video_url = encontrar_url_video(
                dados
            )

            if video_url:

                break

            if status in (
                "failed",
                "error",
                "cancelled"
            ):

                raise RuntimeError(
                    "A geração do vídeo falhou:\n\n"
                    f"{dados}"
                )

        # ----------------------------------------------------
        # Verificar resultado
        # ----------------------------------------------------

        if not video_url:

            raise RuntimeError(
                "O vídeo não ficou pronto dentro "
                "do tempo de espera.\n\n"
                f"Última resposta:\n{dados}"
            )

        # ----------------------------------------------------
        # Baixar
        # ----------------------------------------------------

        with st.spinner(
            "⬇️ Baixando vídeo..."
        ):

            caminho = baixar_video(
                video_url
            )

        # ----------------------------------------------------
        # Mostrar
        # ----------------------------------------------------

        st.success(
            "🎉 VÍDEO GERADO COM SUCESSO!"
        )

        st.video(
            caminho
        )

        st.caption(
            "🎥 Motor: Magic Hour / LTX 2.3"
        )

        st.download_button(
            "⬇️ Baixar vídeo",
            data=Path(caminho).read_bytes(),
            file_name="video_magichour.mp4",
            mime="video/mp4",
            use_container_width=True
        )

    except Exception as erro:

        st.error(
            "❌ Erro no Magic Hour:"
        )

        st.code(
            str(erro)
  )
