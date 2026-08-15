"""Alex IA Ultra - geração de vídeo com fallback automático.

Motores remotos usados por padrão:
- Veo/Gemini (opcional, se o SDK/chave estiver disponível)
- Hugging Face Inference Providers / fal-ai:
  - tencent/HunyuanVideo
  - Lightricks/LTX-Video-0.9.8-13B-distilled
  - meituan-longcat/LongCat-Video

Também deixa Wan2.2 configurado como opção experimental, mas NÃO tenta
usá-lo automaticamente via HF enquanto o modelo não estiver implantado por
um Inference Provider. Isso evita falsos erros de "model not deployed".

O token nunca fica dentro deste arquivo. Use HF_TOKEN nos Secrets.
"""
from __future__ import annotations

import os
import time
import logging
from pathlib import Path
from typing import Callable, Optional, Any

try:
    from huggingface_hub import InferenceClient
except Exception:
    InferenceClient = None

logger = logging.getLogger("AlexIA.Video")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

PASTA_VIDEOS = Path("videos_gerados")
PASTA_VIDEOS.mkdir(parents=True, exist_ok=True)

DURACAO_PADRAO = 8
FPS_PADRAO = 16

CAMERAS = [
    "Sony FX5",
    "Sony FX6",
    "Canon EOS C80",
    "ARRI Alexa Mini LF",
]

PROPORCOES = {
    "16:9": (1280, 720),
    "9:16": (720, 1280),
    "1:1": (720, 720),
}

# Ordem: primeiro os motores mais confiáveis para o endpoint HF atual.
MOTORES_VIDEO = [
    {"nome": "Veo / Gemini", "tipo": "gemini", "modelo": "veo-3.1-generate-preview", "ativo": True},
    {"nome": "HunyuanVideo", "tipo": "huggingface", "modelo": "tencent/HunyuanVideo", "provider": "fal-ai", "ativo": True},
    {"nome": "LTX-Video", "tipo": "huggingface", "modelo": "Lightricks/LTX-Video-0.9.8-13B-distilled", "provider": "fal-ai", "ativo": True},
    {"nome": "LongCat-Video", "tipo": "huggingface", "modelo": "meituan-longcat/LongCat-Video", "provider": "fal-ai", "ativo": True},
    # Wan 2.2 é mantido no catálogo. A página do modelo atualmente informa
    # que não está implantado por Inference Provider; por isso fica desligado
    # no fallback remoto até haver provider disponível.
    {"nome": "Wan 2.2 TI2V 5B", "tipo": "huggingface", "modelo": "Wan-AI/Wan2.2-TI2V-5B", "provider": "fal-ai", "ativo": False, "experimental": True},
    {"nome": "Wan 2.1 1.3B", "tipo": "huggingface", "modelo": "Wan-AI/Wan2.1-T2V-1.3B", "provider": "fal-ai", "ativo": False, "experimental": True},
    {"nome": "CogVideoX 5B", "tipo": "huggingface", "modelo": "THUDM/CogVideoX-5b", "provider": "fal-ai", "ativo": False, "experimental": True},
    {"nome": "Mochi-1", "tipo": "huggingface", "modelo": "genmo/mochi-1-preview", "provider": "fal-ai", "ativo": False, "experimental": True},
]


def _token_hf() -> Optional[str]:
    return os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")


def _cliente_hf(provider: str = "fal-ai"):
    if InferenceClient is None:
        raise RuntimeError("huggingface_hub não está instalado. Adicione huggingface_hub ao requirements.txt.")
    token = _token_hf()
    if not token:
        raise RuntimeError("HF_TOKEN não configurado nos Secrets.")
    # Versões novas aceitam api_key; versões antigas normalmente aceitam token.
    try:
        return InferenceClient(provider=provider, api_key=token)
    except TypeError:
        try:
            return InferenceClient(provider=provider, token=token)
        except TypeError:
            return InferenceClient(token=token)


def _salvar_resultado(resultado: Any, destino: Path) -> Path:
    if isinstance(resultado, (bytes, bytearray)):
        destino.write_bytes(bytes(resultado))
        return destino
    content = getattr(resultado, "content", None)
    if isinstance(content, (bytes, bytearray)):
        destino.write_bytes(bytes(content))
        return destino
    # Alguns retornos podem ser objetos com bytes em atributo data.
    data = getattr(resultado, "data", None)
    if isinstance(data, (bytes, bytearray)):
        destino.write_bytes(bytes(data))
        return destino
    raise RuntimeError(f"Resposta do motor não contém vídeo binário (tipo: {type(resultado).__name__}).")


def _arquivo(prompt: str, motor: str) -> Path:
    nome = "".join(c if c.isalnum() or c in "-_" else "_" for c in prompt[:40]).strip("_") or "video"
    stamp = int(time.time() * 1000)
    return PASTA_VIDEOS / f"{nome}_{motor.replace(' ', '_')}_{stamp}.mp4"


def _prompt_camera(prompt: str, camera: str) -> str:
    camera = camera if camera in CAMERAS else CAMERAS[0]
    return (
        f"{prompt.strip()}. Cinematic live-action video, filmed with the look of {camera}, "
        "natural motion, consistent subject identity, realistic lighting, detailed environment, "
        "smooth camera movement, no text, no subtitles, no watermark."
    )


def gerar_huggingface(prompt: str, motor: dict, destino: Path, *, num_frames: int = 81, seed: Optional[int] = None) -> Path:
    client = _cliente_hf(motor.get("provider") or "fal-ai")
    kwargs = {
        "prompt": prompt,
        "model": motor["modelo"],
        "num_frames": int(num_frames),
    }
    if seed is not None:
        kwargs["seed"] = int(seed)
    logger.info("Vídeo: tentando %s (%s)", motor["nome"], motor["modelo"])
    resultado = client.text_to_video(**kwargs)
    return _salvar_resultado(resultado, destino)


