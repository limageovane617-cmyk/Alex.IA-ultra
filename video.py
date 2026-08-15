# ============================================================
# VIDEO.PY — GERENCIADOR AUTOMÁTICO DE VÍDEO
# Alex IA Ultra
# ============================================================

import os
import time
from pathlib import Path

import requests
import streamlit as st

try:
    from gradio_client import Client, handle_file
except ImportError:
    Client = None
    handle_file = None

NOME_MODULO = "Alex IA Ultra — Gerenciador de Vídeo"
MOTORES_VIDEO = ["Magic Hour — LTX-2.3", "LTX-2.3 — Hugging Face"]
CAMERAS = ["Sony FX5", "Sony FX6", "Canon EOS C80", "ARRI Alexa Mini LF"]
PROPORCOES = ["1:1", "16:9", "9:16"]
DURACAO_PADRAO = 5
LTX_HF_SPACE = "https://huggingface.co/spaces/Lightricks/LTX-2-3"
MAGIC_HOUR_BASE_URL = "https://api.magichour.ai/v1"
MAGIC_HOUR_MODELO = "ltx-2.3"
MAGIC_HOUR_RESOLUCAO = "720p"
MAGIC_HOUR_DURACAO = 5
PASTA = Path("/tmp/alex_ia_ultra_videos")
PASTA.mkdir(parents=True, exist_ok=True)


def obter_api_key_magichour():
    try:
        chave = st.secrets.get("MAGIC_HOUR_API_KEY", "")
    except Exception:
        chave = ""
    if not chave:
        chave = os.environ.get("MAGIC_HOUR_API_KEY", "")
    return str(chave).strip()


def verificar_magic_hour():
    chave = obter_api_key_magichour()
    if chave:
        return True, "MAGIC_HOUR_API_KEY encontrada."
    return False, "MAGIC_HOUR_API_KEY não encontrada nos Secrets."


def headers_magichour():
    chave = obter_api_key_magichour()
    if not chave:
        raise RuntimeError("MAGIC_HOUR_API_KEY não foi encontrada nos Secrets do Streamlit.")
    return {"Authorization": f"Bearer {chave}", "Accept": "application/json", "Content-Type": "application/json"}


def salvar_video(conteudo, nome="video.mp4"):
    caminho = PASTA / nome
    caminho.write_bytes(conteudo)
    return str(caminho)


def _normalizar_imagem(imagem_bytes, nome_imagem):
    if not imagem_bytes:
        return None
    ext = Path(nome_imagem or "imagem.png").suffix.lower() or ".png"
    caminho = PASTA / f"imagem_ltx{ext}"
    caminho.write_bytes(imagem_bytes)
    return caminho


def gerar_ltx_huggingface(prompt, duration=5.0, height=1024, width=1536,
                          imagem_bytes=None, nome_imagem="imagem.png"):
    if Client is None:
        raise RuntimeError("gradio_client não está instalado. Adicione gradio_client ao requirements.txt.")
    if not prompt or not prompt.strip():
        raise ValueError("O prompt do vídeo está vazio.")

    caminho_imagem = _normalizar_imagem(imagem_bytes, nome_imagem)
    client = Client(LTX_HF_SPACE)

    # A interface oficial atual usa input_image, prompt, duration,
    # enhance_prompt, seed, randomize_seed, height e width em /generate_video.
    resultado = client.predict(
        input_image=str(caminho_imagem) if caminho_imagem else None,
        prompt=prompt.strip(),
        duration=float(max(1.0, min(float(duration), 10.0))),
        enhance_prompt=True,
        seed=42,
        randomize_seed=True,
        height=int(height),
        width=int(width),
        api_name="/generate_video",
    )

    if isinstance(resultado, (tuple, list)):
        caminho_video = resultado[0] if resultado else None
        seed = resultado[1] if len(resultado) > 1 else None
    else:
        caminho_video, seed = resultado, None

    if not caminho_video:
        raise RuntimeError("LTX-2.3 do Hugging Face não retornou um vídeo.")

    return {"motor": "LTX-2.3 — Hugging Face", "video": str(caminho_video), "seed": seed}


