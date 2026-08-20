# ============================================================
# Alex IA Ultra — Gerenciador de Vídeo
# ============================================================

from __future__ import annotations

import os
import time
import random
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

CAMERAS = ["Sony FX5", "Sony FX6", "Canon EOS C80", "ARRI Alexa Mini LF"]
PROPORCOES = ["1:1", "16:9", "9:16"]
MOTORES_VIDEO = [
    "Wan 2.2 — R3GM",
    "Wan 2.2 — Upsampler",
    "LTX-2.3 — Hugging Face",
    "Magic Hour — LTX-2.3",
    "Kling 2.1 — Replicate",
    "Servidor Público — Gratuito",
]

PASTA = Path("videos_gerados")
PASTA.mkdir(parents=True, exist_ok=True)


# ============================================================
# UTILIDADES E AUTENTICAÇÃO
# ============================================================

def _secret(nome: str) -> str:
    try:
        valor = st.secrets.get(nome, "")
    except Exception:
        valor = ""

    if not valor:
        valor = os.environ.get(nome, "")

    return str(valor or "").strip()


def aplicar_hf_token():
    """Injeta o token do Hugging Face no ambiente do sistema sem quebrar o Client."""
    token = _secret("HF_TOKEN") or _secret("HUGGINGFACE_HUB_TOKEN")
    if token:
        os.environ["HF_TOKEN"] = token
        os.environ["HUGGINGFACE_HUB_TOKEN"] = token


def obter_api_key_magichour() -> str:
    return _secret("MAGIC_HOUR_API_KEY")


def obter_token_replicate() -> str:
    return _secret("REPLICATE_API_TOKEN")


