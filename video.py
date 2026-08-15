# ============================================================
# 🎬 ALEX IA ULTRA — GERENCIADOR DE VÍDEO
# Fallback + quota + reativação automática
# Compatível com app.py / servicos.py
# ============================================================

from __future__ import annotations

import io
import time
import uuid
from pathlib import Path

import streamlit as st
from google.genai import types

from servicos import (
    criar_cliente_gemini,
    criar_cliente_huggingface,
)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

PASTA_VIDEOS = Path("videos_gerados")
PASTA_VIDEOS.mkdir(parents=True, exist_ok=True)

DURACAO_PADRAO = 8

# Tempo de bloqueio quando um motor atinge quota.
# 1800 segundos = 30 minutos.
TEMPO_REATIVACAO_QUOTA = 1800

MODELO_VEO = "veo-3.1-generate-preview"


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

def _estado_motores():

    if "video_motores" not in st.session_state:

        st.session_state.video_motores = {

            "Veo 3.1": {
                "ativo": True,
                "bloqueado_ate": 0.0,
                "erros": 0,
                "sucessos": 0,
                "ultimo_erro": "",
            },

            "Hugging Face": {
                "ativo": True,
                "bloqueado_ate": 0.0,
                "erros": 0,
                "sucessos": 0,
                "ultimo_erro": "",
            },

        }

    return st.session_state.video_motores


# ============================================================
# REATIVAÇÃO AUTOMÁTICA
# ============================================================

def _reativar_motores_expirados():

    agora = time.time()

    motores = _estado_motores()

    for dados in motores.values():

        if (
            dados["bloqueado_ate"] > 0
            and dados["bloqueado_ate"] <= agora
        ):

            dados["bloqueado_ate"] = 0.0
            dados["ultimo_erro"] = ""

            print(
                "[VIDEO] ♻️ Motor "
                "reativado automaticamente."
            )


# ============================================================
# MOTOR DISPONÍVEL
# ============================================================

def _motor_disponivel(nome):

    motores = _estado_motores()

    dados = motores[nome]

    if not dados["ativo"]:
        return False

    return time.time() >= dados["bloqueado_ate"]


# ============================================================
# DETECTAR QUOTA
# ============================================================

def _erro_e_quota(erro):

    texto = str(erro).lower()

    sinais = [

        "429",

        "quota",

        "resource_exhausted",

        "resource exhausted",

        "rate limit",

        "rate_limit",

        "too many requests",

        "limit exceeded",

        "daily limit",

        "usage limit",

        "capacity exceeded",

    ]

    return any(
        sinal in texto
        for sinal in sinais
    )


# ============================================================
# BLOQUEAR MOTOR
# ============================================================

def _bloquear_por_quota(
    nome,
    erro,
):

    dados = _estado_motores()[nome]

    dados["bloqueado_ate"] = (
        time.time()
        + TEMPO_REATIVACAO_QUOTA
    )

    dados["ultimo_erro"] = str(erro)

    dados["erros"] += 1

    print(
        f"[VIDEO] ⚠️ {nome} "
        "atingiu quota."
    )

    print(
        f"[VIDEO] ⏱️ Bloqueado por "
        f"{TEMPO_REATIVACAO_QUOTA} segundos."
    )


# ============================================================
# ERRO NORMAL
# ============================================================

def _registrar_erro(
    nome,
    erro,
):

    dados = _estado_motores()[nome]

    dados["ultimo_erro"] = str(erro)

    dados["erros"] += 1


# ============================================================
# SUCESSO
# ============================================================

def _registrar_sucesso(
    nome,
):

    dados = _estado_motores()[nome]

    dados["bloqueado_ate"] = 0.0

    dados["ultimo_erro"] = ""

    dados["sucessos"] += 1


# ============================================================
# CONFIGURAÇÃO DO VÍDEO
# ============================================================

def mostrar_configuracao_video():

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

    duracao = st.selectbox(
        "⏱️ Duração",
        [8],
        index=0,
        key="video_duracao_config",
        help=(
            "Os clipes deste sistema "
            "usam 8 segundos."
        ),
    )

    return (
        camera,
        proporcao,
        duracao,
    )


# ============================================================
# MAGIC HOUR
# ============================================================

