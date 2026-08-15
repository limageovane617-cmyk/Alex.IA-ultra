# ============================================================
# 🎬 ALEX IA ULTRA — GERENCIADOR DE VÍDEO
# ============================================================
# Motores confirmados:
#
# 1. LTX-2.3 via Hugging Face / Gradio Space
# 2. Magic Hour — LTX-2.3
#
# Sistema:
# - fallback automático
# - detecção de quota
# - bloqueio temporário
# - reativação automática
# - text-to-video
# - image-to-video
# ============================================================

from __future__ import annotations

import os
import time
import threading
from pathlib import Path
from typing import Any, Optional

import requests
import streamlit as st


# ============================================================
# CONFIGURAÇÕES
# ============================================================

PASTA_VIDEOS = Path("videos_gerados")
PASTA_VIDEOS.mkdir(
    parents=True,
    exist_ok=True
)

LTX_SPACE = (
    "https://lightricks-ltx-2-3.hf.space"
)

MAGIC_HOUR_BASE_URL = (
    "https://api.magichour.ai/v1"
)

TEMPO_REATIVACAO_QUOTA = 1800

DURACAO_PADRAO = 5


# ============================================================
# CÂMERAS
# ============================================================

CAMERAS = [

    "Sony FX5",

    "Sony FX6",

    "Canon EOS C80",

    "ARRI Alexa Mini LF",

]


# ============================================================
# PROPORÇÕES
# ============================================================

PROPORCOES = [

    "16:9",

    "9:16",

    "1:1",

]


# ============================================================
# ESTADO DOS MOTORES
# ============================================================

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
# ESTADO
# ============================================================

def _estado(nome):

    return ESTADO_MOTORES[nome]


# ============================================================
# REATIVAÇÃO AUTOMÁTICA
# ============================================================

def _reativar_expirados():

    agora = time.time()

    with LOCK:

        for nome, estado in ESTADO_MOTORES.items():

            if not estado["ativo"]:

                continue

            if (
                estado["cooldown_until"] > 0
                and estado["cooldown_until"] <= agora
            ):

                estado["cooldown_until"] = 0.0

                estado["quota"] = False

                estado["ultimo_erro"] = None

                print(
                    f"[VIDEO] ♻️ "
                    f"{nome} reativado automaticamente."
                )


# ============================================================
# MOTOR DISPONÍVEL
# ============================================================

def _disponivel(nome):

    _reativar_expirados()

    estado = _estado(nome)

    return (

        estado["ativo"]

        and estado["cooldown_until"]
        <= time.time()

    )


# ============================================================
# REGISTRAR SUCESSO
# ============================================================

def _registrar_sucesso(nome):

    estado = _estado(nome)

    estado["sucessos"] += 1

    estado["ultimo_erro"] = None

    estado["quota"] = False

    estado["cooldown_until"] = 0.0


# ============================================================
# REGISTRAR ERRO
# ============================================================

def _registrar_erro(
    nome,
    erro
):

    estado = _estado(nome)

    estado["erros"] += 1

    estado["ultimo_erro"] = str(
        erro
    )


# ============================================================
# DETECTAR QUOTA
# ============================================================

def _eh_quota(erro):

    texto = str(
        erro
    ).lower()

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

    return any(

        palavra in texto

        for palavra in palavras

    )


# ============================================================
# BLOQUEAR POR QUOTA
# ============================================================

def _bloquear_quota(
    nome,
    erro
):

    estado = _estado(nome)

    estado["quota"] = True

    estado["erros"] += 1

    estado["ultimo_erro"] = str(
        erro
    )

    estado["cooldown_until"] = (

        time.time()

        + TEMPO_REATIVACAO_QUOTA

    )

    print(
        f"[VIDEO] ⚠️ QUOTA: {nome}"
    )

    print(
        "[VIDEO] 🔒 Motor temporariamente bloqueado."
    )


# ============================================================
# NOME DE ARQUIVO
# ============================================================

def _nome_arquivo(
    prefixo="video"
):

    return (

        f"{prefixo}_"

        f"{int(time.time() * 1000)}"

        ".mp4"

    )


