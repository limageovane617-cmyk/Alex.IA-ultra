# ============================================================
# Alex IA Ultra — Gerenciador de Imagem
# ============================================================

import os
import time
import random

from pathlib import Path
from typing import Optional, Union
import requests
import streamlit as st
from PIL import Image

PASTA_IMAGENS = Path("/tmp/alex_ia_ultra_imagens")
PASTA_IMAGENS.mkdir(parents=True, exist_ok=True)


def _secret(nome: str) -> str:
    try:
        valor = st.secrets.get(nome, "")
    except Exception:
        valor = ""

    if not valor:
        valor = os.environ.get(nome, "")

    return str(valor or "").strip()


def remover_fundo(imagem_path: Union[str, Path]) -> Optional[str]:
    """Remove o fundo da imagem usando rembg se disponível."""
    try:
        from rembg import remove

        img = Image.open(imagem_path)
        img_sem_fundo = remove(img)
        saida_path = PASTA_IMAGENS / f"transparente_{int(time.time()*1000)}.png"
        img_sem_fundo.save(saida_path)
        return str(saida_path)
    except Exception:
        return str(imagem_path)


def gerar_imagem(
    prompt: str,
    largura: int = 1024,
    altura: int = 1024,
    remover_background: bool = False,
    **kwargs,
) -> dict:
    """Gera imagem e retorna formato de dicionário padronizado."""
    if not prompt or not prompt.strip():
        return {"sucesso": False, "erro": "Prompt de imagem vazio."}

    seed = random.randint(1, 999999)
    prompt_encoded = requests.utils.quote(prompt.strip())
    url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width={largura}&height={altura}&seed={seed}&model=flux"

    caminho_final = PASTA_IMAGENS / f"imagem_{int(time.time()*1000)}.png"

    try:
        res = requests.get(url, timeout=30)
        if res.status_code == 200 and len(res.content) > 1000:
            caminho_final.write_bytes(res.content)

            if remover_background:
                caminho_processado = remover_fundo(caminho_final)
                if caminho_processado:
                    caminho_final = Path(caminho_processado)

            return {
                "sucesso": True,
                "imagem": str(caminho_final),
                "arquivo": str(caminho_final),
                "mensagem": "🖼️ Imagem gerada com sucesso.",
            }
    except Exception as e:
        return {"sucesso": False, "erro": f"Erro na geração de imagem: {e}"}

    return {"sucesso": False, "erro": "Não foi possível gerar a imagem."}


def gerar(prompt: str, **kwargs) -> dict:
    return gerar_imagem(prompt, **kwargs)


def processar_imagem(prompt: str, **kwargs) -> dict:
    return gerar_imagem(prompt, **kwargs)


__all__ = ["gerar_imagem", "gerar", "processar_imagem", "remover_fundo"]
