# ============================================================
# 🎬 ALEX IA ULTRA — GERENCIADOR DE VÍDEO CORRIGIDO
# ============================================================
# LTX-2.3 HF + Magic Hour
#
# Correções:
# - chamada LTX atualizada para o Space atual
# - resolução compatível com LTX-2.3
# - image-to-video e text-to-video
# - fallback automático
# - erros detalhados
# - Magic Hour 401 identificado separadamente
# ============================================================

from __future__ import annotations

import os
import time
import threading
from pathlib import Path

import requests
import streamlit as st


# ============================================================
# CONFIGURAÇÕES
# ============================================================

PASTA_VIDEOS = Path("videos_gerados")
PASTA_VIDEOS.mkdir(parents=True, exist_ok=True)

LTX_SPACE = "https://lightricks-ltx-2-3.hf.space"

MAGIC_HOUR_BASE_URL = "https://api.magichour.ai/v1"

TEMPO_REATIVACAO_QUOTA = 1800
DURACAO_PADRAO = 5

CAMERAS = [
    "Sony FX5",
    "Sony FX6",
    "Canon EOS C80",
    "ARRI Alexa Mini LF",
]

PROPORCOES = [
    "16:9",
    "9:16",
    "1:1",
]

LOCK = threading.Lock()

ESTADO_MOTORES = {
    "LTX-2.3 HF": {
        "ativo": True,
        "cooldown_until": 0.0,
        "quota": False,
        "erros": 0,
        "sucessos": 0,
        "ultimo_erro": None,
    },
    "Magic Hour": {
        "ativo": True,
        "cooldown_until": 0.0,
        "quota": False,
        "erros": 0,
        "sucessos": 0,
        "ultimo_erro": None,
    },
}


# ============================================================
# ESTADO DOS MOTORES
# ============================================================

def _estado(nome):
    return ESTADO_MOTORES[nome]


def _reativar_expirados():
    agora = time.time()

    with LOCK:
        for nome, estado in ESTADO_MOTORES.items():
            if estado["cooldown_until"] > 0 and estado["cooldown_until"] <= agora:
                estado["cooldown_until"] = 0.0
                estado["quota"] = False
                estado["ultimo_erro"] = None


def _disponivel(nome):
    _reativar_expirados()
    estado = _estado(nome)

    return (
        estado["ativo"]
        and estado["cooldown_until"] <= time.time()
    )


def _registrar_sucesso(nome):
    estado = _estado(nome)
    estado["sucessos"] += 1
    estado["ultimo_erro"] = None
    estado["quota"] = False
    estado["cooldown_until"] = 0.0


def _registrar_erro(nome, erro):
    estado = _estado(nome)
    estado["erros"] += 1
    estado["ultimo_erro"] = str(erro)


def _eh_quota(erro):
    texto = str(erro).lower()

    palavras = [
        "429",
        "quota",
        "rate limit",
        "rate_limit",
        "resource_exhausted",
        "resource exhausted",
        "too many requests",
        "limit exceeded",
        "daily limit",
        "usage limit",
        "capacity",
        "exceeded",
    ]

    return any(palavra in texto for palavra in palavras)


def _bloquear_quota(nome, erro):
    estado = _estado(nome)
    estado["quota"] = True
    estado["erros"] += 1
    estado["ultimo_erro"] = str(erro)
    estado["cooldown_until"] = time.time() + TEMPO_REATIVACAO_QUOTA


# ============================================================
# UTILITÁRIOS
# ============================================================

def _nome_arquivo(prefixo="video"):
    return f"{prefixo}_{int(time.time() * 1000)}.mp4"


def _validar_camera(camera):
    return camera if camera in CAMERAS else "Sony FX6"


def _validar_proporcao(proporcao):
    return proporcao if proporcao in PROPORCOES else "16:9"


def _validar_duracao(duracao):
    try:
        valor = float(duracao)
    except Exception:
        valor = DURACAO_PADRAO

    valor = max(1.0, min(10.0, valor))
    return valor