def obter_url_upload(extensao):
    extensao = str(extensao).lower().lstrip(".")
    formatos = {"png", "jpg", "jpeg", "webp", "jfif", "heic", "heif", "avif", "bmp", "tif", "tiff"}
    if extensao not in formatos:
        raise RuntimeError(f"Formato de imagem não suportado: {extensao}")
    resposta = requests.post(
        f"{MAGIC_HOUR_BASE_URL}/files/upload-urls",
        headers=headers_magichour(),
        json={"items": [{"type": "image", "extension": extensao}]},
        timeout=60,
    )
    if resposta.status_code != 200:
        raise RuntimeError(f"Magic Hour HTTP {resposta.status_code}: {resposta.text}")
    dados = resposta.json()
    itens = dados.get("items") or []
    if not itens or not itens[0].get("upload_url") or not itens[0].get("file_path"):
        raise RuntimeError(f"Resposta de upload inesperada do Magic Hour: {dados}")
    return itens[0]["upload_url"], itens[0]["file_path"]


def enviar_imagem_magichour(imagem_bytes, nome_arquivo):
    ext = Path(nome_arquivo or "imagem.png").suffix.lower().lstrip(".") or "png"
    upload_url, file_path = obter_url_upload(ext)
    resposta = requests.put(upload_url, data=imagem_bytes, timeout=120)
    if resposta.status_code not in (200, 201, 204):
        raise RuntimeError(f"Falha no upload da imagem: HTTP {resposta.status_code}: {resposta.text}")
    return file_path


def criar_projeto_magichour(file_path, prompt):
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
        headers=headers_magichour(), json=dados, timeout=120,
    )
    if resposta.status_code not in (200, 201, 202):
        raise RuntimeError(f"Magic Hour HTTP {resposta.status_code}: {resposta.text}")
    dados_resp = resposta.json()
    projeto_id = dados_resp.get("id")
    if not projeto_id:
        raise RuntimeError(f"Magic Hour não retornou ID: {dados_resp}")
    return projeto_id, dados_resp


def consultar_projeto_magichour(projeto_id):
    ultimo = None
    for url in (
        f"{MAGIC_HOUR_BASE_URL}/video-projects/{projeto_id}",
        f"{MAGIC_HOUR_BASE_URL}/image-to-video/{projeto_id}",
    ):
        try:
            resposta = requests.get(url, headers=headers_magichour(), timeout=60)
            if resposta.status_code == 200:
                return resposta.json()
            ultimo = f"HTTP {resposta.status_code}: {resposta.text}"
        except Exception as erro:
            ultimo = str(erro)
    raise RuntimeError(f"Não foi possível consultar o projeto Magic Hour: {ultimo}")


def encontrar_download_magichour(dados):
    if not isinstance(dados, dict):
        return None
    chaves = ("video_url", "download_url", "output_url", "url")
    for chave in chaves:
        valor = dados.get(chave)
        if isinstance(valor, str) and valor.startswith("http"):
            return valor
    for chave in ("downloads", "output", "outputs", "result"):
        valor = dados.get(chave)
        itens = valor.values() if isinstance(valor, dict) else valor if isinstance(valor, list) else []
        for item in itens:
            if isinstance(item, str) and item.startswith("http"):
                return item
            if isinstance(item, dict):
                for sub in chaves:
                    u = item.get(sub)
                    if isinstance(u, str) and u.startswith("http"):
                        return u
    return None


def baixar_video_magichour(url):
    resposta = requests.get(url, timeout=180)
    if resposta.status_code != 200:
        raise RuntimeError(f"Falha ao baixar o vídeo: HTTP {resposta.status_code}")
    return salvar_video(resposta.content, f"video_magichour_{int(time.time())}.mp4")