def verificar_magic_hour(
    *args,
    **kwargs,
):

    return bool(
        kwargs.get(
            "ativo",
            False,
        )
        or kwargs.get(
            "magic_hour",
            False,
        )
    )


# ============================================================
# PROMPT CINEMATOGRÁFICO
# ============================================================

def _montar_prompt(
    prompt,
    camera,
    proporcao,
):

    return f"""
Crie um vídeo cinematográfico
realista e fotorealista.

CENA:

{prompt}

CÂMERA:

{camera}

FORMATO:

{proporcao}

DIREÇÃO CINEMATOGRÁFICA:

- iluminação realista;
- movimentos naturais;
- câmera estável;
- profundidade cinematográfica;
- física natural;
- continuidade temporal;
- personagens consistentes;
- ambiente consistente;
- preservar rosto e identidade;
- preservar roupa e aparência;
- não criar personagens extras sem necessidade;
- evitar deformações;
- evitar mudanças repentinas de aparência;
- manter a câmera consistente durante o clipe.
""".strip()


# ============================================================
# NOMES DE ARQUIVOS
# ============================================================

def _novo_arquivo(
    prefixo="video",
):

    return (
        PASTA_VIDEOS
        / f"{prefixo}_"
        f"{uuid.uuid4().hex[:12]}"
        ".mp4"
    )


# ============================================================
# SALVAR BYTES
# ============================================================

def _salvar_bytes(
    dados,
    caminho=None,
):

    if not dados:

        raise RuntimeError(
            "O motor retornou "
            "dados vazios."
        )

    caminho = (
        caminho
        or _novo_arquivo()
    )

    caminho.write_bytes(
        dados
    )

    if (
        not caminho.exists()
        or caminho.stat().st_size <= 0
    ):

        raise RuntimeError(
            "O arquivo de vídeo "
            "ficou vazio."
        )

    return str(caminho)


# ============================================================
# EXTRAIR RESPOSTA DE VÍDEO
# ============================================================

def _salvar_resposta(
    resposta,
    caminho=None,
):

    if resposta is None:

        raise RuntimeError(
            "Resposta vazia."
        )


    # bytes

    if isinstance(
        resposta,
        bytes,
    ):

        return _salvar_bytes(
            resposta,
            caminho,
        )


    # bytearray

    if isinstance(
        resposta,
        bytearray,
    ):

        return _salvar_bytes(
            bytes(resposta),
            caminho,
        )


    # caminho de arquivo

    if isinstance(
        resposta,
        (str, Path),
    ):

        origem = Path(
            resposta
        )

        if origem.exists():

            destino = (
                caminho
                or (
                    PASTA_VIDEOS
                    / origem.name
                )
            )

            destino.write_bytes(
                origem.read_bytes()
            )

            if destino.stat().st_size <= 0:

                raise RuntimeError(
                    "Arquivo vazio."
                )

            return str(
                destino
            )


    # dicionário

    if isinstance(
        resposta,
        dict,
    ):

        chaves = [

            "video",
            "video_bytes",
            "bytes",
            "content",
            "data",
            "output",
            "path",
            "file",

        ]

        for chave in chaves:

            if chave not in resposta:
                continue

            valor = resposta[
                chave
            ]

            if valor is None:
                continue

            try:

                return _salvar_resposta(
                    valor,
                    caminho,
                )

            except Exception:
                pass


    # objeto de SDK

    atributos = [

        "video",
        "video_bytes",
        "bytes",
        "content",
        "data",
        "output",
        "path",
        "file",

    ]

    for atributo in atributos:

        try:

            valor = getattr(
                resposta,
                atributo,
                None,
            )

        except Exception:

            valor = None

        if valor is None:
            continue

        try:

            return _salvar_resposta(
                valor,
                caminho,
            )

        except Exception:
            pass


    # read()

    if hasattr(
        resposta,
        "read",
    ):

        try:

            dados = resposta.read()

            if dados:

                return _salvar_bytes(
                    dados,
                    caminho,
                )

        except Exception:
            pass


    raise RuntimeError(
        "Não foi possível "
        "extrair um arquivo "
        "de vídeo válido."
    )


# ============================================================
# MOTOR VEO
# ============================================================