# ============================================================
# VALIDAR CÂMERA
# ============================================================

def _validar_camera(
    camera
):

    if camera in CAMERAS:

        return camera

    return "Sony FX6"


# ============================================================
# VALIDAR PROPORÇÃO
# ============================================================

def _validar_proporcao(
    proporcao
):

    if proporcao in PROPORCOES:

        return proporcao

    return "16:9"


# ============================================================
# VALIDAR DURAÇÃO
# ============================================================

def _validar_duracao(
    duracao
):

    try:

        valor = int(
            float(duracao)
        )

    except Exception:

        valor = DURACAO_PADRAO

    if valor <= 0:

        valor = DURACAO_PADRAO

    return valor


# ============================================================
# SALVAR VÍDEO
# ============================================================

def _salvar_video(
    origem,
    nome_arquivo=None
):

    origem = Path(
        origem
    )

    if not origem.exists():

        raise RuntimeError(
            f"Vídeo não encontrado: {origem}"
        )

    if origem.stat().st_size <= 0:

        raise RuntimeError(
            "O vídeo está vazio."
        )

    if nome_arquivo:

        nome = Path(
            nome_arquivo
        ).name

    else:

        nome = origem.name

    if not nome.lower().endswith(
        ".mp4"
    ):

        nome += ".mp4"

    destino = (
        PASTA_VIDEOS
        / nome
    )

    if destino.resolve() != origem.resolve():

        destino.write_bytes(
            origem.read_bytes()
        )

    if not destino.exists():

        raise RuntimeError(
            "Não foi possível salvar o vídeo."
        )

    if destino.stat().st_size <= 0:

        raise RuntimeError(
            "O vídeo salvo está vazio."
        )

    return str(
        destino
    )


# ============================================================
# BAIXAR URL
# ============================================================

def _baixar_url(
    url,
    nome_arquivo=None
):

    if not isinstance(
        url,
        str
    ) or not url.startswith(
        "http"
    ):

        raise RuntimeError(
            "URL do vídeo inválida."
        )

    resposta = requests.get(
        url,
        timeout=180
    )

    if resposta.status_code != 200:

        raise RuntimeError(
            f"Falha ao baixar vídeo. "
            f"HTTP {resposta.status_code}: "
            f"{resposta.text[:1000]}"
        )

    if not resposta.content:

        raise RuntimeError(
            "O download retornou vazio."
        )

    nome = (
        nome_arquivo
        or _nome_arquivo()
    )

    if not nome.lower().endswith(
        ".mp4"
    ):

        nome += ".mp4"

    destino = (
        PASTA_VIDEOS
        / Path(nome).name
    )

    destino.write_bytes(
        resposta.content
    )

    if destino.stat().st_size <= 0:

        raise RuntimeError(
            "O vídeo baixado está vazio."
        )

    return str(
        destino
        )
    # ============================================================
# 🎬 MOTOR 1 — LTX-2.3 HUGGING FACE / GRADIO
# ============================================================

