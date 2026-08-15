# ============================================================
# 🎬 VIDEO.PY — GERENCIADOR AUTOMÁTICO DE VÍDEO
# Alex IA Ultra
#
# MOTORES:
# 1. LTX-2.3 — Hugging Face
# 2. Magic Hour — LTX-2.3
#
# COM IMAGEM:
#     Magic Hour → LTX-2.3 como fallback
#
# SEM IMAGEM:
#     LTX-2.3 — Hugging Face
# ============================================================

import os
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import requests
import streamlit as st

try:
    from gradio_client import Client
except ImportError:
    Client = None


# ============================================================
# ⚙️ CONFIGURAÇÃO
# ============================================================

NOME_MODULO = "Alex IA Ultra — Gerenciador de Vídeo"

MOTORES_VIDEO = [
    "LTX-2.3 — Hugging Face",
    "Magic Hour — LTX-2.3",
]

CAMERAS = [
    "Sony FX5",
    "Sony FX6",
    "Canon EOS C80",
    "ARRI Alexa Mini LF",
]

PROPORCOES = [
    "1:1",
    "16:9",
    "9:16",
]

DURACAO_PADRAO = 5


# ============================================================
# 🎬 LTX-2.3 — HUGGING FACE
# ============================================================

LTX_HF_SPACE = (
    "https://lightricks-ltx-2-3.hf.space"
)


# ============================================================
# 🎬 MAGIC HOUR
# ============================================================

MAGIC_HOUR_BASE_URL = (
    "https://api.magichour.ai/v1"
)

MAGIC_HOUR_MODELO = "ltx-2.3"

MAGIC_HOUR_RESOLUCAO = "480p"

MAGIC_HOUR_DURACAO = 5


# ============================================================
# 📁 PASTA TEMPORÁRIA
# ============================================================

PASTA = Path(
    "/tmp/alex_ia_ultra_videos"
)

PASTA.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# 🔐 API KEY MAGIC HOUR
# ============================================================

def obter_api_key_magichour():

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
# 🔐 HEADERS MAGIC HOUR
# ============================================================

def headers_magichour():

    chave = obter_api_key_magichour()

    if not chave:

        raise RuntimeError(
            "MAGIC_HOUR_API_KEY não foi encontrada "
            "nos Secrets do Streamlit."
        )

    return {

        "Authorization":
            f"Bearer {chave}",

        "Accept":
            "application/json",

        "Content-Type":
            "application/json",
    }


# ============================================================
# 🧰 SALVAR ARQUIVO
# ============================================================

def salvar_video(
    conteudo,
    nome
):

    caminho = (
        PASTA /
        nome
    )

    caminho.write_bytes(
        conteudo
    )

    return str(caminho)


# ============================================================
# 🎬 MOTOR 1
# LTX-2.3 — HUGGING FACE
# ============================================================

def gerar_ltx_huggingface(
    prompt,
    duration=5.0,
    height=512,
    width=512
):

    if Client is None:

        raise RuntimeError(
            "gradio_client não está instalado."
        )

    if not prompt or not prompt.strip():

        raise ValueError(
            "O prompt do vídeo está vazio."
        )

    # --------------------------------------------------------
    # CONECTAR
    # --------------------------------------------------------

    client = Client(
        LTX_HF_SPACE
    )

    # --------------------------------------------------------
    # GERAR
    # --------------------------------------------------------

    resultado = client.predict(

        input_image=None,

        prompt=prompt.strip(),

        duration=float(
            duration
        ),

        enhance_prompt=True,

        seed=0,

        randomize_seed=True,

        height=int(
            height
        ),

        width=int(
            width
        ),

        api_name="/generate_video"
    )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    if isinstance(
        resultado,
        (tuple, list)
    ):

        if not resultado:

            raise RuntimeError(
                "LTX-2.3 não retornou resultado."
            )

        caminho_video = (
            resultado[0]
        )

        seed = (
            resultado[1]
            if len(resultado) > 1
            else None
        )

    else:

        caminho_video = resultado

        seed = None

    if not caminho_video:

        raise RuntimeError(
            "LTX-2.3 não retornou o vídeo."
        )

    return {

        "motor":
            "LTX-2.3 — Hugging Face",

        "video":
            str(caminho_video),

        "seed":
            seed,

    }


# ============================================================
# 📤 MAGIC HOUR
# OBTER URL DE UPLOAD
# ============================================================