def _gerar_veo(
    prompt,
    imagem_bytes=None,
    proporcao="16:9",
    duracao=8,
):

    cliente = (
        criar_cliente_gemini()
    )

    if cliente is None:

        raise RuntimeError(
            "GEMINI_API_KEY "
            "não está configurada."
        )


    if int(duracao) != 8:

        raise RuntimeError(
            "O Veo configurado "
            "neste projeto usa "
            "clipes de 8 segundos."
        )


    aspect_ratio = (
        "9:16"
        if proporcao == "9:16"
        else "16:9"
    )


    configuracao = (
        types.GenerateVideosConfig(
            aspect_ratio=aspect_ratio,
            resolution="720p",
        )
    )


    parametros = {

        "model": MODELO_VEO,

        "prompt": prompt,

        "config": configuracao,

    }


    # Imagem inicial opcional

    if imagem_bytes:

        try:

            from PIL import Image

            imagem = Image.open(
                io.BytesIO(
                    imagem_bytes
                )
            )

            parametros[
                "image"
            ] = imagem

        except Exception as erro:

            raise RuntimeError(
                "Não foi possível "
                "preparar a imagem "
                "de referência: "
                f"{erro}"
            )


    operacao = (
        cliente.models.generate_videos(
            **parametros
        )
    )


    while not operacao.done:

        time.sleep(10)

        operacao = (
            cliente.operations.get(
                operacao
            )
        )


    erro_operacao = getattr(
        operacao,
        "error",
        None,
    )

    if erro_operacao:

        raise RuntimeError(
            str(erro_operacao)
        )


    resposta = getattr(
        operacao,
        "response",
        None,
    )


    videos = (
        getattr(
            resposta,
            "generated_videos",
            None,
        )
        if resposta
        else None
    )


    if not videos:

        raise RuntimeError(
            "O Veo terminou, "
            "mas não retornou "
            "nenhum vídeo."
        )


    video = videos[0]


    caminho = _novo_arquivo(
        "veo"
    )


    # Download pelo cliente Gemini

    cliente.files.download(
        file=video.video
    )


    video.video.save(
        str(caminho)
    )


    if (
        not caminho.exists()
        or caminho.stat().st_size <= 0
    ):

        raise RuntimeError(
            "O Veo não produziu "
            "um arquivo válido."
        )


    return str(
        caminho
    )


# ============================================================
# MOTOR HUGGING FACE
# ============================================================

def _gerar_huggingface(
    prompt,
    duracao=8,
):

    cliente = (
        criar_cliente_huggingface()
    )

    if cliente is None:

        raise RuntimeError(
            "HF_TOKEN "
            "não está configurado."
        )


    modelo = (
        "Lightricks/"
        "LTX-Video-0.9.8-13B-distilled"
    )


    resultado = (
        cliente.text_to_video(
            prompt,
            model=modelo,
        )
    )


    return _salvar_resposta(
        resultado,
        _novo_arquivo(
            "huggingface"
        ),
    )


# ============================================================
# GERADOR PRINCIPAL
# ============================================================

