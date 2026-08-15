"""
============================================================
ALEX IA ULTRA
GERENCIADOR DE VÍDEO
============================================================

Sistema completo de:

- múltiplos motores;
- fallback automático;
- detecção de quota;
- bloqueio temporário;
- reativação automática;
- tratamento de erros;
- confirmação de vídeo real;
- geração de clipes;
- suporte a diferentes câmeras.

============================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional
import time
import threading


# ============================================================
# CONFIGURAÇÕES GERAIS
# ============================================================

PASTA_VIDEOS = Path("videos_gerados")

PASTA_VIDEOS.mkdir(
    parents=True,
    exist_ok=True
)


# Duração padrão dos vídeos
DURACAO_PADRAO = 8


# Tempo que um motor ficará bloqueado
# depois de atingir quota.
#
# 30 minutos = 1800 segundos
TEMPO_REATIVACAO_QUOTA = 1800


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
# ESTRUTURAS
# ============================================================

@dataclass
class ResultadoVideo:

    sucesso: bool

    motor: str

    arquivo: Optional[str] = None

    mensagem: str = ""

    erro: Optional[str] = None


@dataclass
class MotorVideo:

    nome: str

    funcao: Callable[..., Any]

    ativo: bool = True

    bloqueado_ate: float = 0.0

    ultimo_erro: Optional[str] = None

    quantidade_erros: int = 0

    quantidade_sucessos: int = 0

    quota_atingida: bool = False


# ============================================================
# LISTA DE MOTORES
# ============================================================

MOTORES: list[MotorVideo] = []


# ============================================================
# LOCK
# ============================================================

LOCK_MOTORES = threading.Lock()


# ============================================================
# REGISTRAR MOTOR
# ============================================================

def registrar_motor(
    nome: str,
    funcao: Callable[..., Any],
    ativo: bool = True,
) -> None:

    """
    Adiciona um motor ao sistema.

    Exemplo:

        registrar_motor(
            "Veo",
            minha_funcao_veo
        )
    """

    if not nome:

        raise ValueError(
            "O nome do motor não pode estar vazio."
        )


    with LOCK_MOTORES:

        # Verifica se já existe

        for motor in MOTORES:

            if motor.nome.lower() == nome.lower():

                motor.funcao = funcao

                motor.ativo = ativo

                return


        # Cria novo motor

        novo_motor = MotorVideo(

            nome=nome,

            funcao=funcao,

            ativo=ativo,

        )


        MOTORES.append(
            novo_motor
        )


# ============================================================
# REMOVER MOTOR
# ============================================================

def remover_motor(
    nome: str
) -> bool:

    global MOTORES


    with LOCK_MOTORES:

        quantidade_antes = len(
            MOTORES
        )


        MOTORES = [

            motor

            for motor in MOTORES

            if motor.nome.lower()
            != nome.lower()

        ]


        return (
            len(MOTORES)
            < quantidade_antes
        )


# ============================================================
# ATIVAR MOTOR
# ============================================================

def ativar_motor(
    nome: str
) -> bool:

    with LOCK_MOTORES:

        for motor in MOTORES:

            if motor.nome.lower() == nome.lower():

                motor.ativo = True

                motor.bloqueado_ate = 0

                motor.quota_atingida = False

                return True


    return False


# ============================================================
# DESATIVAR MOTOR
# ============================================================

def desativar_motor(
    nome: str
) -> bool:

    with LOCK_MOTORES:

        for motor in MOTORES:

            if motor.nome.lower() == nome.lower():

                motor.ativo = False

                return True


    return False


# ============================================================
# LISTAR MOTORES
# ============================================================

def listar_motores() -> list[str]:

    reativar_motores_expirados()


    with LOCK_MOTORES:

        return [

            motor.nome

            for motor in MOTORES

            if motor.ativo

            and motor.bloqueado_ate
            <= time.time()

        ]


# ============================================================
# DETECTAR QUOTA
# ============================================================

def erro_e_quota(
    erro: Exception | str
) -> bool:

    """
    Detecta erros comuns de quota.

    Exemplos:

    429
    RESOURCE_EXHAUSTED
    quota
    rate limit
    too many requests
    """

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


    for palavra in palavras:

        if palavra in texto:

            return True


    return False


# ============================================================
# BLOQUEAR MOTOR
# ============================================================

def bloquear_por_quota(
    motor: MotorVideo,
    erro: Exception | str,
) -> None:

    agora = time.time()


    motor.quota_atingida = True

    motor.ultimo_erro = str(
        erro
    )

    motor.quantidade_erros += 1


    motor.bloqueado_ate = (
        agora
        + TEMPO_REATIVACAO_QUOTA
    )


    print(
        "[VIDEO] ⚠️ QUOTA ATINGIDA"
    )


    print(
        f"[VIDEO] Motor: {motor.nome}"
    )


    print(
        f"[VIDEO] Bloqueado por "
        f"{TEMPO_REATIVACAO_QUOTA} segundos."
    )


# ============================================================
# REGISTRAR ERRO NORMAL
# ============================================================

def registrar_erro(
    motor: MotorVideo,
    erro: Exception | str,
) -> None:

    motor.ultimo_erro = str(
        erro
    )

    motor.quantidade_erros += 1


# ============================================================
# REGISTRAR SUCESSO
# ============================================================

def registrar_sucesso(
    motor: MotorVideo
) -> None:

    motor.quantidade_sucessos += 1

    motor.ultimo_erro = None

    motor.quota_atingida = False

    motor.bloqueado_ate = 0


# ============================================================
# MOTOR DISPONÍVEL?
# ============================================================

def motor_esta_disponivel(
    motor: MotorVideo
) -> bool:

    if not motor.ativo:

        return False


    agora = time.time()


    # Ainda está bloqueado

    if (
        motor.bloqueado_ate
        > agora
    ):

        return False


    return True


# ============================================================
# REATIVAÇÃO AUTOMÁTICA
# ============================================================

def reativar_motores_expirados() -> None:

    agora = time.time()


    with LOCK_MOTORES:

        for motor in MOTORES:

            if not motor.ativo:

                continue


            if (
                motor.bloqueado_ate > 0
                and motor.bloqueado_ate
                <= agora
            ):

                motor.bloqueado_ate = 0

                motor.quota_atingida = False

                motor.ultimo_erro = None


                print(
                    "[VIDEO] ♻️ Motor "
                    f"{motor.nome} "
                    "reativado automaticamente."
                )


# ============================================================
# TEMPO RESTANTE
# ============================================================

def tempo_bloqueio(
    nome: str
) -> int:

    agora = time.time()


    with LOCK_MOTORES:

        for motor in MOTORES:

            if motor.nome.lower()
            == nome.lower():

                restante = (
                    motor.bloqueado_ate
                    - agora
                )


                if restante <= 0:

                    return 0


                return int(
                    restante
                )


    return 0


# ============================================================
# LIMPAR ESTADO DE UM MOTOR
# ============================================================

def resetar_motor(
    nome: str
) -> bool:

    with LOCK_MOTORES:

        for motor in MOTORES:

            if motor.nome.lower()
            == nome.lower():

                motor.bloqueado_ate = 0

                motor.quota_atingida = False

                motor.ultimo_erro = None

                motor.quantidade_erros = 0

                return True


    return False


# ============================================================
# VALIDAR CÂMERA
# ============================================================

def validar_camera(
    camera: str
) -> str:

    if camera in CAMERAS:

        return camera


    return "Sony FX6"


# ============================================================
# VALIDAR PROPORÇÃO
# ============================================================

def validar_proporcao(
    proporcao: str
) -> str:

    if proporcao in PROPORCOES:

        return proporcao


    return "16:9"


# ============================================================
# VALIDAR DURAÇÃO
# ============================================================

def validar_duracao(
    duracao: Any
) -> int:

    try:

        duracao = int(
            duracao
        )

    except Exception:

        duracao = DURACAO_PADRAO


    if duracao <= 0:

        duracao = DURACAO_PADRAO


    return duracao


# ============================================================
# MONTAR PROMPT
# ============================================================

def montar_prompt(
    descricao: str,
    camera: str = "Sony FX6",
    proporcao: str = "16:9",
    duracao: int = 8,
) -> str:

    descricao = str(
        descricao
    ).strip()


    if not descricao:

        raise ValueError(
            "A descrição do vídeo "
            "não pode estar vazia."
        )


    camera = validar_camera(
        camera
    )


    proporcao = validar_proporcao(
        proporcao
    )


    duracao = validar_duracao(
        duracao
    )


    return f"""