def obter_url_upload(
    extensao
):

    extensao = (
        extensao
        .lower()
        .replace(
            ".",
            ""
        )
    )

    formatos = [

        "png",
        "jpg",
        "jpeg",
        "webp",
        "jfif",
        "heic",
        "heif",
        "avif",
        "bmp",
        "tif",
        "tiff",

    ]

    if extensao not in formatos:

        raise RuntimeError(
            "Formato de imagem não suportado: "
            f"{extensao}"
        )

    dados = {

        "items": [

            {

                "type":
                    "image",

                "extension":
                    extensao

            }

        ]

    }

    resposta = requests.post(

        f"{MAGIC_HOUR_BASE_URL}"
        "/files/upload-urls",

        headers=
            headers_magichour(),

        json=
            dados,

        timeout=60
    )

    if resposta.status_code != 200:

        try:

            detalhes = (
                resposta.json()
            )

        except Exception:

            detalhes = (
                resposta.text
            )

        raise RuntimeError(

            "Magic Hour retornou "
            f"HTTP {resposta.status_code} "
            "ao solicitar upload:\n\n"
            f"{detalhes}"

        )

    resultado = (
        resposta.json()
    )

    itens = (
        resultado.get(
            "items"
        )
    )

    if not itens:

        raise RuntimeError(

            "Magic Hour não retornou "
            "a lista de upload.\n\n"
            f"{resultado}"

        )

    primeiro = (
        itens[0]
    )

    upload_url = (
        primeiro.get(
            "upload_url"
        )
    )

    file_path = (
        primeiro.get(
            "file_path"
        )
    )

    if (
        not upload_url
        or
        not file_path
    ):

        raise RuntimeError(

            "A resposta não contém "
            "upload_url e file_path.\n\n"
            f"{resultado}"

        )

    return (
        upload_url,
        file_path
    )


# ============================================================
# 🖼️ ENVIAR IMAGEM PARA MAGIC HOUR
# ============================================================

def enviar_imagem_magichour(
    imagem_bytes,
    nome_arquivo
):

    extensao = (
        Path(
            nome_arquivo
        )
        .suffix
        .lower()
        .replace(
            ".",
            ""
        )
    )

    upload_url, file_path = (
        obter_url_upload(
            extensao
        )
    )

    resposta = requests.put(

        upload_url,

        data=imagem_bytes,

        timeout=120
    )

    if resposta.status_code not in [

        200,
        201,
        204

    ]:

        raise RuntimeError(

            "Falha no upload da imagem.\n"
            f"HTTP {resposta.status_code}\n"
            f"{resposta.text}"

        )

    return file_path


# ============================================================
# 🎬 CRIAR PROJETO MAGIC HOUR
# ============================================================

def criar_projeto_magichour(
    file_path,
    prompt
):

    dados = {

        "name":
            "Alex IA Ultra",

        "end_seconds":
            MAGIC_HOUR_DURACAO,

        "model":
            MAGIC_HOUR_MODELO,

        "resolution":
            MAGIC_HOUR_RESOLUCAO,

        "audio":
            False,

        "style": {

            "prompt":
                prompt.strip()

        },

        "assets": {

            "image_file_path":
                file_path

        }

    }

    resposta = requests.post(

        f"{MAGIC_HOUR_BASE_URL}"
        "/image-to-video",

        headers=
            headers_magichour(),

        json=
            dados,

        timeout=120
    )

    if resposta.status_code not in [

        200,
        201,
        202

    ]:

        try:

            detalhes = (
                resposta.json()
            )

        except Exception:

            detalhes = (
                resposta.text
            )

        raise RuntimeError(

            "Magic Hour retornou "
            f"HTTP {resposta.status_code} "
            "ao criar vídeo:\n\n"
            f"{detalhes}"

        )

    resultado = (
        resposta.json()
    )

    projeto_id = (
        resultado.get(
            "id"
        )
    )

    if not projeto_id:

        raise RuntimeError(

            "Magic Hour não retornou "
            "o ID do vídeo.\n\n"
            f"{resultado}"

        )

    return (
        projeto_id,
        resultado
    )


# ============================================================
# 🔎 CONSULTAR PROJETO MAGIC HOUR
# ============================================================