def _gerar_ltx_hf(
    prompt,
    imagem_bytes=None,
    nome_imagem="imagem.png",
    duracao=5,
    width=512,
    height=512,
    **kwargs
):

    try:

        from gradio_client import Client

    except Exception as erro:

        raise RuntimeError(
            "gradio_client não está instalado. "
            "Adicione gradio_client ao requirements.txt."
        ) from erro


    print(
        "[VIDEO] 🔌 Conectando ao LTX-2.3..."
    )


    client = Client(
        LTX_SPACE
    )


    # --------------------------------------------------------
    # Imagem opcional
    # --------------------------------------------------------

    caminho_imagem = None

    if imagem_bytes:

        pasta_temp = (
            PASTA_VIDEOS
            / "temp"
        )

        pasta_temp.mkdir(
            parents=True,
            exist_ok=True
        )

        caminho_imagem = (
            pasta_temp
            / Path(
                nome_imagem
            ).name
        )

        caminho_imagem.write_bytes(
            imagem_bytes
        )


    # --------------------------------------------------------
    # Dimensões
    # --------------------------------------------------------

    try:

        largura = int(
            width
        )

    except Exception:

        largura = 512


    try:

        altura = int(
            height
        )

    except Exception:

        altura = 512


    # --------------------------------------------------------
    # Chamada real do Space
    # --------------------------------------------------------

    print(
        "[VIDEO] 🎥 Gerando com LTX-2.3..."
    )


    resultado = client.predict(

        input_image=(
            str(caminho_imagem)
            if caminho_imagem
            else None
        ),

        prompt=str(
            prompt
        ),

        duration=(
            float(duracao)
        ),

        enhance_prompt=True,

        seed=0,

        randomize_seed=True,

        height=altura,

        width=largura,

        api_name="/generate_video"

    )


    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    if not resultado:

        raise RuntimeError(
            "LTX-2.3 retornou uma resposta vazia."
        )


    caminho = None

    seed = None


    if isinstance(
        resultado,
        (tuple, list)
    ):

        if len(resultado) >= 1:

            caminho = resultado[0]

        if len(resultado) >= 2:

            seed = resultado[1]

    else:

        caminho = resultado


    if not caminho:

        raise RuntimeError(
            "LTX-2.3 não retornou o caminho do vídeo."
        )


    caminho = Path(
        str(caminho)
    )


    if not caminho.exists():

        raise RuntimeError(
            "O LTX-2.3 informou um vídeo, "
            "mas o arquivo não foi encontrado."
        )


    arquivo = _salvar_video(
        caminho
    )


    print(
        "[VIDEO] ✅ LTX-2.3 gerou o vídeo."
    )


    return {

        "video": arquivo,

        "motor": "LTX-2.3 HF",

        "seed": seed,

    }


# ============================================================
# 🔐 MAGIC HOUR — API KEY
# ============================================================

def _magic_hour_api_key():

    try:

        chave = st.secrets.get(
            "MAGIC_HOUR_API_KEY",
            ""
        )

    except Exception:

        chave = ""


    if not chave:

        chave = os.environ.get(
            "MAGIC_HOUR_API_KEY",
            ""
        )


    chave = str(
        chave
    ).strip()


    if not chave:

        raise RuntimeError(
            "MAGIC_HOUR_API_KEY não está "
            "configurada nos Secrets."
        )


    return chave


# ============================================================
# 🔐 MAGIC HOUR — HEADERS
# ============================================================

def _magic_headers():

    chave = _magic_hour_api_key()

    return {

        "Authorization":
            f"Bearer {chave}",

        "Accept":
            "application/json",

        "Content-Type":
            "application/json",

    }


# ============================================================
# 📤 MAGIC HOUR — URL DE UPLOAD
# ============================================================

def _magic_obter_upload_url(
    extensao
):

    extensao = (
        str(extensao)
        .lower()
        .replace(
            ".",
            ""
        )
    )


    extensoes = [

        "png",

        "jpg",

        "jpeg",

        "webp",

        "jfif",

        "heic",

        "heif",

        "avif",

        "bmp",

        "tif",

        "tiff",

    ]


    if extensao not in extensoes:

        raise RuntimeError(
            f"Formato não suportado: {extensao}"
        )


    dados = {

        "items": [

            {

                "type": "image",

                "extension": extensao

            }

        ]

    }


    resposta = requests.post(

        f"{MAGIC_HOUR_BASE_URL}"
        "/files/upload-urls",

        headers=_magic_headers(),

        json=dados,

        timeout=60

    )


    if resposta.status_code != 200:

        try:

            detalhes = resposta.json()

        except Exception:

            detalhes = resposta.text


        raise RuntimeError(

            "Magic Hour falhou ao "
            "obter URL de upload.\n\n"

            f"HTTP {resposta.status_code}\n"

            f"{detalhes}"

        )


    dados_resposta = resposta.json()


    itens = dados_resposta.get(
        "items"
    )


    if not itens:

        raise RuntimeError(
            "Magic Hour não retornou "
            "os dados de upload."
        )


    item = itens[0]


    upload_url = item.get(
        "upload_url"
    )

    file_path = item.get(
        "file_path"
    )


    if not upload_url or not file_path:

        raise RuntimeError(
            "Magic Hour não retornou "
            "upload_url/file_path."
        )


    return (
        upload_url,
        file_path
    )