def _dimensoes_por_proporcao(proporcao):
    proporcao = _validar_proporcao(proporcao)

    if proporcao == "9:16":
        return 576, 1024

    if proporcao == "1:1":
        return 1024, 1024

    return 1536, 1024


def _salvar_video(origem, nome_arquivo=None):
    origem = Path(origem)

    if not origem.exists():
        raise RuntimeError(f"Vídeo não encontrado: {origem}")

    if origem.stat().st_size <= 0:
        raise RuntimeError("O vídeo está vazio.")

    nome = Path(nome_arquivo).name if nome_arquivo else origem.name

    if not nome.lower().endswith(".mp4"):
        nome += ".mp4"

    destino = PASTA_VIDEOS / nome

    if destino.resolve() != origem.resolve():
        destino.write_bytes(origem.read_bytes())

    if not destino.exists() or destino.stat().st_size <= 0:
        raise RuntimeError("Não foi possível salvar o vídeo.")

    return str(destino)


def _baixar_url(url, nome_arquivo=None):
    if not isinstance(url, str) or not url.startswith("http"):
        raise RuntimeError("URL do vídeo inválida.")

    resposta = requests.get(url, timeout=180)

    if resposta.status_code != 200:
        raise RuntimeError(
            f"Falha ao baixar vídeo. HTTP {resposta.status_code}: "
            f"{resposta.text[:1000]}"
        )

    nome = nome_arquivo or _nome_arquivo()
    if not nome.lower().endswith(".mp4"):
        nome += ".mp4"

    destino = PASTA_VIDEOS / Path(nome).name
    destino.write_bytes(resposta.content)

    if destino.stat().st_size <= 0:
        raise RuntimeError("O vídeo baixado está vazio.")

    return str(destino)


# ============================================================
# 🎬 LTX-2.3 — HUGGING FACE / GRADIO
# ============================================================

def _gerar_ltx_hf(
    prompt,
    imagem_bytes=None,
    nome_imagem="imagem.png",
    duracao=5,
    width=None,
    height=None,
    camera=None,
    proporcao="16:9",
    nome_arquivo=None,
    **kwargs
):
    try:
        from gradio_client import Client
    except Exception as erro:
        raise RuntimeError(
            "gradio_client não está instalado. "
            "Adicione gradio_client ao requirements.txt."
        ) from erro

    largura_padrao, altura_padrao = _dimensoes_por_proporcao(proporcao)

    try:
        largura = int(width or largura_padrao)
        altura = int(height or altura_padrao)
    except Exception:
        largura = largura_padrao
        altura = altura_padrao

    # O Space atual trabalha com resoluções maiores.
    if largura < 512 or altura < 512:
        largura, altura = largura_padrao, altura_padrao

    duracao = _validar_duracao(duracao)

    caminho_imagem = None

    if imagem_bytes:
        pasta_temp = PASTA_VIDEOS / "temp"
        pasta_temp.mkdir(parents=True, exist_ok=True)

        caminho_imagem = pasta_temp / Path(nome_imagem).name
        caminho_imagem.write_bytes(imagem_bytes)

    try:
        client = Client(LTX_SPACE)

        resultado = client.predict(
            input_image=str(caminho_imagem) if caminho_imagem else None,
            prompt=str(prompt),
            duration=float(duracao),
            enhance_prompt=True,
            seed=42,
            randomize_seed=True,
            height=altura,
            width=largura,
            api_name="/generate_video",
        )

    except Exception as erro:
        texto = str(erro)

        if "upstream Gradio app has raised an exception" in texto:
            raise RuntimeError(
                "O Space LTX-2.3 recebeu a solicitação, "
                "mas apresentou uma exceção interna. "
                "Isso pode acontecer quando o Space está sem GPU "
                "disponível ou em erro temporário. "
                f"Detalhe: {texto}"
            ) from erro

        raise RuntimeError(
            f"Falha na comunicação com o Space LTX-2.3: {texto}"
        ) from erro

    if not resultado:
        raise RuntimeError("LTX-2.3 retornou resposta vazia.")

    caminho = resultado[0] if isinstance(resultado, (tuple, list)) else resultado

    if not caminho:
        raise RuntimeError("LTX-2.3 não retornou o caminho do vídeo.")

    caminho = Path(str(caminho))

    if not caminho.exists():
        raise RuntimeError(
            f"LTX-2.3 retornou um caminho inexistente: {caminho}"
        )

    arquivo = _salvar_video(caminho, nome_arquivo)

    return {
        "video": arquivo,
        "motor": "LTX-2.3 HF",
    }


