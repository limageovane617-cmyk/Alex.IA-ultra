import os
import random
import base64
import time
from pathlib import Path
import requests

try:
    from gradio_client import Client, handle_file
except ImportError:
    Client = None
    handle_file = None


# ============================================================
# CONFIGURAÇÃO
# ============================================================

PASTA_VIDEOS = Path("videos")
PASTA_VIDEOS.mkdir(parents=True, exist_ok=True)

R3GM_SPACE = "r3gm/wan2-2-fp8da-aoti-preview"
UPSAMPLER_SPACE = "Upsampler/wan-2-2-14b-image-to-video"

MOTORES_VIDEO = [
    "Wan 2.2 — R3GM (Hugging Face)",
    "Wan 2.2 — Upsampler (Hugging Face)",
    "Kling 2.1 — Replicate"
]

CAMERAS = [
    "Sony FX5",
    "Sony FX6",
    "Canon EOS C80",
    "ARRI Alexa Mini LF"
]

PROPORCOES = [
    "16:9",
    "9:16",
    "1:1"
]

DURACAO_PADRAO = 0.5


# ============================================================
# LISTAS
# ============================================================

def listar_motores():
    return MOTORES_VIDEO


def listar_cameras():
    return CAMERAS


def listar_proporcoes():
    return PROPORCOES


# ============================================================
# PROMPT
# ============================================================

def montar_prompt(movimento, camera="Sony FX6"):

    return f"""
Animate the provided image into a realistic cinematic video.

Movement:
{movimento}

Camera:
{camera}

Keep the exact same character from the reference image.

Preserve:
- exact face
- hairstyle
- clothing
- body
- accessories
- colors
- identity

Do not create another character.
Do not change the clothes.
Do not change the face.
Do not change the hairstyle.
Do not duplicate the character.
Do not add another person.

Use natural realistic movement.
Smooth cinematic camera movement.
Realistic lighting and physics.

The image is the visual reference.
"""


# ============================================================
# LER IMAGEM
# ============================================================

def ler_imagem(imagem):

    if hasattr(imagem, "getvalue"):

        dados = imagem.getvalue()
        nome = getattr(
            imagem,
            "name",
            "imagem.jpg"
        )

        return dados, nome

    if isinstance(imagem, bytes):

        return imagem, "imagem.jpg"

    caminho = Path(str(imagem))

    if not caminho.exists():

        raise FileNotFoundError(
            f"Imagem não encontrada: {caminho}"
        )

    return (
        caminho.read_bytes(),
        caminho.name
    )


# ============================================================
# TESTE DO R3GM
# ============================================================

def testar_r3gm(
    imagem,
    movimento,
    camera="Sony FX6",
    duracao=0.5,
    steps=4,
    nome_arquivo="teste_r3gm.mp4"
):
    """
    TESTE DIRETO DO MOTOR R3GM.

    Esse é o mesmo motor que já foi testado
    e conseguiu gerar vídeo.
    """

    if Client is None or handle_file is None:

        raise RuntimeError(
            "gradio_client não está instalado."
        )

    dados, nome = ler_imagem(imagem)

    extensao = Path(nome).suffix.lower()

    if extensao not in [
        ".png",
        ".jpg",
        ".jpeg",
        ".webp"
    ]:

        extensao = ".jpg"

    arquivo = (
        PASTA_VIDEOS /
        f"_entrada_r3gm{extensao}"
    )

    arquivo.write_bytes(dados)

    prompt = montar_prompt(
        movimento,
        camera
    )

    seed = random.randint(
        0,
        2147483647
    )

    cliente = Client(
        R3GM_SPACE
    )

    resultado = cliente.predict(

        input_image=handle_file(
            str(arquivo)
        ),

        last_image=None,

        prompt=prompt,

        steps=int(steps),

        negative_prompt=(
            "static, blurry, low quality, "
            "distorted face, extra fingers, "
            "deformed hands, duplicate person, "
            "duplicate body, bad anatomy, "
            "text, subtitles, watermark"
        ),

        duration_seconds=float(
            max(
                0.5,
                min(float(duracao), 10.0)
            )
        ),

        guidance_scale=1.0,

        guidance_scale_2=1.0,

        seed=seed,

        randomize_seed=True,

        quality=5,

        scheduler="UniPCMultistep",

        flow_shift=6.0,

        frame_multiplier=16,

        video_component=True,

        safe_mode=True,

        enable_safety_checker=True,

        api_name="/generate_video"
    )

    return salvar_video_gradio(
        resultado,
        PASTA_VIDEOS / nome_arquivo
    )


# ============================================================
# LOCALIZAR VÍDEO DO GRADIO
# ============================================================