# ============================================================
# 🖼️ MAGIC HOUR — ENVIAR IMAGEM
# ============================================================

def _magic_enviar_imagem(
    imagem_bytes,
    nome_imagem
):

    extensao = Path(
        nome_imagem
    ).suffix.lower()


    upload_url, file_path = (
        _magic_obter_upload_url(
            extensao
        )
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

            "Falha no upload da imagem "
            "para o Magic Hour.\n\n"

            f"HTTP {resposta.status_code}\n"

            f"{resposta.text[:1000]}"

        )


    return file_path


# ============================================================
# 🎬 MAGIC HOUR — CRIAR VÍDEO
# ============================================================

def _magic_criar_video(
    file_path,
    prompt,
    duracao=5
):

    dados = {

        "name":
            "Alex IA Ultra",

        "end_seconds":
            int(duracao),

        "model":
            "ltx-2.3",

        "resolution":
            "480p",

        "audio":
            False,

        "style": {

            "prompt":
                str(prompt).strip()

        },

        "assets": {

            "image_file_path":
                file_path

        }

    }


    resposta = requests.post(

        f"{MAGIC_HOUR_BASE_URL}"
        "/image-to-video",

        headers=_magic_headers(),

        json=dados,

        timeout=120

    )


    if resposta.status_code not in [
        200,
        201,
        202
    ]:

        try:

            detalhes = resposta.json()

        except Exception:

            detalhes = resposta.text


        raise RuntimeError(

            "Magic Hour falhou ao "
            "criar o vídeo.\n\n"

            f"HTTP {resposta.status_code}\n"

            f"{detalhes}"

        )


    dados_resposta = (
        resposta.json()
    )


    projeto_id = dados_resposta.get(
        "id"
    )


    if not projeto_id:

        raise RuntimeError(

            "Magic Hour não retornou "
            "o ID do projeto.\n\n"

            f"{dados_resposta}"

        )


    return (
        projeto_id,
        dados_resposta
    )


# ============================================================
# 🔎 MAGIC HOUR — CONSULTAR PROJETO
# ============================================================

def _magic_consultar(
    projeto_id
):

    urls = [

        f"{MAGIC_HOUR_BASE_URL}"
        f"/video-projects/{projeto_id}",

        f"{MAGIC_HOUR_BASE_URL}"
        f"/image-to-video/{projeto_id}",

    ]


    ultimo_erro = None


    for url in urls:

        try:

            resposta = requests.get(

                url,

                headers=_magic_headers(),

                timeout=60

            )

        except Exception as erro:

            ultimo_erro = str(
                erro
            )

            continue


        if resposta.status_code == 200:

            try:

                return resposta.json()

            except Exception:

                return {}


        ultimo_erro = (

            f"HTTP {resposta.status_code}: "

            f"{resposta.text[:1000]}"

        )


    raise RuntimeError(

        "Não foi possível consultar "
        "o projeto Magic Hour.\n\n"

        f"{ultimo_erro}"

    )


# ============================================================
# 🔗 MAGIC HOUR — ENCONTRAR VÍDEO
# ============================================================

def _magic_encontrar_url(
    dados
):

    if not isinstance(
        dados,
        dict
    ):

        return None


    campos = [

        "video_url",

        "download_url",

        "output_url",

        "url",

    ]


    for campo in campos:

        valor = dados.get(
            campo
        )

        if (

            isinstance(
                valor,
                str
            )

            and valor.startswith(
                "http"
            )

        ):

            return valor


    downloads = dados.get(
        "downloads"
    )


    if isinstance(
        downloads,
        dict
    ):

        valores = downloads.values()

    elif isinstance(
        downloads,
        list
    ):

        valores = downloads

    else:

        valores = []


    for item in valores:

        if (

            isinstance(
                item,
                str
            )

            and item.startswith(
                "http"
            )

        ):

            return item


        if isinstance(
            item,
            dict
        ):

            for chave in [

                "url",

                "download_url",

                "video_url",

            ]:

                valor = item.get(
                    chave
                )


                if (

                    isinstance(
                        valor,
                        str
                    )

                    and valor.startswith(
                        "http"
                    )

                ):

                    return valor


    output = dados.get(
        "output"
    )


    if isinstance(
        output,
        dict
    ):

        for valor in output.values():

            if (

                isinstance(
                    valor,
                    str
                )

                and valor.startswith(
                    "http"
                )

            ):

                return valor


    return None