# ============================================================
# 🔐 MAGIC HOUR
# ============================================================

def _magic_hour_api_key():
    try:
        chave = st.secrets.get("MAGIC_HOUR_API_KEY", "")
    except Exception:
        chave = ""

    if not chave:
        chave = os.environ.get("MAGIC_HOUR_API_KEY", "")

    chave = str(chave).strip()

    if not chave:
        raise RuntimeError(
            "MAGIC_HOUR_API_KEY não está configurada nos Secrets."
        )

    return chave


def _magic_headers():
    return {
        "Authorization": f"Bearer {_magic_hour_api_key()}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _magic_obter_upload_url(extensao):
    extensao = str(extensao).lower().replace(".", "")

    extensoes = [
        "png", "jpg", "jpeg", "webp", "jfif",
        "heic", "heif", "avif", "bmp", "tif", "tiff",
    ]

    if extensao not in extensoes:
        raise RuntimeError(f"Formato não suportado: {extensao}")

    resposta = requests.post(
        f"{MAGIC_HOUR_BASE_URL}/files/upload-urls",
        headers=_magic_headers(),
        json={
            "items": [
                {
                    "type": "image",
                    "extension": extensao,
                }
            ]
        },
        timeout=60,
    )

    if resposta.status_code == 401:
        raise RuntimeError(
            "Magic Hour recusou a API Key (HTTP 401 Unauthorized). "
            "Verifique se MAGIC_HOUR_API_KEY contém uma chave válida "
            "do Magic Hour nos Secrets do Streamlit."
        )

    if resposta.status_code != 200:
        try:
            detalhes = resposta.json()
        except Exception:
            detalhes = resposta.text

        raise RuntimeError(
            f"Magic Hour falhou ao obter URL de upload. "
            f"HTTP {resposta.status_code}: {detalhes}"
        )

    dados = resposta.json()
    itens = dados.get("items")

    if not itens:
        raise RuntimeError("Magic Hour não retornou os dados de upload.")

    item = itens[0]
    upload_url = item.get("upload_url")
    file_path = item.get("file_path")

    if not upload_url or not file_path:
        raise RuntimeError(
            "Magic Hour não retornou upload_url/file_path."
        )

    return upload_url, file_path


def _magic_enviar_imagem(imagem_bytes, nome_imagem):
    extensao = Path(nome_imagem).suffix.lower()

    upload_url, file_path = _magic_obter_upload_url(extensao)

    resposta = requests.put(
        upload_url,
        data=imagem_bytes,
        timeout=120,
    )

    if resposta.status_code not in [200, 201, 204]:
        raise RuntimeError(
            f"Falha no upload da imagem para o Magic Hour. "
            f"HTTP {resposta.status_code}: {resposta.text[:1000]}"
        )

    return file_path


def _magic_criar_video(file_path, prompt, duracao=5):
    dados = {
        "name": "Alex IA Ultra",
        "end_seconds": int(_validar_duracao(duracao)),
        "model": "ltx-2.3",
        "resolution": "480p",
        "audio": False,
        "style": {
            "prompt": str(prompt).strip()
        },
        "assets": {
            "image_file_path": file_path
        },
    }

    resposta = requests.post(
        f"{MAGIC_HOUR_BASE_URL}/image-to-video",
        headers=_magic_headers(),
        json=dados,
        timeout=120,
    )

    if resposta.status_code == 401:
        raise RuntimeError(
            "Magic Hour recusou a API Key (HTTP 401 Unauthorized)."
        )

    if resposta.status_code not in [200, 201, 202]:
        try:
            detalhes = resposta.json()
        except Exception:
            detalhes = resposta.text

        raise RuntimeError(
            f"Magic Hour falhou ao criar o vídeo. "
            f"HTTP {resposta.status_code}: {detalhes}"
        )

    dados_resposta = resposta.json()
    projeto_id = dados_resposta.get("id")

    if not projeto_id:
        raise RuntimeError(
            f"Magic Hour não retornou o ID do projeto: {dados_resposta}"
        )

    return projeto_id


def _magic_consultar(projeto_id):
    urls = [
        f"{MAGIC_HOUR_BASE_URL}/video-projects/{projeto_id}",
        f"{MAGIC_HOUR_BASE_URL}/image-to-video/{projeto_id}",
    ]

    ultimo_erro = None

    for url in urls:
        try:
            resposta = requests.get(
                url,
                headers=_magic_headers(),
                timeout=60,
            )
        except Exception as erro:
            ultimo_erro = str(erro)
            continue

        if resposta.status_code == 200:
            return resposta.json()

        ultimo_erro = (
            f"HTTP {resposta.status_code}: "
            f"{resposta.text[:1000]}"
        )

    raise RuntimeError(
        f"Não foi possível consultar o projeto Magic Hour. "
        f"{ultimo_erro}"
    )


def _magic_encontrar_url(dados):
    if not isinstance(dados, dict):
        return None

    for campo in [
        "video_url",
        "download_url",
        "output_url",
        "url",
    ]:
        valor = dados.get(campo)
        if isinstance(valor, str) and valor.startswith("http"):
            return valor

    downloads = dados.get("downloads")

    if isinstance(downloads, dict):
        valores = downloads.values()
    elif isinstance(downloads, list):
        valores = downloads
    else:
        valores = []

    for item in valores:
        if isinstance(item, str) and item.startswith("http"):
            return item

        if isinstance(item, dict):
            for chave in [
                "url",
                "download_url",
                "video_url",
            ]:
                valor = item.get(chave)
                if isinstance(valor, str) and valor.startswith("http"):
                    return valor

    output = dados.get("output")

    if isinstance(output, dict):
        for valor in output.values():
            if isinstance(valor, str) and valor.startswith("http"):
                return valor

    return None


def _gerar_magic_hour(
    prompt,
    imagem_bytes=None,
    nome_imagem="imagem.png",
    duracao=5,
    nome_arquivo=None,
    **kwargs
):
    if not imagem_bytes:
        raise RuntimeError(
            "Magic Hour precisa de uma imagem de referência."
        )

    file_path = _magic_enviar_imagem(
        imagem_bytes,
        nome_imagem,
    )

    projeto_id = _magic_criar_video(
        file_path,
        prompt,
        duracao,
    )

    ultimo_resultado = {}
    video_url = None

    for _ in range(60):
        time.sleep(5)

        ultimo_resultado = _magic_consultar(projeto_id)

        status = str(
            ultimo_resultado.get("status", "processing")
        ).lower()

        video_url = _magic_encontrar_url(ultimo_resultado)

        if video_url:
            break

        if status in [
            "failed",
            "error",
            "cancelled",
            "canceled",
        ]:
            raise RuntimeError(
                f"Magic Hour informou falha: {ultimo_resultado}"
            )

    if not video_url:
        raise RuntimeError(
            "Magic Hour terminou o tempo de espera sem disponibilizar "
            f"o vídeo. Última resposta: {ultimo_resultado}"
        )

    arquivo = _baixar_url(
        video_url,
        nome_arquivo,
    )

    return {
        "video": arquivo,
        "motor": "Magic Hour",
    }


# ============================================================
# 🧠 PROMPT
# ============================================================

def _montar_prompt(
    descricao,
    camera="Sony FX6",
    proporcao="16:9",
    duracao=5,
):
    descricao = str(descricao).strip()

    if not descricao:
        raise ValueError("A descrição do vídeo não pode estar vazia.")

    camera = _validar_camera(camera)
    proporcao = _validar_proporcao(proporcao)
    duracao = _validar_duracao(duracao)

    return f"""
Crie um vídeo cinematográfico realista e consistente.

CENA:
{descricao}

CÂMERA:
{camera}

FORMATO:
{proporcao}

DURAÇÃO:
{duracao} segundos.

DIREÇÃO:
- aparência realista;
- movimento natural;
- câmera cinematográfica;
- iluminação natural;
- física realista;
- continuidade visual;
- manter personagens consistentes;
- manter rosto, cabelo, roupa e identidade consistentes;
- evitar deformações;
- movimentos suaves;
- composição cinematográfica.
""".strip()


# ============================================================
# 🎬 FUNÇÃO PRINCIPAL
# ============================================================

def gerar_video(
    descricao=None,
    prompt=None,
    camera="Sony FX6",
    proporcao="16:9",
    duracao=DURACAO_PADRAO,
    imagem_bytes=None,
    nome_imagem="imagem.png",
    nome_arquivo=None,
    width=None,
    height=None,
    **kwargs,
):
    _reativar_expirados()

    if descricao is None:
        descricao = prompt

    if descricao is None or not str(descricao).strip():
        raise ValueError(
            "É necessário informar a descrição do vídeo."
        )

    prompt_final = _montar_prompt(
        descricao,
        camera,
        proporcao,
        duracao,
    )

    nome_arquivo = nome_arquivo or _nome_arquivo()

    motores = [
        ("LTX-2.3 HF", _gerar_ltx_hf),
        ("Magic Hour", _gerar_magic_hour),
    ]

    erros = []

    for nome_motor, funcao in motores:
        if not _disponivel(nome_motor):
            continue

        try:
            resultado = funcao(
                prompt=prompt_final,
                imagem_bytes=imagem_bytes,
                nome_imagem=nome_imagem,
                duracao=duracao,
                width=width,
                height=height,
                camera=camera,
                proporcao=proporcao,
                nome_arquivo=nome_arquivo,
                **kwargs,
            )

            if not isinstance(resultado, dict):
                raise RuntimeError(
                    f"{nome_motor} retornou formato inválido."
                )

            caminho = resultado.get("video")

            if not caminho:
                raise RuntimeError(
                    f"{nome_motor} não retornou o caminho do vídeo."
                )

            caminho = Path(caminho)

            if not caminho.exists():
                raise RuntimeError(
                    f"{nome_motor} retornou um caminho inexistente."
                )

            if caminho.stat().st_size <= 0:
                raise RuntimeError(
                    f"{nome_motor} retornou um vídeo vazio."
                )

            _registrar_sucesso(nome_motor)

            return {
                "sucesso": True,
                "video": str(caminho),
                "motor": nome_motor,
                "mensagem": (
                    f"Vídeo gerado com sucesso pelo {nome_motor}."
                ),
            }

        except Exception as erro:
            texto = str(erro)
            erros.append(f"{nome_motor}: {texto}")

            if _eh_quota(erro):
                _bloquear_quota(nome_motor, erro)
            else:
                _registrar_erro(nome_motor, erro)

            continue

    return {
        "sucesso": False,
        "video": None,
        "motor": "nenhum",
        "mensagem": (
            "❌ NENHUM MOTOR DE VÍDEO CONSEGUIU GERAR O VÍDEO."
        ),
        "erro": "\n\n".join(erros),
        "erros_motores": erros,
    }


# ============================================================
# ⚙️ CONFIGURAÇÃO PARA O APP
# ============================================================

def mostrar_configuracao_video():
    st.markdown("### 🎬 Configuração do vídeo")

    camera = st.selectbox(
        "📷 Câmera",
        CAMERAS,
        index=1,
        key="video_camera_config",
    )

    proporcao = st.selectbox(
        "📐 Proporção",
        PROPORCOES,
        index=0,
        key="video_proporcao_config",
    )

    duracao = st.number_input(
        "⏱️ Duração",
        min_value=1,
        max_value=10,
        value=DURACAO_PADRAO,
        step=1,
        key="video_duracao_config",
    )

    return camera, proporcao, int(duracao)


# ============================================================
# 🔐 VERIFICAÇÕES
# ============================================================

def verificar_magic_hour():
    try:
        return bool(_magic_hour_api_key())
    except Exception:
        return False


def verificar_ltx():
    return bool(LTX_SPACE)


def tempo_bloqueio(nome_motor):
    _reativar_expirados()

    if nome_motor not in ESTADO_MOTORES:
        return 0

    restante = (
        _estado(nome_motor)["cooldown_until"] - time.time()
    )

    return max(0, int(restante))


def reativar_motor(nome_motor):
    if nome_motor not in ESTADO_MOTORES:
        return False

    estado = _estado(nome_motor)
    estado["cooldown_until"] = 0.0
    estado["quota"] = False
    estado["ultimo_erro"] = None
    estado["ativo"] = True

    return True


def desativar_motor(nome_motor):
    if nome_motor not in ESTADO_MOTORES:
        return False

    _estado(nome_motor)["ativo"] = False
    return True


def status_motores():
    _reativar_expirados()

    agora = time.time()
    resultado = []

    for nome, estado in ESTADO_MOTORES.items():
        restante = max(
            0,
            int(estado["cooldown_until"] - agora),
        )

        resultado.append({
            "motor": nome,
            "ativo": estado["ativo"],
            "disponivel": (
                estado["ativo"] and restante == 0
            ),
            "quota": estado["quota"],
            "bloqueado_segundos": restante,
            "erros": estado["erros"],
            "sucessos": estado["sucessos"],
            "ultimo_erro": estado["ultimo_erro"],
        })

    return resultado


def status_video():
    return {
        "motores": status_motores(),
        "cameras": CAMERAS,
        "proporcoes": PROPORCOES,
        "duracao_padrao": DURACAO_PADRAO,
        "reativacao_quota_segundos": TEMPO_REATIVACAO_QUOTA,
        "ltx_space": LTX_SPACE,
        "magic_hour": verificar_magic_hour(),
    }


# ============================================================
# 🎬 GERAR VÁRIOS CLIPES
# ============================================================

def gerar_clipes(
    descricoes,
    camera="Sony FX6",
    proporcao="16:9",
    duracao=5,
    imagem_bytes=None,
    nome_imagem="imagem.png",
):
    resultados = []

    if not descricoes:
        return resultados

    for indice, descricao in enumerate(descricoes, start=1):
        resultado = gerar_video(
            descricao=descricao,
            camera=camera,
            proporcao=proporcao,
            duracao=duracao,
            imagem_bytes=imagem_bytes,
            nome_imagem=nome_imagem,
            nome_arquivo=f"clipe_{indice:03d}.mp4",
        )

        resultados.append(resultado)

        if not resultado.get("sucesso"):
            break

    return resultados


# ============================================================
# 🔄 RESET
# ============================================================

def resetar_motor(nome_motor):
    if nome_motor not in ESTADO_MOTORES:
        return False

    estado = _estado(nome_motor)
    estado["cooldown_until"] = 0.0
    estado["quota"] = False
    estado["ultimo_erro"] = None
    estado["erros"] = 0
    estado["sucessos"] = 0
    estado["ativo"] = True

    return True


def resetar_todos_motores():
    for nome in ESTADO_MOTORES:
        resetar_motor(nome)


def testar_motores():
    return [
        {
            "motor": nome,
            "disponivel": _disponivel(nome),
            "tempo_bloqueio": tempo_bloqueio(nome),
        }
        for nome in ESTADO_MOTORES
    ]


# ============================================================
# 🧪 TESTE DIRETO
# ============================================================

if __name__ == "__main__":
    print("ALEX IA ULTRA — SISTEMA DE VÍDEO")
    print("Motores:", list(ESTADO_MOTORES.keys()))
    print("Fallback automático: ATIVADO")