def gerar_magichour(imagem_bytes, nome_arquivo, prompt, timeout_segundos=300):
    if not imagem_bytes:
        raise ValueError("O Magic Hour precisa de uma imagem.")
    if not obter_api_key_magichour():
        raise RuntimeError("MAGIC_HOUR_API_KEY não configurada.")
    file_path = enviar_imagem_magichour(imagem_bytes, nome_arquivo)
    projeto_id, resultado = criar_projeto_magichour(file_path, prompt)
    inicio = time.time()
    while True:
        video_url = encontrar_download_magichour(resultado)
        if video_url:
            return {"motor": "Magic Hour — LTX-2.3", "video": baixar_video_magichour(video_url), "projeto_id": projeto_id, "url": video_url}
        status = str(resultado.get("status", "processing")).lower() if isinstance(resultado, dict) else "processing"
        if status in {"failed", "error", "cancelled"}:
            raise RuntimeError(f"Magic Hour falhou: {resultado}")
        if time.time() - inicio >= timeout_segundos:
            raise RuntimeError(f"Tempo limite do Magic Hour atingido. Última resposta: {resultado}")
        time.sleep(5)
        resultado = consultar_projeto_magichour(projeto_id)


def gerar_video_automatico(prompt, imagem_bytes=None, nome_imagem="imagem.png", duracao=5.0, width=1536, height=1024):
    if not prompt or not prompt.strip():
        raise ValueError("O prompt do vídeo está vazio.")
    erros = []

    # Com imagem, Magic Hour é o primeiro motor. Se falhar, NÃO interrompe:
    # o LTX-2.3 do Hugging Face recebe a oportunidade de fazer o fallback.
    if imagem_bytes and obter_api_key_magichour():
        try:
            resultado = gerar_magichour(imagem_bytes, nome_imagem, prompt)
            resultado.update(fallback=False, erros_anteriores=erros)
            return resultado
        except Exception as erro:
            erros.append(f"Magic Hour: {erro}")
    elif imagem_bytes:
        erros.append("Magic Hour: MAGIC_HOUR_API_KEY não configurada; usando fallback.")

    try:
        resultado = gerar_ltx_huggingface(
            prompt=prompt, duration=duracao, width=width, height=height,
            imagem_bytes=imagem_bytes, nome_imagem=nome_imagem,
        )
        resultado.update(fallback=bool(erros), erros_anteriores=erros)
        return resultado
    except Exception as erro:
        erros.append(f"LTX-2.3 Hugging Face: {erro}")

    raise RuntimeError("❌ NENHUM MOTOR DE VÍDEO CONSEGUIU GERAR O VÍDEO.\n\n" + "\n\n".join(erros))


def mostrar_configuracao_video():
    col1, col2, col3 = st.columns(3)
    with col1:
        camera = st.selectbox("🎥 Câmera", CAMERAS, key="video_camera")
    with col2:
        proporcao = st.selectbox("📐 Proporção", PROPORCOES, index=1, key="video_proporcao")
    with col3:
        duracao = st.slider("⏱️ Duração", 1.0, 10.0, float(DURACAO_PADRAO), 1.0, key="video_duracao")
    return camera, proporcao, duracao


def gerar_video(prompt=None, imagem_bytes=None, nome_imagem="imagem.png", duracao=5.0,
                width=1536, height=1024, descricao=None, camera=None, proporcao=None):
    # Compatibilidade com as duas chamadas existentes no app.py.
    texto = prompt if prompt is not None else descricao
    if not texto:
        raise ValueError("Descrição do vídeo não informada.")
    if camera:
        texto += f"\nCâmera cinematográfica: {camera}."
    if proporcao:
        texto += f"\nProporção: {proporcao}."
    return gerar_video_automatico(texto, imagem_bytes, nome_imagem, duracao, width, height)