def consultar_projeto_magichour(
    projeto_id
):

    urls = [

        (
            f"{MAGIC_HOUR_BASE_URL}"
            f"/video-projects/{projeto_id}"
        ),

        (
            f"{MAGIC_HOUR_BASE_URL}"
            f"/image-to-video/{projeto_id}"
        ),

    ]

    ultimo_erro = None

    for url in urls:

        try:

            resposta = requests.get(

                url,

                headers=
                    headers_magichour(),

                timeout=60
            )

        except Exception as erro:

            ultimo_erro = str(
                erro
            )

            continue

        if resposta.status_code == 200:

            try:

                return resposta.json()

            except Exception:

                return {}

        ultimo_erro = (

            f"HTTP {resposta.status_code}: "
            f"{resposta.text}"

        )

    raise RuntimeError(

        "Não foi possível consultar "
        "o projeto.\n\n"
        f"{ultimo_erro}"

    )


# ============================================================
# 🔗 ENCONTRAR DOWNLOAD
# ============================================================

def encontrar_download_magichour(
    dados
):

    if not isinstance(
        dados,
        dict
    ):

        return None

    # --------------------------------------------------------
    # CAMPOS DIRETOS
    # --------------------------------------------------------

    campos = [

        "video_url",
        "download_url",
        "output_url",
        "url",

    ]

    for campo in campos:

        valor = (
            dados.get(
                campo
            )
        )

        if (

            isinstance(
                valor,
                str
            )

            and

            valor.startswith(
                "http"
            )

        ):

            return valor

    # --------------------------------------------------------
    # DOWNLOADS — DICT
    # --------------------------------------------------------

    downloads = (
        dados.get(
            "downloads"
        )
    )

    if isinstance(
        downloads,
        dict
    ):

        for valor in (
            downloads.values()
        ):

            if (

                isinstance(
                    valor,
                    str
                )

                and

                valor.startswith(
                    "http"
                )

            ):

                return valor

            if isinstance(
                valor,
                dict
            ):

                for chave in [

                    "url",
                    "download_url"

                ]:

                    url = (
                        valor.get(
                            chave
                        )
                    )

                    if (

                        isinstance(
                            url,
                            str
                        )

                        and

                        url.startswith(
                            "http"
                        )

                    ):

                        return url

    # --------------------------------------------------------
    # DOWNLOADS — LIST
    # --------------------------------------------------------

    if isinstance(
        downloads,
        list
    ):

        for item in downloads:

            if (

                isinstance(
                    item,
                    str
                )

                and

                item.startswith(
                    "http"
                )

            ):

                return item

            if isinstance(
                item,
                dict
            ):

                for chave in [

                    "url",
                    "download_url"

                ]:

                    url = (
                        item.get(
                            chave
                        )
                    )

                    if (

                        isinstance(
                            url,
                            str
                        )

                        and

                        url.startswith(
                            "http"
                        )

                    ):

                        return url

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    output = (
        dados.get(
            "output"
        )
    )

    if isinstance(
        output,
        dict
    ):

        for valor in (
            output.values()
        ):

            if (

                isinstance(
                    valor,
                    str
                )

                and

                valor.startswith(
                    "http"
                )

            ):

                return valor

    return None


# ============================================================
# ⬇️ BAIXAR VÍDEO MAGIC HOUR
# ============================================================

def baixar_video_magichour(
    url
):

    caminho = (
        PASTA /
        "video_magichour.mp4"
    )

    resposta = requests.get(

        url,

        timeout=180
    )

    if resposta.status_code != 200:

        raise RuntimeError(

            "Falha ao baixar o vídeo.\n"
            f"HTTP {resposta.status_code}"

        )

    caminho.write_bytes(
        resposta.content
    )

    return str(
        caminho
    )


# ============================================================
# 🎬 GERAR MAGIC HOUR
# ============================================================

