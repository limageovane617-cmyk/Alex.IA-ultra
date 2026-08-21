# ============================================================
# Alex IA Ultra — Gerenciador de Vídeo
# ============================================================

from __future__ import annotations

import io
import os
import random
import time
import urllib.parse
import re
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

HEADERS_REQ = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def _secret(nome: str) -> str:
    try:
        valor = st.secrets.get(nome, "")
    except Exception:
        valor = ""
    if not valor:
        valor = os.environ.get(nome, "")
    return str(valor or "").strip()


def aplicar_hf_token():
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


def limpar_prompt(prompt: str) -> str:
    """Remove comandos de texto deixando apenas o assunto principal."""
    p = re.sub(r"(?i)^(cria|gere|faz|faça|gerar|criar)\s+(um\s+|uma\s+)?(vídeo|video)\s+(de\s+|do\s+|da\s+)?", "", prompt.strip())
    return p if p else prompt


def montar_prompt(movimento: str, camera: str = "Sony FX6") -> str:
    return f"Animate image. Movement: {movimento}. Camera: {camera}. Cinematic high quality."


def obter_imagem_prompt(prompt: str) -> Optional[bytes]:
    """Obtém imagem com requisição autenticada contra bloqueios na nuvem."""
    assunto = limpar_prompt(prompt)
    prompt_enc = urllib.parse.quote(assunto)
    seed = random.randint(1, 99999)

    urls = [
        f"https://image.pollinations.ai/prompt/{prompt_enc}?width=512&height=512&nologo=true&seed={seed}&model=flux",
        f"https://image.pollinations.ai/prompt/{prompt_enc}?width=512&height=512&nologo=true&seed={seed}",
        f"https://picsum.photos/512/512"
    ]

    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS_REQ, timeout=10)
            if r.status_code == 200 and len(r.content) > 3000:
                return r.content
        except Exception:
            continue

    return None


def _extrair_video_gradio(resultado: Any) -> Optional[str]:
    if isinstance(resultado, str) and (resultado.startswith("http") or resultado.endswith(".mp4")):
        return resultado
    if isinstance(resultado, dict):
        for k in ["video", "output", "path", "url"]:
            res = _extrair_video_gradio(resultado.get(k))
            if res:
                return res
    if isinstance(resultado, (list, tuple)):
        for item in resultado:
            res = _extrair_video_gradio(item)
            if res:
                return res
    return None


def _salvar_video_gradio(origem: str, destino: Path) -> str:
    if Path(origem).exists():
        destino.write_bytes(Path(origem).read_bytes())
    elif origem.startswith("http"):
        r = requests.get(origem, headers=HEADERS_REQ, timeout=300)
        r.raise_for_status()
        destino.write_bytes(r.content)
    return str(destino)


def gerar_r3gm(imagem_bytes: bytes, nome_imagem: str, movimento: str, camera: str, duracao: float) -> dict:
    if Client is None or handle_file is None or not imagem_bytes:
        raise RuntimeError("R3GM indisponível.")
    aplicar_hf_token()
    entrada = PASTA / f"in_r3gm_{int(time.time()*1000)}.jpg"
    entrada.write_bytes(imagem_bytes)
    
    client = Client(SPACES_HF[0])
    resultado = client.predict(
        input_image=handle_file(str(entrada)),
        last_image=None,
        prompt=montar_prompt(movimento, camera),
        steps=4,
        negative_prompt="static, blurry",
        duration_seconds=max(0.5, min(float(duracao), 10.0)),
        guidance_scale=1.0, guidance_scale_2=1.0,
        seed=random.randint(0, 2147483647),
        randomize_seed=True, quality=5,
        scheduler="FlowMatchEulerDiscrete", flow_shift=6.0,
        frame_multiplier=16, video_component=True,
        safe_mode=True, enable_safety_checker=True,
        api_name="/generate_video",
    )
    video = _extrair_video_gradio(resultado)
    if not video:
        raise RuntimeError("Sem retorno do R3GM.")
    caminho = _salvar_video_gradio(video, _nome_saida("video_r3gm"))
    return {"sucesso": True, "motor": "Wan 2.2 — R3GM", "video": caminho, "arquivo": caminho, "fallback": False, "erro": None}


