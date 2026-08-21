"""Alex IA Ultra - Gerenciador de Vídeo.

Motores:
1. Wan 2.2 14B FP8 — R3GM
2. Wan 2.2 14B I2V — Upsampler
3. LTX-2.3 — Hugging Face
4. Magic Hour — LTX-2.3
5. Kling 2.1 — Replicate (manual)

O R3GM e o Upsampler são Image-to-Video.
"""

from __future__ import annotations

import os
import time
import random
import base64
from pathlib import Path
from typing import Any, Optional

import streamlit as st
import requests

try:
    from gradio_client import Client, handle_file
except Exception:
    Client = None
    handle_file = None


# ============================================================
# CONFIGURAÇÃO
# ============================================================

NOME_MODULO = "Alex IA Ultra — Gerenciador de Vídeo"

DURACAO_PADRAO = 5

R3GM_SPACE = "r3gm/wan2-2-fp8da-aoti-preview"

UPSAMPLER_SPACE = "Upsampler/wan-2-2-14b-image-to-video"

LTX_HF_SPACE = "https://lightricks-ltx-2-3.hf.space"

MAGIC_HOUR_BASE_URL = "https://api.magichour.ai/v1"
MAGIC_HOUR_MODELO = "ltx-2.3"
MAGIC_HOUR_RESOLUCAO = "480p"
MAGIC_HOUR_DURACAO = 5


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


MOTORES_VIDEO = [
    "Wan 2.2 — R3GM",
    "Wan 2.2 — Upsampler",
    "LTX-2.3 — Hugging Face",
    "Magic Hour — LTX-2.3",
    "Kling 2.1 — Replicate",
]


PASTA = Path("videos_gerados")
PASTA.mkdir(parents=True, exist_ok=True)


# ============================================================
# UTILIDADES
# ============================================================

def _secret(nome: str) -> str:

    try:
        valor = st.secrets.get(nome, "")
    except Exception:
        valor = ""

    if not valor:
        valor = os.environ.get(nome, "")

    return str(valor or "").strip()


def obter_api_key_magichour() -> str:

    return _secret("MAGIC_HOUR_API_KEY")


def obter_token_replicate() -> str:

    return _secret("REPLICATE_API_TOKEN")


