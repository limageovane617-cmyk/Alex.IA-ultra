# ============================================================
# Alex IA Ultra — Gerenciador de Vídeo
# ============================================================

from __future__ import annotations

import io
import os
import random
import time
import urllib.parse
from pathlib import Path
from typing import Any, Optional

import requests
import streamlit as st
from PIL import Image, ImageDraw

try:
    import imageio
    import numpy as np

    IMAGEIO_AVAILABLE = True
except ImportError:
    IMAGEIO_AVAILABLE = False

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

SPACES_HF = [
    "r3gm/wan2-2-fp8da-aoti-preview",
    "Upsampler/wan-2-2-14b-image-to-video",
    "https://lightricks-ltx-2-3.hf.space",
]

CAMERAS = ["Sony FX5", "Sony FX6", "Canon EOS C80", "ARRI Alexa Mini LF"]
PROPORCOES = ["1:1", "16:9", "9:16"]
MOTORES_VIDEO = [
    "Wan 2.2 — R3GM",
    "Wan 2.2 — Upsampler",
    "LTX-2.3 — Hugging Face",
    "Alex Dynamic Motion Engine",
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
    """Injeta um token rotativo do Hugging Face se disponível."""
    tokens = [
        _secret("HF_TOKEN"),
        _secret("HF_TOKEN_2"),
        _secret("HF_TOKEN_3"),
        _secret("HUGGINGFACE_HUB_TOKEN"),
    ]
    tokens_validos = [t for t in tokens if t]

    if tokens_validos:
        token_escolhido = random.choice(tokens_validos)
        os.environ["HF_TOKEN"] = token_escolhido
        os.environ["HUGGINGFACE_HUB_TOKEN"] = token_escolhido


def _nome_saida(prefixo: str, extensao: str = ".mp4") -> Path:
    return PASTA / f"{prefixo}_{int(time.time() * 1000)}{extensao}"


def montar_prompt(movimento: str, camera: str = "Sony FX6") -> str:
    return f"""
Animate the provided image into a realistic cinematic video.
Movement: {movimento}
Camera: {camera}
IMPORTANT: Keep exactly the same character from the reference image.
Preserve face, hairstyle, clothing, identity. Natural realistic movement.
""".strip()


def obter_imagem_prompt(prompt: str) -> Optional[bytes]:
    """Gera uma imagem base via IA caso o usuário peça apenas texto."""
    try:
        prompt_enc = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{prompt_enc}?width=512&height=512&nologo=true"
        r = requests.get(url, timeout=12)
        if r.status_code == 200 and len(r.content) > 1000:
            return r.content
    except Exception:
        pass
    return None


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
# MOTORES DE GERAÇÃO
# ============================================================


def gerar_r3gm(
    imagem_bytes: bytes,
    nome_imagem: str,
    movimento: str,
    camera: str = "Sony FX6",
    duracao: float = 5.0,
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

    client = Client(SPACES_HF[0])
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


def gerar_ltx_huggingface(
    prompt: str,
    duration: float = 5.0,
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

    client = Client(SPACES_HF[2])
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
        "fallback": False,
        "erro": None,
    }


def gerar_video_local_fallback(
    texto: str, imagem_bytes: Optional[bytes] = None, duracao: float = 5.0
) -> dict:
    """Gera um MP4 animado com movimento dinâmico de câmera (Zoom de 35% + Pan) bem perceptível."""
    if not imagem_bytes:
        imagem_bytes = obter_imagem_prompt(texto)

    destino = _nome_saida("video_motion", extensao=".mp4")
    fps = 30
    duracao_sec = max(2.0, min(float(duracao), 10.0))
    total_frames = int(duracao_sec * fps)

    if imagem_bytes:
        try:
            base = Image.open(io.BytesIO(imagem_bytes)).convert("RGB")
        except Exception:
            base = Image.new("RGB", (512, 512), color=(15, 23, 42))
    else:
        base = Image.new("RGB", (512, 512), color=(15, 23, 42))

    w, h = base.size
    frames = []

    for i in range(total_frames):
        progresso = i / float(total_frames)

        if imagem_bytes and w > 10 and h > 10:
            # Zoom mais forte (35% de ampliação)
            scale = 1.0 + (0.35 * progresso)
            nw, nh = int(w * scale), int(h * scale)
            img_scaled = base.resize((nw, nh), Image.Resampling.LANCZOS)

            # Movimento dinâmico de pan (câmera deslizando)
            max_x = nw - w
            max_y = nh - h
            
            crop_x = int(max_x * (0.5 + 0.5 * np.sin(progresso * np.pi)))
            crop_y = int(max_y * progresso)

            crop_x = max(0, min(crop_x, max_x))
            crop_y = max(0, min(crop_y, max_y))

            frame = img_scaled.crop((crop_x, crop_y, crop_x + w, crop_y + h))
            frame = frame.resize((512, 512), Image.Resampling.LANCZOS)
        else:
            frame = base.copy()
            draw = ImageDraw.Draw(frame)
            draw.text((20, 240), texto[:40] + "...", fill=(255, 255, 255))

        frames.append(frame)

    if IMAGEIO_AVAILABLE:
        np_frames = [np.array(f) for f in frames]
        imageio.mimsave(str(destino), np_frames, fps=fps)
        caminho_final = str(destino)
    else:
        caminho_gif = destino.with_suffix(".gif")
        frames[0].save(
            caminho_gif,
            save_all=True,
            append_images=frames[1:],
            duration=int(1000 / fps),
            loop=0,
        )
        caminho_final = str(caminho_gif)

    return {
        "sucesso": True,
        "motor": "Alex Dynamic Motion Engine",
        "video": caminho_final,
        "arquivo": caminho_final,
        "fallback": True,
        "erro": None,
    }


# ============================================================
# ORQUESTRADOR PRINCIPAL
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

    if not imagem_bytes:
        imagem_bytes = obter_imagem_prompt(texto)

    erros = []

    # 1. Tentar GPUs em Nuvem (Hugging Face)
    if imagem_bytes:
        try:
            return gerar_r3gm(imagem_bytes, nome_imagem, texto, camera, duracao)
        except Exception as erro:
            erros.append("R3GM: " + str(erro))

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

    # 2. Fallback de Movimento Dinâmico
    try:
        return gerar_video_local_fallback(
            texto, imagem_bytes=imagem_bytes, duracao=duracao
        )
    except Exception as erro:
        erros.append("Fallback Local: " + str(erro))

    return {
        "sucesso": False,
        "video": None,
        "arquivo": None,
        "motor": None,
        "erro": "⚠️ Não foi possível gerar o vídeo no momento.",
        "erros": erros,
    }


def gerar_video(prompt: Optional[str] = None, **kwargs) -> dict:
    return gerar_video_automatico(prompt=prompt, **kwargs)


def gerar_video_texto(prompt: str, **kwargs) -> dict:
    return gerar_video_automatico(prompt=prompt, **kwargs)


def gerar_video_imagem(
    imagem_bytes: bytes, nome_imagem: str, prompt: str, **kwargs
) -> dict:
    return gerar_video(
        prompt, imagem_bytes=imagem_bytes, nome_imagem=nome_imagem, **kwargs
    )


def mostrar_configuracao_video():
    st.subheader("🎬 Configuração de Vídeo")
    camera_video = st.selectbox(
        "📷 Câmera", CAMERAS, index=1, key="video_camera"
    )
    proporcao_video = st.selectbox(
        "📐 Proporção", PROPORCOES, index=1, key="video_proporcao"
    )
    duracao_video = st.number_input(
        "⏱️ Duração do vídeo",
        min_value=0.5,
        max_value=10.0,
        value=5.0,
        step=0.5,
        key="video_duracao",
    )
    return (camera_video, proporcao_video, duracao_video)


def status_video() -> dict:
    return {
        "gradio_client": Client is not None,
    }


__all__ = [
    "NOME_MODULO",
    "MOTORES_VIDEO",
    "CAMERAS",
    "PROPORCOES",
    "DURACAO_PADRAO",
    "gerar_video",
    "gerar_video_automatico",
    "gerar_video_texto",
    "gerar_video_imagem",
    "mostrar_configuracao_video",
    "status_video",
]