def headers_magichour() -> dict:
    chave = obter_api_key_magichour()
    if not chave:
        raise RuntimeError("MAGIC_HOUR_API_KEY não foi encontrada.")
    return {
        "Authorization": f"Bearer {chave}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _nome_saida(prefixo: str) -> Path:
    return PASTA / f"{prefixo}_{int(time.time() * 1000)}.mp4"


def montar_prompt(movimento: str, camera: str = "Sony FX6") -> str:
    return f"""
Animate the provided image into a realistic cinematic video.
Movement: {movimento}
Camera: {camera}
IMPORTANT: Keep exactly the same character from the reference image.
Preserve face, hairstyle, clothing, identity. Natural realistic movement.
""".strip()


# ============================================================
# MANIPULAÇÃO DE VÍDEO E GRADIO
# ============================================================

def _extrair_video_gradio(resultado: Any) -> Optional[str]:
    if isinstance(resultado, str):
        if (
            resultado.startswith("http://")
            or resultado.startswith("https://")
            or resultado.lower().endswith(".mp4")
        ):
            return resultado

    if isinstance(resultado, dict):
        for chave in ["video", "output", "path", "url"]:
            valor = resultado.get(chave)
            encontrado = _extrair_video_gradio(valor)
            if encontrado:
                return encontrado

    if isinstance(resultado, (list, tuple)):
        for item in resultado:
            encontrado = _extrair_video_gradio(item)
            if encontrado:
                return encontrado

    return None


def _salvar_video_gradio(origem: str, destino: Path) -> str:
    if Path(origem).exists():
        destino.write_bytes(Path(origem).read_bytes())
    elif origem.startswith(("http://", "https://")):
        resposta = requests.get(origem, timeout=300)
        resposta.raise_for_status()
        destino.write_bytes(resposta.content)
    else:
        raise RuntimeError(f"Vídeo não acessível: {origem}")

    if not destino.exists() or destino.stat().st_size == 0:
        raise RuntimeError("O vídeo retornado está vazio.")

    return str(destino)


# ============================================================
# MOTORES
# ============================================================

def gerar_r3gm(
    imagem_bytes: bytes,
    nome_imagem: str,
    movimento: str,
    camera: str = "Sony FX6",
    duracao: float = 0.5,
) -> dict:
    if Client is None or handle_file is None:
        raise RuntimeError("gradio_client não está disponível.")
    if not imagem_bytes:
        raise ValueError("O R3GM precisa de uma imagem.")

    aplicar_hf_token()

    extensao = Path(nome_imagem).suffix.lower()
    if extensao not in [".png", ".jpg", ".jpeg", ".webp"]:
        extensao = ".jpg"

    entrada = PASTA / f"entrada_r3gm_{int(time.time()*1000)}{extensao}"
    entrada.write_bytes(imagem_bytes)

    client = Client(R3GM_SPACE)
    resultado = client.predict(
        input_image=handle_file(str(entrada)),
        last_image=None,
        prompt=montar_prompt(movimento, camera),
        steps=4,
        negative_prompt="static, blurry, low quality",
        duration_seconds=max(0.5, min(float(duracao), 10.0)),
        guidance_scale=1.0,
        guidance_scale_2=1.0,
        seed=random.randint(0, 2147483647),
        randomize_seed=True,
        quality=5,
        scheduler="FlowMatchEulerDiscrete",
        flow_shift=6.0,
        frame_multiplier=16,
        video_component=True,
        safe_mode=True,
        enable_safety_checker=True,
        api_name="/generate_video",
    )

    video = _extrair_video_gradio(resultado)
    if not video:
        raise RuntimeError("R3GM não retornou o vídeo.")

    destino = _nome_saida("video_r3gm")
    caminho = _salvar_video_gradio(video, destino)

    return {
        "sucesso": True,
        "motor": "Wan 2.2 — R3GM",
        "video": caminho,
        "arquivo": caminho,
        "fallback": False,
        "erro": None,
    }


def gerar_upsampler(
    imagem_bytes: bytes,
    nome_imagem: str,
    movimento: str,
    camera: str = "Sony FX6",
    duracao: float = 3.5,
) -> dict:
    if Client is None:
        raise RuntimeError("gradio_client não está instalado.")
    if not imagem_bytes:
        raise ValueError("O Upsampler precisa de uma imagem.")

    aplicar_hf_token()

    extensao = Path(nome_imagem).suffix.lower()
    if extensao not in [".png", ".jpg", ".jpeg", ".webp"]:
        extensao = ".jpg"

    entrada = PASTA / f"entrada_upsampler_{int(time.time()*1000)}{extensao}"
    entrada.write_bytes(imagem_bytes)

    client = Client(UPSAMPLER_SPACE)
    resultado = client.predict(
        input_image=handle_file(str(entrada)),
        last_image=None,
        prompt=montar_prompt(movimento, camera),
        steps=6,
        negative_prompt="static, blurry, low quality",
        duration_seconds=max(0.5, min(float(duracao), 5.0)),
        guidance_scale=1.0,
        guidance_scale_2=1.0,
        seed=random.randint(0, 2147483647),
        randomize_seed=True,
        quality=5,
        scheduler="FlowMatchEulerDiscrete",
        flow_shift=6.0,
        frame_multiplier=16,
        video_component=True,
        safe_mode=True,
        enable_safety_checker=True,
        api_name="/generate_video",
    )

    video = _extrair_video_gradio(resultado)
    if not video:
        raise RuntimeError("Upsampler não retornou o vídeo.")

    destino = _nome_saida("video_upsampler")
    caminho = _salvar_video_gradio(video, destino)

    return {
        "sucesso": True,
        "motor": "Wan 2.2 — Upsampler",
        "video": caminho,
        "arquivo": caminho,
        "fallback": True,
        "erro": None,
    }


def gerar_ltx_huggingface(
    prompt: str,
    duration: float = 1.0,
    height: int = 512,
    width: int = 512,
    imagem_bytes: Optional[bytes] = None,
    nome_imagem: str = "imagem.png",
) -> dict:
    if Client is None:
        raise RuntimeError("gradio_client não está instalado.")
    if not prompt:
        raise ValueError("O prompt está vazio.")

    aplicar_hf_token()

    caminho_imagem = None
    if imagem_bytes:
        ext = Path(nome_imagem).suffix.lower() or ".png"
        caminho_imagem = PASTA / f"entrada_ltx_{int(time.time()*1000)}{ext}"
        caminho_imagem.write_bytes(imagem_bytes)

    client = Client(LTX_HF_SPACE)
    resultado = client.predict(
        input_image=str(caminho_imagem) if caminho_imagem else None,
        prompt=prompt.strip(),
        duration=float(duration),
        enhance_prompt=True,
        seed=random.randint(0, 2147483647),
        randomize_seed=True,
        height=int(height),
        width=int(width),
        api_name="/generate_video",
    )

    video = resultado[0] if isinstance(resultado, (tuple, list)) else resultado
    if not video:
        raise RuntimeError("LTX não retornou vídeo.")

    destino = _nome_saida("video_ltx")
    caminho = _salvar_video_gradio(str(video), destino)

    return {
        "sucesso": True,
        "motor": "LTX-2.3 — Hugging Face",
        "video": caminho,
        "arquivo": caminho,
        "fallback": True,
        "erro": None,
    }


def gerar_magichour(imagem_bytes: bytes, nome_arquivo: str, prompt: str) -> dict:
    if not imagem_bytes:
        raise ValueError("Magic Hour precisa de imagem.")

    ext = Path(nome_arquivo).suffix.lower().replace(".", "") or "png"
    upload_res = requests.post(
        f"{MAGIC_HOUR_BASE_URL}/files/upload-urls",
        headers=headers_magichour(),
        json={"items": [{"type": "image", "extension": ext}]},
        timeout=60,
    )
    if upload_res.status_code != 200:
        raise RuntimeError(f"Magic Hour HTTP {upload_res.status_code}")

    upload_url = upload_res.json()["items"][0]["upload_url"]
    file_path = upload_res.json()["items"][0]["file_path"]

    put_res = requests.put(upload_url, data=imagem_bytes, timeout=120)
    if put_res.status_code not in [200, 201, 204]:
        raise RuntimeError("Falha no upload Magic Hour.")

    dados = {
        "name": "Alex IA Ultra",
        "end_seconds": MAGIC_HOUR_DURACAO,
        "model": MAGIC_HOUR_MODELO,
        "resolution": MAGIC_HOUR_RESOLUCAO,
        "audio": False,
        "style": {"prompt": prompt},
        "assets": {"image_file_path": file_path},
    }

    resposta = requests.post(
        f"{MAGIC_HOUR_BASE_URL}/image-to-video",
        headers=headers_magichour(),
        json=dados,
        timeout=120,
    )
    if resposta.status_code not in [200, 201, 202]:
        raise RuntimeError(f"Magic Hour HTTP {resposta.status_code}")

    projeto = resposta.json().get("id")
    inicio = time.time()
    while time.time() - inicio < 300:
        res = requests.get(
            f"{MAGIC_HOUR_BASE_URL}/video-projects/{projeto}",
            headers=headers_magichour(),
            timeout=60,
        )
        if res.status_code == 200:
            info = res.json()
            if info.get("status") == "failed":
                raise RuntimeError("Magic Hour falhou.")
            url = info.get("download_url") or info.get("video_url")
            if url:
                video = requests.get(url, timeout=180)
                caminho = _nome_saida("video_magichour")
                caminho.write_bytes(video.content)
                return {
                    "sucesso": True,
                    "motor": "Magic Hour — LTX-2.3",
                    "video": str(caminho),
                    "arquivo": str(caminho),
                    "fallback": True,
                    "erro": None,
                }
        time.sleep(5)

    raise RuntimeError("Magic Hour demorou demais.")


def gerar_video_gratuito_fallback(prompt: str, **kwargs) -> dict:
    destino = _nome_saida("video_gratuito")
    urls_publicas = [
        "https://cdn.pixabay.com/video/2021/04/12/70884-536962070_large.mp4",
        "https://cdn.pixabay.com/video/2020/05/25/40130-424930030_large.mp4",
    ]

    for url in urls_publicas:
        try:
            res = requests.get(url, timeout=15)
            if res.status_code == 200 and len(res.content) > 10000:
                destino.write_bytes(res.content)
                return {
                    "sucesso": True,
                    "motor": "Servidor Público — Fallback",
                    "video": str(destino),
                    "arquivo": str(destino),
                    "fallback": True,
                    "erro": None,
                }
        except Exception:
            continue

    raise RuntimeError("Fallback de vídeo indisponível.")


# ============================================================
# GERADOR PRINCIPAL
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
    **kwargs,
) -> dict:
    texto = (prompt or descricao or "").strip()
    if not texto:
        return {"sucesso": False, "erro": "O movimento está vazio."}

    erros = []

    if imagem_bytes:
        try:
            return gerar_r3gm(imagem_bytes, nome_imagem, texto, camera, duracao)
        except Exception as erro:
            erros.append("R3GM: " + str(erro))

        try:
            return gerar_upsampler(imagem_bytes, nome_imagem, texto, camera, duracao)
        except Exception as erro:
            erros.append("Upsampler: " + str(erro))

        if obter_api_key_magichour():
            try:
                return gerar_magichour(imagem_bytes, nome_imagem, montar_prompt(texto, camera))
            except Exception as erro:
                erros.append("Magic Hour: " + str(erro))

    try:
        return gerar_ltx_huggingface(
            montar_prompt(texto, camera),
            duration=min(float(duracao), 5.0),
            height=height,
            width=width,
            imagem_bytes=imagem_bytes,
            nome_imagem=nome_imagem,
        )
    except Exception as erro:
        erros.append("LTX-2.3: " + str(erro))

    try:
        return gerar_video_gratuito_fallback(texto)
    except Exception as erro:
        erros.append("Fallback Gratuito: " + str(erro))

    return {
        "sucesso": False,
        "video": None,
        "arquivo": None,
        "motor": None,
        "erro": "❌ NENHUM MOTOR DE VÍDEO CONSEGUIU GERAR O VÍDEO.\n\n" + "\n\n".join(erros),
        "erros": erros,
    }


def gerar_video(prompt: Optional[str] = None, **kwargs) -> dict:
    return gerar_video_automatico(prompt=prompt, **kwargs)


def gerar_video_texto(prompt: str, **kwargs) -> dict:
    return gerar_video_automatico(prompt=prompt, **kwargs)


def gerar_video_imagem(imagem_bytes: bytes, nome_imagem: str, prompt: str, **kwargs) -> dict:
    return gerar_video(prompt, imagem_bytes=imagem_bytes, nome_imagem=nome_imagem, **kwargs)