# ============================================================
# 🎬 MOTOR 2 — MAGIC HOUR COMPLETO
# ============================================================

def _gerar_magic_hour(
    prompt,
    imagem_bytes=None,
    nome_imagem="imagem.png",
    duracao=5,
    **kwargs
):

    if not imagem_bytes:

        raise RuntimeError(
            "O Magic Hour precisa de "
            "uma imagem de referência."
        )


    print(
        "[VIDEO] 🔌 Conectando ao Magic Hour..."
    )


    # --------------------------------------------------------
    # 1 — Upload da imagem
    # --------------------------------------------------------

    file_path = _magic_enviar_imagem(

        imagem_bytes,

        nome_imagem

    )


    print(
        "[VIDEO] ✅ Imagem enviada ao Magic Hour."
    )


    # --------------------------------------------------------
    # 2 — Criar projeto
    # --------------------------------------------------------

    projeto_id, resposta = (
        _magic_criar_video(

            file_path,

            prompt,

            duracao

        )
    )


    print(
        f"[VIDEO] 🎬 Projeto Magic Hour: "
        f"{projeto_id}"
    )


    # --------------------------------------------------------
    # 3 — Aguardar processamento
    # --------------------------------------------------------

    ultimo_resultado = {}

    video_url = None


    # Até aproximadamente 5 minutos

    for tentativa in range(60):

        time.sleep(5)


        ultimo_resultado = (
            _magic_consultar(
                projeto_id
            )
        )


        status = str(

            ultimo_resultado.get(
                "status",
                "processing"
            )

        ).lower()


        print(
            f"[VIDEO] ⏳ Magic Hour: "
            f"{status}"
        )


        video_url = (
            _magic_encontrar_url(
                ultimo_resultado
            )
        )


        if video_url:

            break


        if status in [

            "failed",

            "error",

            "cancelled",

            "canceled",

        ]:

            raise RuntimeError(

                "Magic Hour informou "
                "que a geração falhou.\n\n"

                f"{ultimo_resultado}"

            )


    # --------------------------------------------------------
    # 4 — Verificar URL
    # --------------------------------------------------------

    if not video_url:

        raise RuntimeError(

            "Magic Hour terminou o tempo "
            "de espera sem disponibilizar "
            "o vídeo.\n\n"

            f"Última resposta:\n"
            f"{ultimo_resultado}"

        )


    # --------------------------------------------------------
    # 5 — Download
    # --------------------------------------------------------

    arquivo = _baixar_url(
        video_url
    )


    print(
        "[VIDEO] ✅ Magic Hour gerou o vídeo."
    )


    return {

        "video": arquivo,

        "motor": "Magic Hour",

    }


# ============================================================
# 🧠 PROMPT CINEMATOGRÁFICO
# ============================================================

def _montar_prompt(
    descricao,
    camera="Sony FX6",
    proporcao="16:9",
    duracao=5
):

    descricao = str(
        descricao
    ).strip()


    if not descricao:

        raise ValueError(
            "A descrição do vídeo "
            "não pode estar vazia."
        )


    camera = _validar_camera(
        camera
    )


    proporcao = _validar_proporcao(
        proporcao
    )


    duracao = _validar_duracao(
        duracao
    )


    return f"""
Crie um vídeo cinematográfico
realista e consistente.

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
- manter rosto consistente;
- manter cabelo consistente;
- manter roupa consistente;
- manter identidade consistente;
- evitar deformações;
- evitar mudanças desnecessárias;
- movimentos suaves;
- composição cinematográfica.

A aparência dos personagens
deve permanecer consistente
durante toda a sequência.
""".strip()