def gerar_magichour(
    imagem_bytes,
    nome_arquivo,
    prompt,
    timeout_segundos=300
):

    if not imagem_bytes:

        raise ValueError(

            "O Magic Hour precisa "
            "de uma imagem."

        )

    if not prompt or not prompt.strip():

        raise ValueError(
            "O prompt do vídeo está vazio."
        )

    # --------------------------------------------------------
    # 1 — UPLOAD
    # --------------------------------------------------------

    file_path = (
        enviar_imagem_magichour(

            imagem_bytes,

            nome_arquivo

        )
    )

    # --------------------------------------------------------
    # 2 — CRIAR PROJETO
    # --------------------------------------------------------

    projeto_id, resultado = (
        criar_projeto_magichour(

            file_path,

            prompt

        )
    )

    # --------------------------------------------------------
    # 3 — PROCESSAMENTO
    # --------------------------------------------------------

    inicio = time.time()

    ultimo_resultado = (
        resultado
    )

    video_url = (
        encontrar_download_magichour(
            ultimo_resultado
        )
    )

    while not video_url:

        if (
            time.time()
            -
            inicio
            >=
            timeout_segundos
        ):

            raise RuntimeError(

                "Tempo limite atingido "
                "no Magic Hour.\n\n"

                f"Última resposta:\n"
                f"{ultimo_resultado}"

            )

        time.sleep(5)

        ultimo_resultado = (
            consultar_projeto_magichour(
                projeto_id
            )
        )

        status = str(

            ultimo_resultado.get(

                "status",

                "processing"

            )

        ).lower()

        if status in [

            "failed",
            "error",
            "cancelled"

        ]:

            raise RuntimeError(

                "A geração no Magic Hour "
                "falhou.\n\n"

                f"{ultimo_resultado}"

            )

        video_url = (
            encontrar_download_magichour(
                ultimo_resultado
            )
        )

    # --------------------------------------------------------
    # 4 — DOWNLOAD
    # --------------------------------------------------------

    caminho = (
        baixar_video_magichour(
            video_url
        )
    )

    return {

        "motor":
            "Magic Hour — LTX-2.3",

        "video":
            caminho,

        "projeto_id":
            projeto_id,

        "url":
            video_url,

    }


# ============================================================
# 🤖 GERADOR AUTOMÁTICO
# ============================================================

def gerar_video_automatico(
    prompt,
    imagem_bytes=None,
    nome_imagem="imagem.png",
    duracao=5.0,
    width=512,
    height=512
):

    """
    SISTEMA AUTOMÁTICO.

    COM IMAGEM:

        1º Magic Hour
        2º LTX-2.3 Hugging Face

    SEM IMAGEM:

        LTX-2.3 Hugging Face

    Se um motor falhar, o próximo é acionado.
    """

    erros = []

    # ========================================================
    # 🥇 PRIMEIRO MOTOR — MAGIC HOUR
    # ========================================================

    if imagem_bytes:

        try:

            resultado = (
                gerar_magichour(

                    imagem_bytes=
                        imagem_bytes,

                    nome_arquivo=
                        nome_imagem,

                    prompt=
                        prompt

                )
            )

            resultado[
                "fallback"
            ] = False

            resultado[
                "erros_anteriores"
            ] = erros

            return resultado

        except Exception as erro:

            erros.append(

                "Magic Hour: "
                +
                str(erro)

            )

    # ========================================================
    # 🥈 SEGUNDO MOTOR — LTX-2.3 HUGGING FACE
    # ========================================================

    try:

        resultado = (
            gerar_ltx_huggingface(

                prompt=
                    prompt,

                duration=
                    duracao,

                height=
                    height,

                width=
                    width

            )
        )

        resultado[
            "fallback"
        ] = bool(
            erros
        )

        resultado[
            "erros_anteriores"
        ] = erros

        return resultado

    except Exception as erro:

        erros.append(

            "LTX-2.3 Hugging Face: "
            +
            str(erro)

        )

    # ========================================================
    # ❌ TODOS FALHARAM
    # ========================================================

    raise RuntimeError(

        "❌ NENHUM MOTOR DE VÍDEO "
        "CONSEGUIU GERAR O VÍDEO.\n\n"

        +
        "\n\n".join(
            erros
        )

    )


# ============================================================
# 🎬 FUNÇÃO PRINCIPAL PARA O APP.PY
# ============================================================

def gerar_video(
    prompt,
    imagem_bytes=None,
    nome_imagem="imagem.png",
    duracao=5.0,
    width=512,
    height=512
):

    """
    Função que o app.py pode chamar.

    Exemplo:

        resultado = gerar_video(
            prompt="Uma pessoa caminhando...",
            imagem_bytes=imagem.getvalue(),
            nome_imagem=imagem.name
        )

        caminho = resultado["video"]
    """

    return (
        gerar_video_automatico(

            prompt=
                prompt,

            imagem_bytes=
                imagem_bytes,

            nome_imagem=
                nome_imagem,

            duracao=
                duracao,

            width=
                width,

            height=
                height

        )
    )


# ============================================================
# 🎥 TEXT-TO-VIDEO
# ============================================================

def gerar_video_texto(
    prompt,
    duracao=5.0
):

    return (
        gerar_ltx_huggingface(

            prompt=
                prompt,

            duration=
                duracao

        )
    )


# ============================================================
# 🖼️ IMAGE-TO-VIDEO
# ============================================================

def gerar_video_imagem(
    imagem_bytes,
    nome_imagem,
    prompt
):

    return (
        gerar_magichour(

            imagem_bytes=
                imagem_bytes,

            nome_arquivo=
                nome_imagem,

            prompt=
                prompt

        )
    )