def extrair_video(resultado):

    if isinstance(
        resultado,
        dict
    ):

        output = resultado.get(
            "output"
        )

        if isinstance(
            output,
            dict
        ):

            video = output.get(
                "video"
            )

            if isinstance(
                video,
                dict
            ):

                return (
                    video.get("path")
                    or video.get("url")
                )

            if isinstance(
                video,
                str
            ):

                return video

        video = resultado.get(
            "video"
        )

        if isinstance(
            video,
            dict
        ):

            return (
                video.get("path")
                or video.get("url")
            )

        if isinstance(
            video,
            str
        ):

            return video

    if isinstance(
        resultado,
        (list, tuple)
    ):

        for item in resultado:

            encontrado = extrair_video(
                item
            )

            if encontrado:

                return encontrado

            if isinstance(
                item,
                str
            ):

                if (
                    item.startswith(
                        "http://"
                    )
                    or
                    item.startswith(
                        "https://"
                    )
                    or
                    item.lower().endswith(
                        ".mp4"
                    )
                ):

                    return item

    if isinstance(
        resultado,
        str
    ):

        if (
            resultado.startswith(
                "http://"
            )
            or
            resultado.startswith(
                "https://"
            )
            or
            resultado.lower().endswith(
                ".mp4"
            )
        ):

            return resultado

    return None


# ============================================================
# SALVAR VÍDEO
# ============================================================

def salvar_video_gradio(
    resultado,
    destino
):

    caminho = extrair_video(
        resultado
    )

    if not caminho:

        raise RuntimeError(
            "O R3GM respondeu, mas "
            "não foi encontrado um vídeo."
        )

    caminho = str(caminho)

    if Path(caminho).exists():

        destino.write_bytes(
            Path(caminho).read_bytes()
        )

    elif caminho.startswith(
        ("http://", "https://")
    ):

        resposta = requests.get(
            caminho,
            timeout=300
        )

        resposta.raise_for_status()

        destino.write_bytes(
            resposta.content
        )

    else:

        raise RuntimeError(
            f"Vídeo não acessível: {caminho}"
        )

    if (
        not destino.exists()
        or
        destino.stat().st_size == 0
    ):

        raise RuntimeError(
            "O vídeo está vazio."
        )

    return str(destino)


# ============================================================
# MOTOR R3GM
# ============================================================

def gerar_video_r3gm(
    imagem,
    movimento,
    camera="Sony FX6",
    proporcao="16:9",
    duracao=0.5,
    nome_arquivo="video_r3gm.mp4"
):

    return testar_r3gm(
        imagem=imagem,
        movimento=movimento,
        camera=camera,
        duracao=duracao,
        steps=4,
        nome_arquivo=nome_arquivo
    )


# ============================================================
# UPSAMPLER — FALLBACK
# ============================================================

def gerar_video_upsampler(
    imagem,
    movimento,
    camera="Sony FX6",
    proporcao="16:9",
    duracao=0.5,
    nome_arquivo="video_upsampler.mp4"
):

    if Client is None:

        raise RuntimeError(
            "gradio_client não está instalado."
        )

    dados, nome = ler_imagem(
        imagem
    )

    extensao = Path(
        nome
    ).suffix.lower()

    if extensao not in [
        ".png",
        ".jpg",
        ".jpeg",
        ".webp"
    ]:

        extensao = ".jpg"

    arquivo = (
        PASTA_VIDEOS /
        f"_entrada_upsampler{extensao}"
    )

    arquivo.write_bytes(
        dados
    )

    prompt = montar_prompt(
        movimento,
        camera
    )

    cliente = Client(
        UPSAMPLER_SPACE
    )

    erros = []

    try:

        resultado = cliente.predict(

            input_image=handle_file(
                str(arquivo)
            ),

            prompt=prompt,

            duration_seconds=float(
                max(
                    0.5,
                    min(float(duracao), 5.0)
                )
            ),

            api_name="/generate"
        )

        return salvar_video_gradio(
            resultado,
            PASTA_VIDEOS /
            nome_arquivo
        )

    except Exception as erro:

        erros.append(
            str(erro)
        )

    try:

        resultado = cliente.predict(

            handle_file(
                str(arquivo)
            ),

            prompt,

            api_name="/generate"
        )

        return salvar_video_gradio(
            resultado,
            PASTA_VIDEOS /
            nome_arquivo
        )

    except Exception as erro:

        erros.append(
            str(erro)
        )

    raise RuntimeError(
        "Upsampler não conseguiu gerar o vídeo:\n"
        + "\n".join(erros)
    )


# ============================================================
# REPLICATE
# ============================================================

def obter_token_replicate():

    token = os.getenv(
        "REPLICATE_API_TOKEN"
    )

    if not token:

        raise RuntimeError(
            "REPLICATE_API_TOKEN não foi encontrado."
        )

    return token