# ============================================================
# 🎬 GERAR VÍDEO — SISTEMA PRINCIPAL
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
    width=512,
    height=512,
    **kwargs
):

    """
    Função principal usada pelo app.py.

    Aceita tanto:

        gerar_video(
            descricao="..."
        )

    quanto:

        gerar_video(
            prompt="..."
        )

    O sistema tenta:

        1. LTX-2.3 HF
        2. Magic Hour

    Se o primeiro atingir quota,
    ele é bloqueado temporariamente
    e o segundo é utilizado.

    Quando o tempo terminar,
    o primeiro é reativado automaticamente.
    """


    _reativar_expirados()


    # --------------------------------------------------------
    # Compatibilidade entre prompt e descricao
    # --------------------------------------------------------

    if descricao is None:

        descricao = prompt


    if descricao is None:

        raise ValueError(
            "É necessário informar "
            "a descrição do vídeo."
        )


    descricao = str(
        descricao
    ).strip()


    if not descricao:

        raise ValueError(
            "A descrição do vídeo "
            "não pode estar vazia."
        )


    # --------------------------------------------------------
    # Prompt cinematográfico
    # --------------------------------------------------------

    prompt_final = _montar_prompt(

        descricao,

        camera,

        proporcao,

        duracao

    )


    # --------------------------------------------------------
    # Nome
    # --------------------------------------------------------

    if not nome_arquivo:

        nome_arquivo = (
            _nome_arquivo()
        )


    # --------------------------------------------------------
    # Lista de motores
    # --------------------------------------------------------

    motores = [

        (
            "LTX-2.3 HF",
            _gerar_ltx_hf
        ),

        (
            "Magic Hour",
            _gerar_magic_hour
        ),

    ]


    erros = []


    # ========================================================
    # FALLBACK AUTOMÁTICO
    # ========================================================

    for numero, (nome_motor, funcao) in enumerate(

        motores,

        start=1

    ):


        # ----------------------------------------------------
        # Verificar disponibilidade
        # ----------------------------------------------------

        if not _disponivel(
            nome_motor
        ):

            restante = max(

                0,

                int(

                    _estado(
                        nome_motor
                    )[
                        "cooldown_until"
                    ]

                    - time.time()

                )

            )


            print(

                f"[VIDEO] ⏭️ "
                f"{nome_motor} indisponível. "
                f"Restam {restante}s."

            )


            continue


        print("")
        print(
            "========================================"
        )

        print(

            f"[VIDEO] 🎬 MOTOR "
            f"{numero}/{len(motores)}"

        )

        print(
            f"[VIDEO] {nome_motor}"
        )

        print(
            "========================================"
        )


        try:

            # ------------------------------------------------
            # Chamada do motor
            # ------------------------------------------------

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

                **kwargs

            )


            # ------------------------------------------------
            # Confirmar resultado
            # ------------------------------------------------

            if not isinstance(
                resultado,
                dict
            ):

                raise RuntimeError(

                    f"{nome_motor} "
                    "retornou formato inválido."

                )


            caminho = resultado.get(
                "video"
            )


            if not caminho:

                raise RuntimeError(

                    f"{nome_motor} "
                    "não retornou o caminho "
                    "do vídeo."

                )


            caminho = Path(
                caminho
            )


            if not caminho.exists():

                raise RuntimeError(

                    f"{nome_motor} "
                    "retornou um caminho "
                    "que não existe."

                )


            if caminho.stat().st_size <= 0:

                raise RuntimeError(

                    f"{nome_motor} "
                    "retornou um vídeo vazio."

                )


            # ------------------------------------------------
            # Sucesso
            # ------------------------------------------------

            _registrar_sucesso(
                nome_motor
            )


            print(
                f"[VIDEO] 🎉 "
                f"SUCESSO: {nome_motor}"
            )


            return {

                "sucesso":
                    True,

                "video":
                    str(caminho),

                "motor":
                    nome_motor,

                "mensagem":
                    (
                        "Vídeo gerado com sucesso "
                        f"pelo {nome_motor}."
                    ),

            }


        except Exception as erro:

            texto = str(
                erro
            )


            erros.append(

                f"{nome_motor}: "
                f"{texto}"

            )


            # ------------------------------------------------
            # QUOTA
            # ------------------------------------------------

            if _eh_quota(
                erro
            ):

                _bloquear_quota(

                    nome_motor,

                    erro

                )


                print(
                    "[VIDEO] 🔄 FALLBACK "
                    "ATIVADO."
                )


                continue


            # ------------------------------------------------
            # Erro normal
            # ------------------------------------------------

            _registrar_erro(

                nome_motor,

                erro

            )


            print(

                f"[VIDEO] ❌ "
                f"{nome_motor}: "
                f"{texto}"

            )


            print(

                "[VIDEO] 🔄 "
                "Tentando próximo motor..."

            )


            continue


    # ========================================================
    # ❌ TODOS OS MOTORES FALHARAM
    # ========================================================

    print("")
    print("========================================")
    print("❌ NENHUM MOTOR DE VÍDEO CONSEGUIU GERAR")
    print("========================================")

    erro_completo = "\n\n".join(erros)

    print("")
    print("🔎 ERROS DOS MOTORES:")
    print(erro_completo)

    return {

        "sucesso":
            False,

        "video":
            None,

        "motor":
            "nenhum",

        "mensagem":
            (
                "❌ NENHUM MOTOR DE VÍDEO "
                "CONSEGUIU GERAR O VÍDEO."
            ),

        "erro":
            erro_completo,

        "erros_motores":
            erros,

    }