# ============================================================
# 📊 INFORMAÇÕES DOS MOTORES
# ============================================================

def listar_motores():

    return {

        "motores":
            MOTORES_VIDEO,

        "cameras":
            CAMERAS,

        "proporcoes":
            PROPORCOES,

        "duracao_padrao":
            DURACAO_PADRAO,

    }


# ============================================================
# 🧪 INTERFACE DE TESTE
#
# Esta parte permite testar video.py diretamente.
# O app.py principal não precisa usar esta interface.
# ============================================================

def interface_teste():

    st.set_page_config(

        page_title=
            "Alex IA Ultra — Vídeo",

        page_icon=
            "🎬",

        layout=
            "wide"

    )

    st.title(
        "🎬 Alex IA Ultra — Gerador de Vídeo"
    )

    st.caption(
        "LTX-2.3 + Magic Hour • Seleção automática"
    )

    st.info(

        "🖼️ Com imagem: "
        "Magic Hour → LTX-2.3\n\n"

        "📝 Sem imagem: "
        "LTX-2.3 — Hugging Face"

    )

    # ========================================================
    # IMAGEM
    # ========================================================

    imagem = st.file_uploader(

        "🖼️ Imagem opcional",

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

            caption=
                "Imagem de entrada",

            use_container_width=
                True

        )

    # ========================================================
    # PROMPT
    # ========================================================

    prompt = st.text_area(

        "📝 Descrição do vídeo",

        value=(

            "O personagem começa a caminhar "
            "lentamente para frente. "

            "A câmera acompanha suavemente "
            "o personagem. "

            "Movimento cinematográfico natural "
            "e estável. "

            "Manter o mesmo personagem, "
            "rosto, cabelo, roupa, aparência "
            "e identidade durante toda a cena."

        ),

        height=
            180

    )

    # ========================================================
    # GERAR
    # ========================================================

    if st.button(

        "🎬 GERAR VÍDEO AUTOMATICAMENTE",

        type=
            "primary",

        use_container_width=
            True

    ):

        if not prompt.strip():

            st.warning(
                "⚠️ Digite uma descrição."
            )

            st.stop()

        try:

            imagem_bytes = (
                imagem.getvalue()
                if imagem
                else None
            )

            nome_imagem = (

                imagem.name
                if imagem
                else
                "imagem.png"

            )

            with st.spinner(

                "🤖 Escolhendo o melhor "
                "motor automaticamente..."

            ):

                resultado = (
                    gerar_video_automatico(

                        prompt=
                            prompt,

                        imagem_bytes=
                            imagem_bytes,

                        nome_imagem=
                            nome_imagem

                    )
                )

            # =================================================
            # RESULTADO
            # =================================================

            st.success(
                "🎉 VÍDEO GERADO COM SUCESSO!"
            )

            st.write(
                "🎬 Motor utilizado:"
            )

            st.code(
                resultado.get(
                    "motor",
                    "Desconhecido"
                )
            )

            st.video(
                resultado["video"]
            )

            # =================================================
            # FALLBACK
            # =================================================

            if resultado.get(
                "fallback"
            ):

                st.warning(

                    "⚠️ O primeiro motor "
                    "falhou.\n\n"

                    "O sistema ativou "
                    "automaticamente o "
                    "segundo motor."

                )

            # =================================================
            # SEED
            # =================================================

            if resultado.get(
                "seed"
            ) is not None:

                st.write(
                    "🎲 Seed utilizada:"
                )

                st.code(
                    str(
                        resultado[
                            "seed"
                        ]
                    )
                )

        except Exception as erro:

            st.error(
                "❌ Erro durante a geração."
            )

            st.code(
                str(
                    erro
                )
            )


# ============================================================
# ▶️ EXECUÇÃO DIRETA
# ============================================================

def mostrar_configuracao_video():
    st.subheader("🎬 Configuração de Vídeo")

    st.write("**Motores disponíveis:**")

    for motor in MOTORES_VIDEO:
        st.write(f"• {motor}")

    st.write("**Câmeras cinematográficas:**")

    for camera in CAMERAS:
        st.write(f"• {camera}")

    st.write("**Proporções disponíveis:**")

    for proporcao in PROPORCOES:
        st.write(f"• {proporcao}")

    st.write(
        f"**Duração padrão:** {DURACAO_PADRAO} segundos"
    )

if __name__ == "__main__":

    interface_teste()