def gerar_video(
    prompt=None,
    imagem_bytes=None,
    nome_imagem="imagem.png",
    duracao=DURACAO_PADRAO,
    width=1536,
    height=1024,
    camera="Sony FX6",
    proporcao="16:9",
    descricao=None,
    nome_arquivo=None,
    **kwargs,
):

    _reativar_motores_expirados()


    texto = (
        prompt
        or descricao
        or ""
    ).strip()


    if not texto:

        raise ValueError(
            "Digite uma descrição "
            "para o vídeo."
        )


    prompt_final = (
        _montar_prompt(
            texto,
            camera,
            proporcao,
        )
    )


    # ========================================================
    # ORDEM DO FALLBACK
    # ========================================================

    motores = [

        (
            "Veo 3.1",

            lambda: _gerar_veo(
                prompt_final,
                imagem_bytes,
                proporcao,
                duracao,
            ),
        ),

        (
            "Hugging Face",

            lambda: _gerar_huggingface(
                prompt_final,
                duracao,
            ),
        ),

    ]


    erros = []


    # ========================================================
    # TENTATIVAS
    # ========================================================

    for nome, funcao in motores:

        if not _motor_disponivel(
            nome
        ):

            restante = (
                _estado_motores()
                [nome]
                ["bloqueado_ate"]
                - time.time()
            )

            if restante > 0:

                print(
                    f"[VIDEO] ⏸️ "
                    f"{nome} bloqueado "
                    f"por aproximadamente "
                    f"{int(restante)} segundos."
                )

            continue


        print(
            f"[VIDEO] 🎬 "
            f"Tentando motor: {nome}"
        )


        try:

            caminho = funcao()


            caminho = Path(
                caminho
            )


            if (
                not caminho.exists()
                or caminho.stat().st_size <= 0
            ):

                raise RuntimeError(
                    "O motor não "
                    "retornou um vídeo "
                    "válido."
                )


            _registrar_sucesso(
                nome
            )


            print(
                f"[VIDEO] ✅ "
                f"Vídeo gerado por "
                f"{nome}"
            )


            return {

                "video":
                    str(caminho),

                "motor":
                    nome,

                "sucesso":
                    True,

                "mensagem":
                    f"Vídeo gerado "
                    f"com {nome}.",

                "erros":
                    erros,

            }


        except Exception as erro:

            texto_erro = str(
                erro
            )


            erros.append(
                f"{nome}: "
                f"{texto_erro}"
            )


            print(
                f"[VIDEO] ❌ "
                f"{nome}: "
                f"{texto_erro}"
            )


            # ================================================
            # QUOTA
            # ================================================

            if _erro_e_quota(
                erro
            ):

                _bloquear_por_quota(
                    nome,
                    erro,
                )


                print(
                    "[VIDEO] 🔄 "
                    "FALLBACK ATIVADO"
                )


            else:

                _registrar_erro(
                    nome,
                    erro,
                )


                print(
                    "[VIDEO] 🔄 "
                    "Tentando próximo motor..."
                )


            continue


    # ========================================================
    # TODOS FALHARAM
    # ========================================================

    if not erros:

        erros.append(
            "Nenhum motor está "
            "disponível no momento."
        )


    raise RuntimeError(
        "❌ NENHUM MOTOR DE VÍDEO "
        "CONSEGUIU GERAR O VÍDEO.\n\n"
        + "\n".join(
            erros
        )
    )


# ============================================================
# STATUS DOS MOTORES
# ============================================================

def status_motores():

    _reativar_motores_expirados()

    agora = time.time()

    resultado = []


    for nome, dados in (
        _estado_motores().items()
    ):

        restante = max(
            0,
            int(
                dados[
                    "bloqueado_ate"
                ]
                - agora
            ),
        )


        resultado.append({

            "motor":
                nome,

            "ativo":
                dados[
                    "ativo"
                ],

            "disponivel":
                _motor_disponivel(
                    nome
                ),

            "quota":
                restante > 0,

            "reativacao_em_segundos":
                restante,

            "erros":
                dados[
                    "erros"
                ],

            "sucessos":
                dados[
                    "sucessos"
                ],

            "ultimo_erro":
                dados[
                    "ultimo_erro"
                ],

        })


    return resultado


# ============================================================
# STATUS GERAL
# ============================================================

def status_video():

    return {

        "modelo_veo":
            MODELO_VEO,

        "duracao_padrao":
            DURACAO_PADRAO,

        "tempo_reativacao_quota":
            TEMPO_REATIVACAO_QUOTA,

        "cameras":
            CAMERAS,

        "proporcoes":
            PROPORCOES,

        "motores":
            status_motores(),

    }


# ============================================================
# GERAR VÁRIOS CLIPES
# ============================================================

def gerar_clipes(
    descricoes,
    camera="Sony FX6",
    proporcao="16:9",
    duracao=8,
):

    resultados = []


    for descricao in descricoes:

        try:

            resultado = (
                gerar_video(
                    prompt=descricao,
                    camera=camera,
                    proporcao=proporcao,
                    duracao=duracao,
                )
            )


            resultados.append(
                resultado
            )


        except Exception as erro:

            resultados.append({

                "video":
                    None,

                "motor":
                    "nenhum",

                "sucesso":
                    False,

                "mensagem":
                    str(erro),

            })


            break


    return resultados