def gerar_video_replicate(
    imagem,
    movimento,
    camera="Sony FX6",
    proporcao="16:9",
    duracao=5,
    nome_arquivo="video_kling.mp4"
):

    token = obter_token_replicate()

    prompt = montar_prompt(
        movimento,
        camera
    )

    imagem_bytes, nome = ler_imagem(
        imagem
    )

    imagem_base64 = base64.b64encode(
        imagem_bytes
    ).decode(
        "utf-8"
    )

    if nome.lower().endswith(
        ".png"
    ):

        mime = "image/png"

    elif nome.lower().endswith(
        ".webp"
    ):

        mime = "image/webp"

    else:

        mime = "image/jpeg"

    imagem_url = (
        f"data:{mime};base64,"
        f"{imagem_base64}"
    )

    headers = {

        "Authorization":
            f"Bearer {token}",

        "Content-Type":
            "application/json"
    }

    dados = {

        "input": {

            "prompt":
                prompt,

            "start_image":
                imagem_url,

            "duration":
                min(
                    int(duracao),
                    5
                ),

            "aspect_ratio":
                proporcao
        }
    }

    url = (
        "https://api.replicate.com/v1/models/"
        "kwaivgi/kling-v2.1/predictions"
    )

    resposta = requests.post(
        url,
        headers=headers,
        json=dados,
        timeout=60
    )

    if resposta.status_code >= 400:

        raise RuntimeError(
            "Erro ao iniciar o Replicate:\n"
            + resposta.text
        )

    operacao = resposta.json()

    prediction_url = (
        operacao
        .get("urls", {})
        .get("get")
    )

    if not prediction_url:

        raise RuntimeError(
            "Replicate não retornou "
            "a URL da operação."
        )

    for _ in range(120):

        resposta = requests.get(

            prediction_url,

            headers={
                "Authorization":
                    f"Bearer {token}"
            },

            timeout=60
        )

        if resposta.status_code >= 400:

            raise RuntimeError(
                "Erro consultando Replicate:\n"
                + resposta.text
            )

        resultado = resposta.json()

        status = resultado.get(
            "status"
        )

        if status == "succeeded":

            break

        if status in [
            "failed",
            "canceled"
        ]:

            raise RuntimeError(
                "Geração falhou: "
                + str(
                    resultado.get(
                        "error",
                        "Erro desconhecido."
                    )
                )
            )

        time.sleep(3)

    else:

        raise RuntimeError(
            "Replicate demorou demais."
        )

    saida = resultado.get(
        "output"
    )

    if not saida:

        raise RuntimeError(
            "Replicate terminou sem vídeo."
        )

    video_url = (
        saida[0]
        if isinstance(
            saida,
            list
        )
        else saida
    )

    caminho = (
        PASTA_VIDEOS /
        nome_arquivo
    )

    video = requests.get(
        video_url,
        timeout=180
    )

    if video.status_code != 200:

        raise RuntimeError(
            "Não foi possível baixar o vídeo."
        )

    caminho.write_bytes(
        video.content
    )

    return str(caminho)


# ============================================================
# GERADOR PRINCIPAL — FALLBACK
# ============================================================

def gerar_video(
    imagem,
    movimento,
    camera="Sony FX6",
    proporcao="16:9",
    duracao=0.5,
    nome_arquivo="video.mp4"
):

    erros = []

    # --------------------------------------------------------
    # 1 — R3GM
    # --------------------------------------------------------

    try:

        caminho = gerar_video_r3gm(

            imagem=imagem,

            movimento=movimento,

            camera=camera,

            proporcao=proporcao,

            duracao=duracao,

            nome_arquivo=nome_arquivo
        )

        return {

            "sucesso": True,

            "motor":
                "Wan 2.2 — R3GM (Hugging Face)",

            "caminho":
                caminho
        }

    except Exception as erro:

        erros.append(
            "R3GM: "
            + str(erro)
        )

    # --------------------------------------------------------
    # 2 — UPSAMPLER
    # --------------------------------------------------------

    try:

        caminho = gerar_video_upsampler(

            imagem=imagem,

            movimento=movimento,

            camera=camera,

            proporcao=proporcao,

            duracao=duracao,

            nome_arquivo=nome_arquivo
        )

        return {

            "sucesso": True,

            "motor":
                "Wan 2.2 — Upsampler (Hugging Face)",

            "caminho":
                caminho
        }

    except Exception as erro:

        erros.append(
            "Upsampler: "
            + str(erro)
        )

    # --------------------------------------------------------
    # NÃO CHAMAMOS REPLICATE AUTOMATICAMENTE
    # --------------------------------------------------------

    raise RuntimeError(
        "Nenhum motor gratuito conseguiu gerar o vídeo.\n\n"
        + "\n".join(erros)
        + "\n\n"
        "O Replicate não foi chamado porque sua conta "
        "está sem crédito."
    )


# ============================================================
# COMPATIBILIDADE
# ============================================================

def gerar_video_com_fallback(
    imagem,
    movimento,
    camera="Sony FX6",
    proporcao="16:9",
    duracao=0.5,
    nome_arquivo="video.mp4"
):

    return gerar_video(
        imagem=imagem,
        movimento=movimento,
        camera=camera,
        proporcao=proporcao,
        duracao=duracao,
        nome_arquivo=nome_arquivo
  )