def _gerar_veo(prompt: str, destino: Path, timeout: int = 300) -> Path:
    """Adaptador para google-genai. Se o SDK não suportar vídeos, falha limpo e segue o fallback."""
    try:
        from google import genai
    except Exception as exc:
        raise RuntimeError(f"SDK google-genai indisponível: {exc}")

    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY/GOOGLE_API_KEY não configurada.")

    client = genai.Client(api_key=key)
    if not hasattr(client.models, "generate_videos"):
        raise RuntimeError("Esta versão do SDK Gemini não expõe generate_videos().")

    operation = client.models.generate_videos(model="veo-3.1-generate-preview", prompt=prompt)
    started = time.time()
    while not getattr(operation, "done", False):
        if time.time() - started > timeout:
            raise TimeoutError("Veo excedeu o tempo máximo de espera.")
        time.sleep(5)
        operation = client.operations.get(operation)

    response = getattr(operation, "response", operation)
    generated = getattr(response, "generated_videos", None) or []
    if not generated:
        raise RuntimeError("Veo terminou sem devolver generated_videos.")

    video = getattr(generated[0], "video", generated[0])
    # O SDK normalmente baixa pelo objeto File.
    if hasattr(client.files, "download"):
        try:
            client.files.download(file=video)
        except Exception:
            pass
    data = getattr(video, "bytes", None)
    if isinstance(data, (bytes, bytearray)):
        destino.write_bytes(bytes(data))
        return destino
    raise RuntimeError("Veo devolveu o vídeo, mas o SDK não expôs os bytes para salvar.")


def gerar_video(
    prompt: str,
    *,
    camera: str = "Sony FX5",
    proporcao: str = "16:9",
    duracao: int = DURACAO_PADRAO,
    motores: Optional[list[str]] = None,
    usar_veo: bool = True,
    incluir_experimentais: bool = False,
    seed: Optional[int] = None,
    callback: Optional[Callable[[str], None]] = None,
) -> dict:
    """Gera vídeo tentando automaticamente o próximo motor quando houver erro."""
    if not prompt or not prompt.strip():
        return {"sucesso": False, "arquivo": None, "motor": None, "modelo": None, "tentativas": [], "erro": "Prompt vazio."}

    if proporcao not in PROPORCOES:
        proporcao = "16:9"
    duracao = max(1, min(int(duracao), 8))
    prompt_final = _prompt_camera(prompt, camera)

    nomes = set(motores or [])
    fila = []
    for m in MOTORES_VIDEO:
        if not m.get("ativo", False):
            if not (incluir_experimentais and m.get("experimental")):
                continue
        if m["tipo"] == "gemini" and not usar_veo:
            continue
        if nomes and m["nome"] not in nomes:
            continue
        fila.append(m)

    # A API do HF pode limitar parâmetros por provider; mantemos só o mínimo.
    num_frames = max(17, int(duracao * FPS_PADRAO) + 1)
    tentativas = []

    for motor in fila:
        destino = _arquivo(prompt, motor["nome"])
        msg = f"🎬 Tentando {motor['nome']}..."
        if callback:
            try: callback(msg)
            except Exception: pass
        try:
            if motor["tipo"] == "gemini":
                arquivo = _gerar_veo(prompt_final, destino)
            else:
                arquivo = gerar_huggingface(prompt_final, motor, destino, num_frames=num_frames, seed=seed)
            if not arquivo.exists() or arquivo.stat().st_size == 0:
                raise RuntimeError("O motor não retornou um arquivo de vídeo válido.")
            if callback:
                try: callback(f"✅ Vídeo gerado com {motor['nome']}.")
                except Exception: pass
            return {"sucesso": True, "arquivo": str(arquivo), "motor": motor["nome"], "modelo": motor["modelo"], "tentativas": tentativas, "erro": None}
        except Exception as exc:
            erro = str(exc)
            tentativas.append({"motor": motor["nome"], "modelo": motor["modelo"], "erro": erro})
            logger.warning("Motor %s falhou: %s", motor["nome"], erro)
            if callback:
                try: callback(f"⚠️ {motor['nome']} falhou. Tentando o próximo...")
                except Exception: pass

    erro_final = "Nenhum motor de vídeo conseguiu gerar o vídeo."
    if callback:
        try: callback("❌ " + erro_final)
        except Exception: pass
    return {"sucesso": False, "arquivo": None, "motor": None, "modelo": None, "tentativas": tentativas, "erro": erro_final}


def gerar_video_fallback(prompt: str, **kwargs) -> Optional[str]:
    resultado = gerar_video(prompt, **kwargs)
    return resultado.get("arquivo") if resultado.get("sucesso") else None


def gerar(prompt: str, **kwargs) -> dict:
    return gerar_video(prompt, **kwargs)


def listar_motores(incluir_experimentais: bool = True) -> list[dict]:
    """Lista os motores sem afirmar que um provider está disponível."""
    if incluir_experimentais:
        return [dict(m) for m in MOTORES_VIDEO]
    return [dict(m) for m in MOTORES_VIDEO if not m.get("experimental")]


def status_motores() -> list[dict]:
    hf = bool(_token_hf())
    gemini = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    resultado = []
    for m in MOTORES_VIDEO:
        x = dict(m)
        if m["tipo"] == "huggingface":
            x["configurado"] = hf
            x["status"] = "HF_TOKEN configurado" if hf else "HF_TOKEN ausente"
        else:
            x["configurado"] = gemini
            x["status"] = "chave Gemini configurada" if gemini else "chave Gemini ausente"
        resultado.append(x)
    return resultado