# ============================================================
# ⚙️ CONFIGURAÇÃO DE VÍDEO PARA O APP
# ============================================================

def mostrar_configuracao_video():
    """
    Mostra as opções de vídeo dentro do Streamlit
    e retorna:

        camera
        proporcao
        duracao
    """

    st.markdown("### 🎬 Configuração do vídeo")

    camera = st.selectbox(
        "📷 Câmera",
        CAMERAS,
        index=1,
        key="video_camera_config"
    )

    proporcao = st.selectbox(
        "📐 Proporção",
        PROPORCOES,
        index=0,
        key="video_proporcao_config"
    )

    duracao = st.number_input(
        "⏱️ Duração",
        min_value=1,
        max_value=60,
        value=DURACAO_PADRAO,
        step=1,
        key="video_duracao_config"
    )

    return (
        camera,
        proporcao,
        int(duracao)
    )


# ============================================================
# 🔐 VERIFICAR MAGIC HOUR
# ============================================================

def verificar_magic_hour():
    """
    Verifica se a API Key do Magic Hour está configurada.
    """

    try:

        chave = _magic_hour_api_key()

        return bool(chave)

    except Exception:

        return False


# ============================================================
# 🔐 VERIFICAR LTX-2.3
# ============================================================

def verificar_ltx():
    """
    O LTX-2.3 via Hugging Face Space não precisa
    de API Key para o teste que você fez.
    """

    return bool(LTX_SPACE)


# ============================================================
# ⏱️ TEMPO RESTANTE DO BLOQUEIO
# ============================================================

def tempo_bloqueio(
    nome_motor
):

    _reativar_expirados()

    if nome_motor not in ESTADO_MOTORES:

        return 0

    restante = (

        _estado(
            nome_motor
        )[
            "cooldown_until"
        ]

        - time.time()

    )

    if restante <= 0:

        return 0

    return int(
        restante
    )


# ============================================================
# 🔄 REATIVAR MOTOR MANUALMENTE
# ============================================================

def reativar_motor(
    nome_motor
):

    if nome_motor not in ESTADO_MOTORES:

        return False

    estado = _estado(
        nome_motor
    )

    estado["cooldown_until"] = 0.0

    estado["quota"] = False

    estado["ultimo_erro"] = None

    estado["ativo"] = True

    print(
        f"[VIDEO] ♻️ "
        f"{nome_motor} reativado."
    )

    return True


# ============================================================
# ⛔ DESATIVAR MOTOR
# ============================================================

def desativar_motor(
    nome_motor
):

    if nome_motor not in ESTADO_MOTORES:

        return False

    _estado(
        nome_motor
    )[
        "ativo"
    ] = False

    return True


# ============================================================
# 📋 STATUS DOS MOTORES
# ============================================================