def headers_magichour() -> dict:

    chave = obter_api_key_magichour()

    if not chave:
        raise RuntimeError(
            "MAGIC_HOUR_API_KEY não foi encontrada."
        )

    return {
        "Authorization": f"Bearer {chave}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _nome_saida(prefixo: str) -> Path:

    return PASTA / (
        f"{prefixo}_{int(time.time() * 1000)}.mp4"
    )


# ============================================================
# PROMPT
# ============================================================

def montar_prompt(
    movimento: str,
    camera: str = "Sony FX6"
) -> str:

    return f"""
Animate the provided image into a realistic cinematic video.

Movement:
{movimento}

Camera:
{camera}

IMPORTANT:
Keep exactly the same character from the reference image.

Preserve:
- face
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

Natural realistic movement.
Smooth cinematic camera movement.
Realistic lighting.
Realistic physics.

The input image is the visual reference.
""".strip()


# ============================================================
# LOCALIZAR VÍDEO RETORNADO PELO GRADIO
# ============================================================

def _extrair_video_gradio(
    resultado: Any
) -> Optional[str]:

    if isinstance(resultado, str):

        if (
            resultado.startswith("http://")
            or resultado.startswith("https://")
            or resultado.lower().endswith(".mp4")
        ):
            return resultado

    if isinstance(resultado, dict):

        for chave in [
            "video",
            "output",
            "path",
            "url"
        ]:

            valor = resultado.get(chave)

            encontrado = _extrair_video_gradio(
                valor
            )

            if encontrado:
                return encontrado

    if isinstance(
        resultado,
        (list, tuple)
    ):

        for item in resultado:

            encontrado = _extrair_video_gradio(
                item
            )

            if encontrado:
                return encontrado

    return None


# ============================================================
# SALVAR / BAIXAR VÍDEO
# ============================================================

def _salvar_video_gradio(
    origem: str,
    destino: Path
) -> str:

    if Path(origem).exists():

        destino.write_bytes(
            Path(origem).read_bytes()
        )

    elif origem.startswith(
        ("http://", "https://")
    ):

        resposta = requests.get(
            origem,
            timeout=300
        )

        resposta.raise_for_status()

        destino.write_bytes(
            resposta.content
        )

    else:

        raise RuntimeError(
            f"Vídeo não acessível: {origem}"
        )

    if (
        not destino.exists()
        or destino.stat().st_size == 0
    ):

        raise RuntimeError(
            "O vídeo retornado está vazio."
        )

    return str(destino)


# ============================================================
# MOTOR 1
# WAN 2.2 — R3GM
# ============================================================

def gerar_r3gm(
    imagem_bytes: bytes,
    nome_imagem: str,
    movimento: str,
    camera: str = "Sony FX6",
    duracao: float = 0.5
) -> dict:

    if Client is None:

        raise RuntimeError(
            "gradio_client não está instalado."
        )

    if handle_file is None:

        raise RuntimeError(
            "handle_file não está disponível."
        )

    if not imagem_bytes:

        raise ValueError(
            "O R3GM precisa de uma imagem."
        )

    if not movimento:

        raise ValueError(
            "O movimento está vazio."
        )

    extensao = Path(
        nome_imagem
    ).suffix.lower()

    if extensao not in [
        ".png",
        ".jpg",
        ".jpeg",
        ".webp"
    ]:

        extensao = ".jpg"

    entrada = (
        PASTA
        / f"entrada_r3gm_{int(time.time()*1000)}"
        f"{extensao}"
    )

    entrada.write_bytes(
        imagem_bytes
    )

    prompt = montar_prompt(
        movimento,
        camera
    )

    seed = random.randint(
        0,
        2147483647
    )

    client = Client(
        R3GM_SPACE
    )

    resultado = client.predict(

        input_image=handle_file(
            str(entrada)
        ),

        last_image=None,

        prompt=prompt,

        steps=4,

        negative_prompt=(
            "static, blurry, low quality, "
            "distorted face, extra fingers, "
            "deformed hands, bad anatomy, "
            "duplicate person, duplicate body, "
            "text, subtitles, watermark"
        ),

        duration_seconds=max(
            0.5,
            min(
                float(duracao),
                10.0
            )
        ),

        guidance_scale=1.0,

        guidance_scale_2=1.0,

        seed=seed,

        randomize_seed=True,

        quality=5,

        scheduler="FlowMatchEulerDiscrete",

        flow_shift=6.0,

        frame_multiplier=16,

        video_component=True,

        safe_mode=True,

        enable_safety_checker=True,

        api_name="/generate_video"
    )

    video = _extrair_video_gradio(
        resultado
    )

    if not video:

        raise RuntimeError(
            "R3GM não retornou o vídeo."
        )

    destino = _nome_saida(
        "video_r3gm"
    )

    caminho = _salvar_video_gradio(
        video,
        destino
    )

    return {
        "sucesso": True,
        "motor": "Wan 2.2 — R3GM",
        "video": caminho,
        "arquivo": caminho,
        "fallback": False,
        "erro": None
    }


# ============================================================
# MOTOR 2
# WAN 2.2 — UPSAMPLER
# ============================================================

def gerar_upsampler(
    imagem_bytes: bytes,
    nome_imagem: str,
    movimento: str,
    camera: str = "Sony FX6",
    duracao: float = 3.5
) -> dict:

    if Client is None:

        raise RuntimeError(
            "gradio_client não está instalado."
        )

    if not imagem_bytes:

        raise ValueError(
            "O Upsampler precisa de uma imagem."
        )

    extensao = Path(
        nome_imagem
    ).suffix.lower()

    if extensao not in [
        ".png",
        ".jpg",
        ".jpeg",
        ".webp"
    ]:

        extensao = ".jpg"

    entrada = (
        PASTA
        / f"entrada_upsampler_{int(time.time()*1000)}"
        f"{extensao}"
    )

    entrada.write_bytes(
        imagem_bytes
    )

    prompt = montar_prompt(
        movimento,
        camera
    )

    client = Client(
        UPSAMPLER_SPACE
    )

    resultado = client.predict(

        input_image=handle_file(
            str(entrada)
        ),

        last_image=None,

        prompt=prompt,

        steps=6,

        negative_prompt=(
            "static, blurry, low quality, "
            "distorted face, extra fingers, "
            "duplicate person, deformed body, "
            "text, subtitles, watermark"
        ),

        duration_seconds=max(
            0.5,
            min(
                float(duracao),
                5.0
            )
        ),

        guidance_scale=1.0,

        guidance_scale_2=1.0,

        seed=random.randint(
            0,
            2147483647
        ),

        randomize_seed=True,

        quality=5,

        scheduler="FlowMatchEulerDiscrete",

        flow_shift=6.0,

        frame_multiplier=16,

        video_component=True,

        safe_mode=True,

        enable_safety_checker=True,

        api_name="/generate_video"
    )

    video = _extrair_video_gradio(
        resultado
    )

    if not video:

        raise RuntimeError(
            "Upsampler não retornou o vídeo."
        )

    destino = _nome_saida(
        "video_upsampler"
    )

    caminho = _salvar_video_gradio(
        video,
        destino
    )

    return {
        "sucesso": True,
        "motor": "Wan 2.2 — Upsampler",
        "video": caminho,
        "arquivo": caminho,
        "fallback": True,
        "erro": None
    }


# ============================================================
# LTX 2.3 — HUGGING FACE
# ============================================================

def gerar_ltx_huggingface(
    prompt: str,
    duration: float = 1.0,
    height: int = 512,
    width: int = 512,
    imagem_bytes: Optional[bytes] = None,
    nome_imagem: str = "imagem.png"
) -> dict:

    if Client is None:

        raise RuntimeError(
            "gradio_client não está instalado."
        )

    if not prompt:

        raise ValueError(
            "O prompt está vazio."
        )

    caminho_imagem = None

    if imagem_bytes:

        ext = (
            Path(nome_imagem)
            .suffix
            .lower()
            or ".png"
        )

        caminho_imagem = (
            PASTA
            / f"entrada_ltx_{int(time.time()*1000)}"
            f"{ext}"
        )

        caminho_imagem.write_bytes(
            imagem_bytes
        )

    client = Client(
        LTX_HF_SPACE
    )

    resultado = client.predict(

        input_image=(
            str(caminho_imagem)
            if caminho_imagem
            else None
        ),

        prompt=prompt.strip(),

        duration=float(
            duration
        ),

        enhance_prompt=True,

        seed=0,

        randomize_seed=True,

        height=int(height),

        width=int(width),

        api_name="/generate_video"
    )

    video = (
        resultado[0]
        if isinstance(
            resultado,
            (tuple, list)
        )
        else resultado
    )

    if not video:

        raise RuntimeError(
            "LTX não retornou vídeo."
        )

    return {
        "sucesso": True,
        "motor": "LTX-2.3 — Hugging Face",
        "video": str(video),
        "arquivo": str(video),
        "fallback": True,
        "erro": None
    }


# ============================================================
# MAGIC HOUR
# ============================================================

def obter_url_upload(
    extensao: str
):

    ext = (
        str(extensao)
        .lower()
        .replace(".", "")
    )

    resposta = requests.post(

        f"{MAGIC_HOUR_BASE_URL}"
        "/files/upload-urls",

        headers=headers_magichour(),

        json={
            "items": [
                {
                    "type": "image",
                    "extension": ext
                }
            ]
        },

        timeout=60
    )

    if resposta.status_code != 200:

        raise RuntimeError(
            f"Magic Hour HTTP "
            f"{resposta.status_code}: "
            f"{resposta.text}"
        )

    dados = resposta.json()

    itens = dados.get(
        "items"
    ) or []

    if not itens:

        raise RuntimeError(
            "Magic Hour não retornou upload."
        )

    item = itens[0]

    return (
        item["upload_url"],
        item["file_path"]
    )


def enviar_imagem_magichour(
    imagem_bytes: bytes,
    nome: str
) -> str:

    ext = (
        Path(nome)
        .suffix
        .lower()
        .replace(".", "")
        or "png"
    )

    upload_url, file_path = (
        obter_url_upload(ext)
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
            "Falha no upload Magic Hour."
        )

    return file_path


def gerar_magichour(
    imagem_bytes: bytes,
    nome_arquivo: str,
    prompt: str
) -> dict:

    if not imagem_bytes:

        raise ValueError(
            "Magic Hour precisa de imagem."
        )

    file_path = (
        enviar_imagem_magichour(
            imagem_bytes,
            nome_arquivo
        )
    )

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
                prompt
        },

        "assets": {
            "image_file_path":
                file_path
        }
    }

    resposta = requests.post(

        f"{MAGIC_HOUR_BASE_URL}"
        "/image-to-video",

        headers=headers_magichour(),

        json=dados,

        timeout=120
    )

    if resposta.status_code not in [
        200,
        201,
        202
    ]:

        raise RuntimeError(
            f"Magic Hour HTTP "
            f"{resposta.status_code}: "
            f"{resposta.text}"
        )

    resultado = resposta.json()

    projeto = resultado.get(
        "id"
    )

    if not projeto:

        raise RuntimeError(
            "Magic Hour não retornou ID."
        )

    inicio = time.time()

    while time.time() - inicio < 300:

        resposta = requests.get(

            f"{MAGIC_HOUR_BASE_URL}"
            f"/video-projects/{projeto}",

            headers=headers_magichour(),

            timeout=60
        )

        if resposta.status_code == 200:

            dados = resposta.json()

            url = encontrar_url_video(
                dados
            )

            if url:

                video = requests.get(
                    url,
                    timeout=180
                )

                video.raise_for_status()

                caminho = _nome_saida(
                    "video_magichour"
                )

                caminho.write_bytes(
                    video.content
                )

                return {
                    "sucesso": True,
                    "motor":
                        "Magic Hour — LTX-2.3",
                    "video":
                        str(caminho),
                    "arquivo":
                        str(caminho),
                    "fallback":
                        True,
                    "erro":
                        None
                }

        time.sleep(5)

    raise RuntimeError(
        "Magic Hour demorou demais."
    )