Crie um vídeo cinematográfico
realista e de alta qualidade.

CENA:

{descricao}

CÂMERA:

{camera}

PROPORÇÃO:

{proporcao}

DURAÇÃO:

{duracao} segundos

DIREÇÃO CINEMATOGRÁFICA:

- iluminação realista;
- movimentos naturais;
- câmera estável;
- profundidade cinematográfica;
- física natural;
- continuidade visual;
- personagens consistentes;
- ambiente consistente;
- detalhes realistas;
- sem deformações;
- sem mudanças desnecessárias
  na aparência dos personagens.

A câmera deve permanecer
consistente durante toda a cena.
""".strip()


# ============================================================
# GERAR NOME
# ============================================================

def gerar_nome_arquivo(
    prefixo: str = "video"
) -> str:

    timestamp = int(
        time.time() * 1000
    )


    return (
        f"{prefixo}_"
        f"{timestamp}.mp4"
    )


# ============================================================
# SALVAR BYTES
# ============================================================

def salvar_bytes(
    dados: bytes,
    nome_arquivo: Optional[str] = None,
) -> str:

    if not dados:

        raise RuntimeError(
            "O motor retornou "
            "dados vazios."
        )


    if not nome_arquivo:

        nome_arquivo = gerar_nome_arquivo()


    nome_arquivo = Path(
        nome_arquivo
    ).name


    if not nome_arquivo.lower().endswith(
        ".mp4"
    ):

        nome_arquivo += ".mp4"


    caminho = (
        PASTA_VIDEOS
        / nome_arquivo
    )


    caminho.write_bytes(
        dados
    )


    if not caminho.exists():

        raise RuntimeError(
            "O arquivo não foi criado."
        )


    if caminho.stat().st_size <= 0:

        try:

            caminho.unlink()

        except Exception:

            pass


        raise RuntimeError(
            "O arquivo foi criado "
            "vazio."
        )


    return str(
        caminho
    )


# ============================================================
# COPIAR VÍDEO
# ============================================================

def copiar_video(
    origem: str | Path,
    nome_arquivo: Optional[str] = None,
) -> str:

    origem = Path(
        origem
    )


    if not origem.exists():

        raise FileNotFoundError(
            f"Arquivo não encontrado: "
            f"{origem}"
        )


    if origem.stat().st_size <= 0:

        raise RuntimeError(
            "O vídeo de origem "
            "está vazio."
        )


    if not nome_arquivo:

        nome_arquivo = origem.name


    nome_arquivo = Path(
        nome_arquivo
    ).name


    destino = (
        PASTA_VIDEOS
        / nome_arquivo
    )


    destino.write_bytes(
        origem.read_bytes()
    )


    return str(
        destino
    )


# ============================================================
# EXTRAIR VÍDEO
# ============================================================

def extrair_video(
    resposta: Any,
    nome_arquivo: Optional[str] = None,
) -> str:

    """
    Tenta extrair o vídeo de
    diferentes formatos de resposta.
    """

    if resposta is None:

        raise RuntimeError(
            "Resposta vazia."
        )


    # Bytes

    if isinstance(
        resposta,
        bytes
    ):

        return salvar_bytes(
            resposta,
            nome_arquivo
        )


    if isinstance(
        resposta,
        bytearray
    ):

        return salvar_bytes(
            bytes(resposta),
            nome_arquivo
        )


    # Caminho

    if isinstance(
        resposta,
        (str, Path)
    ):

        caminho = Path(
            resposta
        )


        if caminho.exists():

            return copiar_video(
                caminho,
                nome_arquivo
            )


    # Dicionário

    if isinstance(
        resposta,
        dict
    ):

        chaves = [

            "video",

            "video_bytes",

            "bytes",

            "content",

            "data",

            "file",

            "output",

            "path",

            "filename",

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

                return extrair_video(
                    valor,
                    nome_arquivo
                )

            except Exception:

                continue


    # Objeto de SDK

    atributos = [

        "video",

        "video_bytes",

        "bytes",

        "content",

        "data",

        "file",

        "output",

        "path",

        "filename",

    ]


    for atributo in atributos:

        try:

            valor = getattr(
                resposta,
                atributo,
                None
            )

        except Exception:

            valor = None


        if valor is None:

            continue


        try:

            return extrair_video(
                valor,
                nome_arquivo
            )

        except Exception:

            continue


    # read()

    if hasattr(
        resposta,
        "read"
    ):

        try:

            dados = resposta.read()


            if dados:

                return salvar_bytes(
                    dados,
                    nome_arquivo
                )

        except Exception:

            pass


    raise RuntimeError(
        "O motor respondeu, "
        "mas não entregou um "
        "arquivo de vídeo válido."
    )


# ============================================================
# GERAR VÍDEO
# ============================================================

def gerar_video(
    descricao: str,
    camera: str = "Sony FX6",
    proporcao: str = "16:9",
    duracao: int = DURACAO_PADRAO,
    nome_arquivo: Optional[str] = None,
) -> ResultadoVideo:

    """
    GERADOR PRINCIPAL.

    O sistema:

    1. prepara o prompt;
    2. verifica os motores;
    3. pula motores bloqueados;
    4. tenta o primeiro disponível;
    5. detecta quota;
    6. bloqueia o motor;
    7. ativa fallback;
    8. tenta o próximo;
    9. confirma o arquivo;
    10. retorna sucesso.

    """

    reativar_motores_expirados()


    try:

        prompt = montar_prompt(
            descricao,
            camera,
            proporcao,
            duracao
        )

    except Exception as erro:

        return ResultadoVideo(

            sucesso=False,

            motor="nenhum",

            mensagem=(
                "Não foi possível "
                "preparar o vídeo."
            ),

            erro=str(erro),

        )


    if not nome_arquivo:

        nome_arquivo = (
            gerar_nome_arquivo()
        )


    # Apenas motores disponíveis

    motores_disponiveis = [

        motor

        for motor in MOTORES

        if motor_esta_disponivel(
            motor
        )

    ]


    if not motores_disponiveis:

        bloqueados = []


        for motor in MOTORES:

            if motor.ativo:

                restante = tempo_bloqueio(
                    motor.nome
                )


                if restante > 0:

                    bloqueados.append(
                        f"{motor.nome}: "
                        f"{restante}s"
                    )


        detalhe = (
            ", ".join(
                bloqueados
            )
            if bloqueados
            else "nenhum motor configurado"
        )


        return ResultadoVideo(

            sucesso=False,

            motor="nenhum",

            mensagem=(
                "❌ Nenhum motor de vídeo "
                "está disponível no momento."
            ),

            erro=detalhe,

        )


    erros = []


    # ========================================================
    # FALLBACK
    # ========================================================

    for indice, motor in enumerate(
        motores_disponiveis,
        start=1
    ):

        print(
            ""
        )

        print(
            "================================"
        )

        print(
            f"[VIDEO] MOTOR "
            f"{indice}/"
            f"{len(motores_disponiveis)}"
        )

        print(
            f"[VIDEO] {motor.nome}"
        )

        print(
            "================================"
        )


        try:

            resposta = motor.funcao(

                prompt=prompt,

                duracao=duracao,

                proporcao=proporcao,

                camera=camera,

            )


            arquivo = extrair_video(

                resposta,

                nome_arquivo

            )


            caminho = Path(
                arquivo
            )


            # Confirmação real

            if not caminho.exists():

                raise RuntimeError(
                    "O arquivo retornado "
                    "não existe."
                )


            if caminho.stat().st_size <= 0:

                raise RuntimeError(
                    "O arquivo retornado "
                    "está vazio."
                )


            # Sucesso

            registrar_sucesso(
                motor
            )


            print(
                f"[VIDEO] ✅ "
                f"VÍDEO GERADO POR "
                f"{motor.nome}"
            )


            return ResultadoVideo(

                sucesso=True,

                motor=motor.nome,

                arquivo=str(
                    caminho
                ),

                mensagem=(
                    f"Vídeo gerado "
                    f"com sucesso pelo "
                    f"{motor.nome}."
                ),

            )


        except Exception as erro:

            texto_erro = str(
                erro
            )


            erros.append(
                f"{motor.nome}: "
                f"{texto_erro}"
            )


            # =================================================
            # QUOTA
            # =================================================

            if erro_e_quota(
                erro
            ):

                bloquear_por_quota(
                    motor,
                    erro
                )


                print(
                    "[VIDEO] 🔄 "
                    "FALLBACK ATIVADO"
                )


                continue


            # =================================================
            # ERRO NORMAL
            # =================================================

            registrar_erro(
                motor,
                erro
            )


            print(
                f"[VIDEO] ❌ "
                f"Erro em "
                f"{motor.nome}: "
                f"{texto_erro}"
            )


            print(
                "[VIDEO] 🔄 "
                "Tentando próximo motor..."
            )


            continue


    # ========================================================
    # TODOS OS MOTORES FALHARAM
    # ========================================================

    print(
        ""
    )

    print(
        "================================"
    )

    print(
        "❌ NENHUM MOTOR CONSEGUIU GERAR"
    )

    print(
        "================================"
    )


    return ResultadoVideo(

        sucesso=False,

        motor="nenhum",

        mensagem=(
            "❌ NENHUM MOTOR DE VÍDEO "
            "CONSEGUIU GERAR O VÍDEO."
        ),

        erro="\n".join(
            erros
        ),

    )


# ============================================================
# GERAR VÁRIOS CLIPES
# ============================================================

def gerar_clipes(
    descricoes: list[str],
    camera: str = "Sony FX6",
    proporcao: str = "16:9",
    duracao: int = 8,
) -> list[ResultadoVideo]:

    """
    Permite criar um vídeo longo
    dividindo-o em vários clipes.

    Exemplo:

    8 segundos
    +
    8 segundos
    +
    8 segundos
    =
    24 segundos
    """

    resultados = []


    for indice, descricao in enumerate(
        descricoes,
        start=1
    ):

        print(
            f"[VIDEO] Criando "
            f"clipe {indice}/"
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

            nome_arquivo=nome,

        )


        resultados.append(
            resultado
        )


        # Se falhou completamente,
        # não continua fingindo que
        # os próximos existem.

        if not resultado.sucesso:

            print(
                "[VIDEO] ❌ "
                "Falha no clipe."
            )

            break


    return resultados


# ============================================================
# STATUS DOS MOTORES
# ============================================================

def status_motores() -> list[dict]:

    reativar_motores_expirados()


    resultado = []


    with LOCK_MOTORES:

        for motor in MOTORES:

            restante = max(
                0,
                int(
                    motor.bloqueado_ate
                    - time.time()
                )
            )


            resultado.append({

                "nome":
                    motor.nome,

                "ativo":
                    motor.ativo,

                "disponivel":
                    motor_esta_disponivel(
                        motor
                    ),

                "quota":
                    motor.quota_atingida,

                "bloqueado_por_segundos":
                    restante,

                "erros":
                    motor.quantidade_erros,

                "sucessos":
                    motor.quantidade_sucessos,

                "ultimo_erro":
                    motor.ultimo_erro,

            })


    return resultado


# ============================================================
# STATUS GERAL
# ============================================================

def status_video() -> dict:

    return {

        "pasta_videos":
            str(
                PASTA_VIDEOS
            ),

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
# MOTOR NÃO CONFIGURADO
# ============================================================

def motor_nao_configurado(
    **kwargs
):

    raise RuntimeError(

        "Este motor ainda não "
        "foi conectado a uma "
        "API real."

    )


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":

    print(
        "======================================"
    )

    print(
        "     ALEX IA ULTRA - VÍDEO"
    )

    print(
        "======================================"
    )

    print()

    print(
        "Status:"
    )

    print(
        status_video()
    )

    print()

    print(
        "Sistema de fallback:"
        " ATIVADO"
    )

    print(
        "Sistema de quota:"
        " ATIVADO"
    )

    print(
        "Reativação automática:"
        " ATIVADA"
    )

    print()

    print(
        "Nenhum motor real foi "
        "conectado automaticamente."
)