def gerar_video_local_fallback(texto: str, imagem_bytes: Optional[bytes] = None, duracao: float = 5.0) -> dict:
    if not imagem_bytes:
        imagem_bytes = obter_imagem_prompt(texto)

    if not imagem_bytes:
        raise RuntimeError("Não foi possível carregar a imagem base para o vídeo.")

    base = Image.open(io.BytesIO(imagem_bytes)).convert("RGB").resize((512, 512))
    w, h = base.size
    destino = _nome_saida("video_motion", extensao=".mp4")
    fps = 30
    total_frames = int(max(2.0, min(float(duracao), 10.0)) * fps)
    frames = []

    for i in range(total_frames):
        prog = i / float(total_frames)
        scale = 1.0 + (0.30 * prog)
        nw, nh = int(w * scale), int(h * scale)
        img_scaled = base.resize((nw, nh), Image.Resampling.LANCZOS)
        
        max_x, max_y = nw - w, nh - h
        crop_x = int(max_x * (0.5 + 0.5 * np.sin(prog * np.pi))) if IMAGEIO_AVAILABLE else int(max_x * prog)
        crop_y = int(max_y * prog)
        
        frame = img_scaled.crop((crop_x, crop_y, crop_x + w, crop_y + h)).resize((512, 512))
        frames.append(frame)

    if IMAGEIO_AVAILABLE:
        np_frames = [np.array(f) for f in frames]
        imageio.mimsave(str(destino), np_frames, fps=fps)
        caminho_final = str(destino)
    else:
        caminho_gif = destino.with_suffix(".gif")
        frames[0].save(caminho_gif, save_all=True, append_images=frames[1:], duration=int(1000/fps), loop=0)
        caminho_final = str(caminho_gif)

    return {"sucesso": True, "motor": "Alex Dynamic Motion", "video": caminho_final, "arquivo": caminho_final, "fallback": True, "erro": None}


def gerar_video_automatico(
    prompt: Optional[str] = None,
    imagem_bytes: Optional[bytes] = None,
    nome_imagem: str = "imagem.png",
    duracao: float = 5.0,
    camera: str = "Sony FX6",
    **kwargs,
) -> dict:
    texto = (prompt or "").strip()
    if not texto:
        return {"sucesso": False, "erro": "Prompt vazio."}

    if not imagem_bytes:
        imagem_bytes = obter_imagem_prompt(texto)

    if imagem_bytes:
        try:
            return gerar_r3gm(imagem_bytes, nome_imagem, texto, camera, duracao)
        except Exception:
            pass

    return gerar_video_local_fallback(texto, imagem_bytes=imagem_bytes, duracao=duracao)


def gerar_video(prompt: Optional[str] = None, **kwargs) -> dict:
    return gerar_video_automatico(prompt=prompt, **kwargs)

def gerar_video_texto(prompt: str, **kwargs) -> dict:
    return gerar_video_automatico(prompt=prompt, **kwargs)

def gerar_video_imagem(imagem_bytes: bytes, nome_imagem: str, prompt: str, **kwargs) -> dict:
    return gerar_video(prompt, imagem_bytes=imagem_bytes, nome_imagem=nome_imagem, **kwargs)

def mostrar_configuracao_video():
    st.subheader("🎬 Configuração de Vídeo")
    camera = st.selectbox("📷 Câmera", CAMERAS, index=1, key="video_camera")
    prop = st.selectbox("📐 Proporção", PROPORCOES, index=1, key="video_proporcao")
    dur = st.number_input("⏱️ Duração", min_value=0.5, max_value=10.0, value=5.0, step=0.5, key="video_duracao")
    return (camera, prop, dur)

def status_video() -> dict:
    return {"gradio_client": Client is not None}

__all__ = [
    "NOME_MODULO", "MOTORES_VIDEO", "CAMERAS", "PROPORCOES", "DURACAO_PADRAO",
    "gerar_video", "gerar_video_automatico", "gerar_video_texto", "gerar_video_imagem",
    "mostrar_configuracao_video", "status_video",
               ]