def status_motores():

    _reativar_expirados()

    resultado = []

    agora = time.time()


    for nome, estado in ESTADO_MOTORES.items():

        restante = max(

            0,

            int(

                estado["cooldown_until"]
                - agora

            )

        )


        resultado.append({

            "motor":
                nome,

            "ativo":
                estado["ativo"],

            "disponivel":
                (
                    estado["ativo"]
                    and restante == 0
                ),

            "quota":
                estado["quota"],

            "bloqueado_segundos":
                restante,

            "erros":
                estado["erros"],

            "sucessos":
                estado["sucessos"],

            "ultimo_erro":
                estado["ultimo_erro"],

        })


    return resultado


# ============================================================
# 📊 STATUS GERAL DO SISTEMA
# ============================================================

def status_video():

    _reativar_expirados()

    return {

        "motores":
            status_motores(),

        "cameras":
            CAMERAS,

        "proporcoes":
            PROPORCOES,

        "duracao_padrao":
            DURACAO_PADRAO,

        "reativacao_quota_segundos":
            TEMPO_REATIVACAO_QUOTA,

        "ltx_space":
            LTX_SPACE,

        "magic_hour":
            verificar_magic_hour(),

    }


# ============================================================
# 🧪 TESTE DOS MOTORES
# ============================================================

def testar_motores():

    resultados = []

    for nome in ESTADO_MOTORES:

        resultados.append({

            "motor":
                nome,

            "disponivel":
                _disponivel(nome),

            "tempo_bloqueio":
                tempo_bloqueio(nome),

        })

    return resultados


# ============================================================
# 🎬 GERAR VÁRIOS CLIPES
# ============================================================

def gerar_clipes(
    descricoes,
    camera="Sony FX6",
    proporcao="16:9",
    duracao=5,
    imagem_bytes=None,
    nome_imagem="imagem.png"
):

    """
    Divide um projeto maior em vários clipes.

    Exemplo:

        cena 1 → vídeo
        cena 2 → vídeo
        cena 3 → vídeo

    O fallback continua funcionando
    individualmente em cada clipe.
    """

    resultados = []


    if not descricoes:

        return resultados


    for indice, descricao in enumerate(

        descricoes,

        start=1

    ):

        print("")

        print(
            f"[VIDEO] 🎬 "
            f"CLIP {indice}/"
            f"{len(descricoes)}"
        )


        nome = (

            f"clipe_"
            f"{indice:03d}.mp4"

        )


        resultado = gerar_video(

            descricao=descricao,

            camera=camera,

            proporcao=proporcao,

            duracao=duracao,

            imagem_bytes=imagem_bytes,

            nome_imagem=nome_imagem,

            nome_arquivo=nome,

        )


        resultados.append(
            resultado
        )


        if not resultado.get(
            "sucesso"
        ):

            print(
                "[VIDEO] ❌ "
                "Falha no clipe."
            )

            break


    return resultados


# ============================================================
# 🔄 RESETAR ESTATÍSTICAS
# ============================================================

def resetar_motor(
    nome_motor
):

    if nome_motor not in ESTADO_MOTORES:

        return False

    estado = _estado(
        nome_motor
    )

    estado["cooldown_until"] = 0.0

    estado["quota"] = False

    estado["ultimo_erro"] = None

    estado["erros"] = 0

    estado["sucessos"] = 0

    estado["ativo"] = True

    return True


# ============================================================
# 🧹 RESETAR TODOS
# ============================================================

def resetar_todos_motores():

    for nome in ESTADO_MOTORES:

        resetar_motor(
            nome
        )


# ============================================================
# 🧪 TESTE DIRETO
# ============================================================

if __name__ == "__main__":

    print("")
    print(
        "=========================================="
    )

    print(
        "🎬 ALEX IA ULTRA — SISTEMA DE VÍDEO"
    )

    print(
        "=========================================="
    )

    print("")

    print(
        "Motores:"
    )

    for nome in ESTADO_MOTORES:

        print(
            f" • {nome}"
        )

    print("")

    print(
        "Fallback automático: ATIVADO"
    )

    print(
        "Detecção de quota: ATIVADA"
    )

    print(
        "Reativação automática: ATIVADA"
    )

    print("")

    print(
        status_video()
    )