def encontrar_url_video(
    dados: Any
) -> Optional[str]:

    if not isinstance(
        dados,
        dict
    ):

        return None

    for chave in [
        "video_url",
        "download_url",
        "output_url",
        "url"
    ]:

        valor = dados.get(
            chave
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

    return None


# ============================================================
# GERADOR PRINCIPAL COM FALLBACK
# ============================================================

def gerar_video_automatico(
    prompt: Optional[str] = None,
    imagem_bytes: Optional[bytes] = None,
    nome_imagem: str = "imagem.png",
    duracao: float = 5.0,
    width: int = 512,
    height: int = 512,
    descricao: Optional[str] = None,
    camera: str = "Sony FX6",
    proporcao: str = "16:9",
    **kwargs
) -> dict:

    texto = (
        prompt
        or descricao
        or ""
    ).strip()

    if not texto:

        return {
            "sucesso":
                False,
            "video":
                None,
            "motor":
                None,
            "erro":
                "O movimento está vazio."
        }

    erros = []

    # --------------------------------------------------------
    # 1 — R3GM
    # --------------------------------------------------------

    if imagem_bytes:

        try:

            return gerar_r3gm(

                imagem_bytes,

                nome_imagem,

                texto,

                camera,

                duracao

            )

        except Exception as erro:

            erros.append(
                "R3GM: "
                + str(erro)
            )

    # --------------------------------------------------------
    # 2 — UPSAMPLER
    # --------------------------------------------------------

    if imagem_bytes:

        try:

            resultado = gerar_upsampler(

                imagem_bytes,

                nome_imagem,

                texto,

                camera,

                duracao

            )

            resultado[
                "erros_anteriores"
            ] = erros

            return resultado

        except Exception as erro:

            erros.append(
                "Upsampler: "
                + str(erro)
            )

    # --------------------------------------------------------
    # 3 — MAGIC HOUR
    # --------------------------------------------------------

    if imagem_bytes:

        try:

            resultado = gerar_magichour(

                imagem_bytes,

                nome_imagem,

                montar_prompt(
                    texto,
                    camera
                )

            )

            resultado[
                "erros_anteriores"
            ] = erros

            return resultado

        except Exception as erro:

            erros.append(
                "Magic Hour: "
                + str(erro)
            )

    # --------------------------------------------------------
    # 4 — LTX
    # --------------------------------------------------------

    try:

        resultado = gerar_ltx_huggingface(

            montar_prompt(
                texto,
                camera
            ),

            duration=min(
                float(duracao),
                5.0
            ),

            height=height,

            width=width,

            imagem_bytes=imagem_bytes,

            nome_imagem=nome_imagem
        )

        resultado[
            "erros_anteriores"
        ] = erros

        return resultado

    except Exception as erro:

        erros.append(
            "LTX-2.3: "
            + str(erro)
        )

    return {

        "sucesso":
            False,

        "video":
            None,

        "motor":
            None,

        "erro":
            "❌ NENHUM MOTOR DE VÍDEO "
            "CONSEGUIU GERAR O VÍDEO.\n\n"
            + "\n\n".join(erros),

        "erros":
            erros
    }


# ============================================================
# FUNÇÕES COMPATÍVEIS COM APP.PY
# ============================================================

def gerar_video(
    prompt: Optional[str] = None,
    imagem_bytes: Optional[bytes] = None,
    nome_imagem: str = "imagem.png",
    duracao: float = 5.0,
    width: int = 512,
    height: int = 512,
    descricao: Optional[str] = None,
    **kwargs
) -> dict:

    return gerar_video_automatico(

        prompt=prompt,

        imagem_bytes=imagem_bytes,

        nome_imagem=nome_imagem,

        duracao=duracao,

        width=width,

        height=height,

        descricao=descricao,

        **kwargs
    )


def gerar_video_texto(
    prompt: str,
    duracao: float = 1.0,
    **kwargs
) -> dict:

    return gerar_ltx_huggingface(
        prompt,
        duration=duracao,
        **kwargs
    )


def gerar_video_imagem(
    imagem_bytes: bytes,
    nome_imagem: str,
    prompt: str,
    duracao: float = 5.0,
    **kwargs
) -> dict:

    return gerar_video(

        prompt,

        imagem_bytes=imagem_bytes,

        nome_imagem=nome_imagem,

        duracao=duracao,

        **kwargs
    )


def gerar(
    prompt: str,
    **kwargs
) -> dict:

    return gerar_video(
        prompt,
        **kwargs
    )


def gerar_video_fallback(
    prompt: str,
    **kwargs
) -> Optional[str]:

    resultado = gerar_video(
        prompt,
        **kwargs
    )

    return (
        resultado.get("video")
        or
        resultado.get("arquivo")
    )


# ============================================================
# CONFIGURAÇÃO DO APP.PY
# ============================================================

def mostrar_configuracao_video():

    st.subheader(
        "🎬 Configuração de Vídeo"
    )

    camera_video = st.selectbox(

        "📷 Câmera",

        CAMERAS,

        index=1,

        key="video_camera"
    )

    proporcao_video = st.selectbox(

        "📐 Proporção",

        PROPORCOES,

        index=1,

        key="video_proporcao"
    )

    duracao_video = st.number_input(

        "⏱️ Duração do vídeo",

        min_value=0.5,

        max_value=10.0,

        value=5.0,

        step=0.5,

        key="video_duracao"
    )

    st.write(
        "**🎥 Motores disponíveis:**"
    )

    for motor in MOTORES_VIDEO:

        st.write(
            f"• {motor}"
        )

    return (
        camera_video,
        proporcao_video,
        duracao_video
    )


# ============================================================
# STATUS
# ============================================================

def verificar_magic_hour():

    try:

        chave = (
            obter_api_key_magichour()
        )

        if chave:

            return (
                True,
                "✅ MAGIC_HOUR_API_KEY encontrada."
            )

        return (
            False,
            "❌ MAGIC_HOUR_API_KEY não encontrada."
        )

    except Exception as erro:

        return (
            False,
            f"❌ Erro: {erro}"
        )


def status_video() -> dict:

    return {

        "r3gm":
            R3GM_SPACE,

        "upsampler":
            UPSAMPLER_SPACE,

        "gradio_client":
            Client is not None,

        "magic_hour":
            bool(
                obter_api_key_magichour()
            ),

        "replicate":
            bool(
                obter_token_replicate()
            ),

        "ltx":
            LTX_HF_SPACE
    }


# ============================================================
# EXPORTAÇÕES
# ============================================================

__all__ = [

    "NOME_MODULO",

    "MOTORES_VIDEO",

    "CAMERAS",

    "PROPORCOES",

    "DURACAO_PADRAO",

    "gerar_video",

    "gerar_video_automatico",

    "gerar_video_fallback",

    "gerar",

    "gerar_video_texto",

    "gerar_video_imagem",

    "gerar_r3gm",

    "gerar_upsampler",

    "gerar_ltx_huggingface",

    "gerar_magichour",

    "gerar_video_replicate",

    "mostrar_configuracao_video",

    "verificar_magic_hour",

    "obter_api_key_magichour",

    "obter_token_replicate",

    "status_video"
]
