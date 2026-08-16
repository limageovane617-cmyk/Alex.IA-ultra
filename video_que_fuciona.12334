"""Alex IA Ultra - gerenciador de vídeo compatível com app.py.

Mantém os dois motores que foram testados pelo projeto:
1. LTX-2.3 via Gradio Space (texto -> vídeo e imagem -> vídeo)
2. Magic Hour LTX-2.3 via API (imagem -> vídeo)

O módulo não executa nada ao ser importado. A interface é criada apenas
quando mostrar_configuracao_video() é chamada.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Optional

import streamlit as st
import requests

try:
    from gradio_client import Client
except Exception:
    Client = None

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
NOME_MODULO = "Alex IA Ultra — Gerenciador de Vídeo"
DURACAO_PADRAO = 5
LTX_HF_SPACE = "https://lightricks-ltx-2-3.hf.space"
MAGIC_HOUR_BASE_URL = "https://api.magichour.ai/v1"
MAGIC_HOUR_MODELO = "ltx-2.3"
MAGIC_HOUR_RESOLUCAO = "480p"
MAGIC_HOUR_DURACAO = 5

CAMERAS = ["Sony FX5", "Sony FX6", "Canon EOS C80", "ARRI Alexa Mini LF"]
PROPORCOES = ["1:1", "16:9", "9:16"]
MOTORES_VIDEO = [
    "LTX-2.3 — Hugging Face",
    "Magic Hour — LTX-2.3",
]

PASTA = Path("videos_gerados")
PASTA.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
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


def headers_magichour() -> dict:
    chave = obter_api_key_magichour()
    if not chave:
        raise RuntimeError("MAGIC_HOUR_API_KEY não foi encontrada nos Secrets do Streamlit.")
    return {
        "Authorization": f"Bearer {chave}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def salvar_video(conteudo: bytes, nome: str = "video.mp4") -> str:
    caminho = PASTA / nome
    caminho.write_bytes(conteudo)
    return str(caminho)


def _nome_saida(prefixo: str) -> Path:
    return PASTA / f"{prefixo}_{int(time.time() * 1000)}.mp4"

# ---------------------------------------------------------------------------
# LTX-2.3 — Space oficial testada
# ---------------------------------------------------------------------------
def gerar_ltx_huggingface(
    prompt: str,
    duration: float = 1.0,
    height: int = 512,
    width: int = 512,
    imagem_bytes: Optional[bytes] = None,
    nome_imagem: str = "imagem.png",
) -> dict:
    if Client is None:
        raise RuntimeError("gradio_client não está instalado. Adicione gradio_client ao requirements.txt.")
    if not prompt or not prompt.strip():
        raise ValueError("O prompt do vídeo está vazio.")

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
        seed=0,
        randomize_seed=True,
        height=int(height),
        width=int(width),
        api_name="/generate_video",
    )

    caminho_video = resultado[0] if isinstance(resultado, (tuple, list)) else resultado
    seed = resultado[1] if isinstance(resultado, (tuple, list)) and len(resultado) > 1 else None
    if not caminho_video:
        raise RuntimeError("LTX-2.3 não retornou o vídeo.")

    return {"sucesso": True, "motor": "LTX-2.3 — Hugging Face", "video": str(caminho_video), "arquivo": str(caminho_video), "seed": seed, "fallback": False, "erro": None}

# ---------------------------------------------------------------------------
# Magic Hour — código baseado no teste que funcionou
# ---------------------------------------------------------------------------
def obter_url_upload(extensao: str):
    ext = str(extensao or "png").lower().replace(".", "")
    formatos = {"png", "jpg", "jpeg", "webp", "jfif", "heic", "heif", "avif", "bmp", "tif", "tiff"}
    if ext not in formatos:
        raise RuntimeError(f"Formato de imagem não suportado: {ext}")
    resposta = requests.post(
        f"{MAGIC_HOUR_BASE_URL}/files/upload-urls",
        headers=headers_magichour(),
        json={"items": [{"type": "image", "extension": ext}]},
        timeout=60,
    )
    if resposta.status_code != 200:
        try:
            detalhes = resposta.json()
        except Exception:
            detalhes = resposta.text
        raise RuntimeError(f"Magic Hour retornou HTTP {resposta.status_code} ao solicitar upload:\n{detalhes}")
    resultado = resposta.json()
    itens = resultado.get("items") or []
    if not itens:
        raise RuntimeError(f"Magic Hour não retornou a lista de upload.\n{resultado}")
    item = itens[0]
    upload_url = item.get("upload_url")
    file_path = item.get("file_path")
    if not upload_url or not file_path:
        raise RuntimeError(f"A resposta não contém upload_url e file_path.\n{resultado}")
    return upload_url, file_path


def enviar_imagem_magichour(imagem_bytes: bytes, nome_arquivo: str) -> str:
    ext = Path(nome_arquivo).suffix.lower().replace(".", "") or "png"
    upload_url, file_path = obter_url_upload(ext)
    resposta = requests.put(upload_url, data=imagem_bytes, timeout=120)
    if resposta.status_code not in (200, 201, 204):
        raise RuntimeError(f"Falha no upload da imagem. HTTP {resposta.status_code}\n{resposta.text}")
    return file_path


def criar_projeto_magichour(file_path: str, prompt: str):
    dados = {
        "name": "Alex IA Ultra",
        "end_seconds": MAGIC_HOUR_DURACAO,
        "model": MAGIC_HOUR_MODELO,
        "resolution": MAGIC_HOUR_RESOLUCAO,
        "audio": False,
        "style": {"prompt": prompt.strip()},
        "assets": {"image_file_path": file_path},
    }
    resposta = requests.post(
        f"{MAGIC_HOUR_BASE_URL}/image-to-video",
        headers=headers_magichour(),
        json=dados,
        timeout=120,
    )
    if resposta.status_code not in (200, 201, 202):
        try:
            detalhes = resposta.json()
        except Exception:
            detalhes = resposta.text
        raise RuntimeError(f"Magic Hour retornou HTTP {resposta.status_code} ao criar vídeo:\n{detalhes}")
    resultado = resposta.json()
    projeto_id = resultado.get("id")
    if not projeto_id:
        raise RuntimeError(f"Magic Hour não retornou o ID do vídeo.\n{resultado}")
    return projeto_id, resultado


def consultar_projeto_magichour(projeto_id: str):
    ultimo_erro = None
    for url in (
        f"{MAGIC_HOUR_BASE_URL}/video-projects/{projeto_id}",
        f"{MAGIC_HOUR_BASE_URL}/image-to-video/{projeto_id}",
    ):
        try:
            resposta = requests.get(url, headers=headers_magichour(), timeout=60)
        except Exception as exc:
            ultimo_erro = str(exc)
            continue
        if resposta.status_code == 200:
            try:
                return resposta.json()
            except Exception:
                return {}
        ultimo_erro = f"HTTP {resposta.status_code}: {resposta.text}"
    raise RuntimeError(f"Não foi possível consultar o projeto.\n{ultimo_erro}")


def encontrar_download_magichour(dados: Any) -> Optional[str]:
    if not isinstance(dados, dict):
        return None
    for chave in ("video_url", "download_url", "output_url", "url"):
        valor = dados.get(chave)
        if isinstance(valor, str) and valor.startswith("http"):
            return valor

    downloads = dados.get("downloads")
    itens = downloads.values() if isinstance(downloads, dict) else downloads if isinstance(downloads, list) else []
    for item in itens:
        if isinstance(item, str) and item.startswith("http"):
            return item
        if isinstance(item, dict):
            for chave in ("url", "download_url"):
                valor = item.get(chave)
                if isinstance(valor, str) and valor.startswith("http"):
                    return valor

    output = dados.get("output")
    if isinstance(output, dict):
        for item in output.values():
            if isinstance(item, str) and item.startswith("http"):
                return item
            if isinstance(item, dict):
                for chave in ("url", "download_url"):
                    valor = item.get(chave)
                    if isinstance(valor, str) and valor.startswith("http"):
                        return valor
    return None


def baixar_video_magichour(url: str) -> str:
    caminho = _nome_saida("video_magichour")
    resposta = requests.get(url, timeout=180)
    if resposta.status_code != 200:
        raise RuntimeError(f"Falha ao baixar o vídeo. HTTP {resposta.status_code}")
    caminho.write_bytes(resposta.content)
    if caminho.stat().st_size == 0:
        raise RuntimeError("Magic Hour retornou um arquivo de vídeo vazio.")
    return str(caminho)


def gerar_magichour(imagem_bytes: bytes, nome_arquivo: str, prompt: str, timeout_segundos: int = 300) -> dict:
    if not imagem_bytes:
        raise ValueError("O Magic Hour precisa de uma imagem.")
    if not prompt or not prompt.strip():
        raise ValueError("O prompt do vídeo está vazio.")
    file_path = enviar_imagem_magichour(imagem_bytes, nome_arquivo)
    projeto_id, resultado = criar_projeto_magichour(file_path, prompt)
    inicio = time.time()
    ultimo = resultado
    video_url = encontrar_download_magichour(ultimo)
    while not video_url:
        if time.time() - inicio >= timeout_segundos:
            raise RuntimeError(f"Tempo limite atingido no Magic Hour.\nÚltima resposta:\n{ultimo}")
        time.sleep(5)
        ultimo = consultar_projeto_magichour(projeto_id)
        status = str(ultimo.get("status", "processing")).lower()
        if status in ("failed", "error", "cancelled"):
            raise RuntimeError(f"A geração no Magic Hour falhou.\n{ultimo}")
        video_url = encontrar_download_magichour(ultimo)
    caminho = baixar_video_magichour(video_url)
    return {"sucesso": True, "motor": "Magic Hour — LTX-2.3", "video": caminho, "arquivo": caminho, "projeto_id": projeto_id, "url": video_url, "fallback": False, "erro": None}

# ---------------------------------------------------------------------------
# Gerador automático
# ---------------------------------------------------------------------------
def gerar_video_automatico(prompt: Optional[str] = None, imagem_bytes: Optional[bytes] = None, nome_imagem: str = "imagem.png", duracao: float = 5.0, width: int = 512, height: int = 512, descricao: Optional[str] = None, **kwargs) -> dict:
    # app.py usa "descricao"; versões antigas usavam "prompt".
    texto = (prompt or descricao or "").strip()
    if not texto:
        return {"sucesso": False, "video": None, "motor": None, "erro": "O prompt/descrição do vídeo está vazio."}
    erros = []

    # Com imagem: tenta primeiro o Magic Hour, exatamente como no teste.
    if imagem_bytes:
        try:
            resultado = gerar_magichour(imagem_bytes, nome_imagem, texto)
            resultado["erros_anteriores"] = erros
            return resultado
        except Exception as exc:
            erros.append(f"Magic Hour: {exc}")

    # Fallback LTX Space. Também é usado para texto->vídeo.
    try:
        resultado = gerar_ltx_huggingface(
            prompt=texto,
            duration=min(float(duracao), 5.0),
            height=int(height),
            width=int(width),
            imagem_bytes=imagem_bytes,
            nome_imagem=nome_imagem,
        )
        resultado["fallback"] = bool(erros)
        resultado["erros_anteriores"] = erros
        resultado["sucesso"] = True
        return resultado
    except Exception as exc:
        erros.append(f"LTX-2.3 Hugging Face: {exc}")

    return {
        "sucesso": False,
        "video": None,
        "motor": None,
        "erro": "❌ NENHUM MOTOR DE VÍDEO CONSEGUIU GERAR O VÍDEO.\n\n" + "\n\n".join(erros),
        "erros": erros,
    }


def gerar_video(prompt: Optional[str] = None, imagem_bytes: Optional[bytes] = None, nome_imagem: str = "imagem.png", duracao: float = 5.0, width: int = 512, height: int = 512, descricao: Optional[str] = None, **kwargs) -> dict:
    return gerar_video_automatico(prompt, imagem_bytes, nome_imagem, duracao, width, height, descricao=descricao, **kwargs)


def gerar_video_texto(prompt: str, duracao: float = 1.0, **kwargs) -> dict:
    return gerar_ltx_huggingface(prompt, duration=duracao, **kwargs)


def gerar_video_imagem(imagem_bytes: bytes, nome_imagem: str, prompt: str, duracao: float = 5.0, **kwargs) -> dict:
    return gerar_video(prompt, imagem_bytes=imagem_bytes, nome_imagem=nome_imagem, duracao=duracao, **kwargs)


def gerar(prompt: str, **kwargs) -> dict:
    return gerar_video(prompt, **kwargs)


def gerar_video_fallback(prompt: str, **kwargs) -> Optional[str]:
    resultado = gerar_video(prompt, **kwargs)
    return resultado.get("video") or resultado.get("arquivo")

# ---------------------------------------------------------------------------
# Compatibilidade com app.py / interface
# ---------------------------------------------------------------------------
def mostrar_configuracao_video():
    st.subheader("🎬 Configuração de Vídeo")
    camera_video = st.selectbox("📷 Câmera", CAMERAS, index=0, key="video_camera")
    proporcao_video = st.selectbox("📐 Proporção", PROPORCOES, index=1, key="video_proporcao")
    duracao_video = st.number_input("⏱️ Duração do vídeo (segundos)", min_value=1, max_value=5, value=DURACAO_PADRAO, step=1, key="video_duracao")
    st.write("**🎥 Motores disponíveis:**")
    for motor in MOTORES_VIDEO:
        st.write(f"• {motor}")
    return camera_video, proporcao_video, duracao_video


def verificar_magic_hour():
    try:
        chave = obter_api_key_magichour()
        return (True, "✅ MAGIC_HOUR_API_KEY foi encontrada.") if chave else (False, "❌ MAGIC_HOUR_API_KEY não foi encontrada.")
    except Exception as exc:
        return False, f"❌ Erro ao verificar Magic Hour: {exc}"


def status_video() -> dict:
    return {
        "magic_hour": bool(obter_api_key_magichour()),
        "gradio_client": Client is not None,
        "ltx_space": LTX_HF_SPACE,
    }

__all__ = [
    "NOME_MODULO", "MOTORES_VIDEO", "CAMERAS", "PROPORCOES", "DURACAO_PADRAO",
    "gerar_video", "gerar_video_automatico", "gerar_video_fallback", "gerar",
    "gerar_video_texto", "gerar_video_imagem", "gerar_ltx_huggingface",
    "gerar_magichour", "mostrar_configuracao_video", "verificar_magic_hour",
    "obter_api_key_magichour", "status_video",
]
