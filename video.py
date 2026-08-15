"""
video.py
Gerenciador de geração de vídeos do Alex IA Ultra.

Objetivos:
- Trabalhar com vídeos de 8 segundos por padrão.
- Suportar diferentes câmeras cinematográficas.
- Permitir vários motores de vídeo.
- Usar fallback automático entre motores.
- NÃO considerar uma tentativa como sucesso se nenhum
  arquivo de vídeo real tiver sido recebido.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional
import time


# ============================================================
# CONFIGURAÇÕES
# ============================================================

PASTA_VIDEOS = Path("videos_gerados")
PASTA_VIDEOS.mkdir(parents=True, exist_ok=True)

DURACAO_PADRAO = 8

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


# ============================================================
# MOTORES
# ============================================================

MOTORES: list[MotorVideo] = []


def registrar_motor(
    nome: str,
    funcao: Callable[..., Any],
    ativo: bool = True,
) -> None:
    """
    Registra um motor de geração de vídeo.
    """

    # Evita registrar o mesmo motor duas vezes.

    for motor in MOTORES:

        if motor.nome.lower() == nome.lower():

            motor.funcao = funcao
            motor.ativo = ativo

            return

    MOTORES.append(
        MotorVideo(
            nome=nome,
            funcao=funcao,
            ativo=ativo,
        )
    )


def remover_motor(nome: str) -> bool:

    global MOTORES

    quantidade_antes = len(MOTORES)

    MOTORES = [
        motor
        for motor in MOTORES
        if motor.nome.lower() != nome.lower()
    ]

    return len(MOTORES) < quantidade_antes


def listar_motores() -> list[str]:

    return [
        motor.nome
        for motor in MOTORES
        if motor.ativo
    ]


# ============================================================
# UTILITÁRIOS
# ============================================================

def limpar_texto(valor: Any) -> str:

    if valor is None:
        return ""

    return str(valor).strip()


def validar_camera(camera: str) -> str:

    camera = limpar_texto(camera)

    if camera in CAMERAS:
        return camera

    return "Sony FX6"


def validar_proporcao(proporcao: str) -> str:

    proporcao = limpar_texto(proporcao)

    if proporcao in PROPORCOES:
        return proporcao

    return "16:9"


def validar_duracao(duracao: Any) -> int:

    try:

        duracao = int(duracao)

    except Exception:

        duracao = DURACAO_PADRAO

    if duracao <= 0:
        duracao = DURACAO_PADRAO

    return duracao


# ============================================================
# PROMPT
# ============================================================

def montar_prompt(
    descricao: str,
    camera: str = "Sony FX6",
    proporcao: str = "16:9",
    duracao: int = 8,
) -> str:

    descricao = limpar_texto(descricao)

    if not descricao:

        raise ValueError(
            "A descrição do vídeo não pode estar vazia."
        )

    camera = validar_camera(camera)

    proporcao = validar_proporcao(proporcao)

    duracao = validar_duracao(duracao)

    prompt = f"""
Crie um vídeo cinematográfico e realista.

CENA:
{descricao}

CÂMERA:
{camera}

PROPORÇÃO:
{proporcao}

DURAÇÃO:
{duracao} segundos

DIREÇÃO:
- aparência cinematográfica;
- iluminação realista;
- movimentos naturais;
- câmera estável;
- continuidade visual;
- detalhes realistas;
- personagens consistentes;
- ambiente coerente;
- física natural;
- sem texto aleatório na imagem;
- sem deformações;
- sem mudanças desnecessárias de identidade.

A câmera deve permanecer consistente durante toda a cena.
"""

    return prompt.strip()


# ============================================================
# ARQUIVOS
# ============================================================

def gerar_nome_arquivo(prefixo: str = "video") -> str:

    timestamp = int(time.time() * 1000)

    return f"{prefixo}_{timestamp}.mp4"


def salvar_bytes(
    dados: bytes,
    nome_arquivo: Optional[str] = None,
) -> str:

    if not dados:

        raise RuntimeError(
            "O motor retornou dados vazios."
        )

    if not nome_arquivo:

        nome_arquivo = gerar_nome_arquivo()

    nome_arquivo = Path(nome_arquivo).name

    if not nome_arquivo.lower().endswith(".mp4"):

        nome_arquivo += ".mp4"

    caminho = PASTA_VIDEOS / nome_arquivo

    caminho.write_bytes(dados)

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
            "O arquivo de vídeo foi criado vazio."
        )

    return str(caminho)


def copiar_video(
    origem: str | Path,
    nome_arquivo: Optional[str] = None,
) -> str:

    origem = Path(origem)

    if not origem.exists():

        raise FileNotFoundError(
            f"Arquivo não encontrado: {origem}"
        )

    if not origem.is_file():

        raise RuntimeError(
            "O caminho informado não é um arquivo."
        )

    if origem.stat().st_size <= 0:

        raise RuntimeError(
            "O arquivo de origem está vazio."
        )

    if not nome_arquivo:

        nome_arquivo = origem.name

    destino = PASTA_VIDEOS / Path(nome_arquivo).name

    destino.write_bytes(
        origem.read_bytes()
    )

    return str(destino)


# ============================================================
# EXTRAÇÃO DA RESPOSTA DOS MOTORES
# ============================================================

def extrair_video(
    resposta: Any,
    nome_arquivo: Optional[str] = None,
) -> str:

    """
    Tenta localizar o vídeo retornado por diferentes SDKs.

    IMPORTANTE:
    Se não existir um vídeo verdadeiro, esta função gera erro.
    """

    if resposta is None:

        raise RuntimeError(
            "O motor retornou uma resposta vazia."
        )

    # --------------------------------------------------------
    # BYTES
    # --------------------------------------------------------

    if isinstance(resposta, bytes):

        return salvar_bytes(
            resposta,
            nome_arquivo,
        )

    if isinstance(resposta, bytearray):

        return salvar_bytes(
            bytes(resposta),
            nome_arquivo,
        )

    # --------------------------------------------------------
    # CAMINHO
    # --------------------------------------------------------

    if isinstance(
        resposta,
        (str, Path),
    ):

        caminho = Path(resposta)

        if caminho.exists():

            return copiar_video(
                caminho,
                nome_arquivo,
            )

    # --------------------------------------------------------
    # DICIONÁRIO
    # --------------------------------------------------------

    if isinstance(resposta, dict):

        possiveis_chaves = [
            "video",
            "video_bytes",
            "bytes",
            "content",
            "data",
            "file",
            "output",
            "path",
            "filename",
            "uri",
        ]

        for chave in possiveis_chaves:

            if chave not in resposta:
                continue

            valor = resposta[chave]

            if valor is None:
                continue

            try:

                return extrair_video(
                    valor,
                    nome_arquivo,
                )

            except Exception:

                continue

    # --------------------------------------------------------
    # OBJETOS DE SDK
    # --------------------------------------------------------

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
                None,
            )

        except Exception:

            valor = None

        if valor is None:
            continue

        try:

            return extrair_video(
                valor,
                nome_arquivo,
            )

        except Exception:

            continue

    # --------------------------------------------------------
    # MÉTODO READ
    # --------------------------------------------------------

    if hasattr(resposta, "read"):

        try:

            dados = resposta.read()

            if dados:

                return salvar_bytes(
                    dados,
                    nome_arquivo,
                )

        except Exception:
            pass

    # --------------------------------------------------------
    # FALHA
    # --------------------------------------------------------

    raise RuntimeError(
        "O motor respondeu, mas não entregou um arquivo "
        "de vídeo válido."
    )


# ============================================================
# GERADOR PRINCIPAL
# ============================================================

def gerar_video(
    descricao: str,
    camera: str = "Sony FX6",
    proporcao: str = "16:9",
    duracao: int = DURACAO_PADRAO,
    nome_arquivo: Optional[str] = None,
) -> ResultadoVideo:

    """
    Tenta gerar o vídeo usando todos os motores ativos.

    Se um motor falhar:

        Motor 1 -> falhou
        Motor 2 -> tenta
        Motor 3 -> tenta

    Só retorna sucesso quando um arquivo real é encontrado.
    """

    try:

        prompt = montar_prompt(
            descricao=descricao,
            camera=camera,
            proporcao=proporcao,
            duracao=duracao,
        )

    except Exception as erro:

        return ResultadoVideo(
            sucesso=False,
            motor="nenhum",
            mensagem="Não foi possível preparar o vídeo.",
            erro=str(erro),
        )

    motores_ativos = [
        motor
        for motor in MOTORES
        if motor.ativo
    ]

    if not motores_ativos:

        return ResultadoVideo(
            sucesso=False,
            motor="nenhum",
            mensagem=(
                "NENHUM MOTOR DE VÍDEO ESTÁ CONFIGURADO."
            ),
            erro=(
                "Adicione os motores usando "
                "registrar_motor()."
            ),
        )

    if not nome_arquivo:

        nome_arquivo = gerar_nome_arquivo()

    erros = []

    # ========================================================
    # FALLBACK
    # ========================================================

    for numero, motor in enumerate(
        motores_ativos,
        start=1,
    ):

        try:

            print(
                f"[VÍDEO] Tentando motor "
                f"{numero}/{len(motores_ativos)}: "
                f"{motor.nome}"
            )

            resposta = motor.funcao(
                prompt=prompt,
                duracao=duracao,
                proporcao=proporcao,
                camera=camera,
            )

            arquivo = extrair_video(
                resposta,
                nome_arquivo,
            )

            caminho = Path(arquivo)

            if not caminho.exists():

                raise RuntimeError(
                    "O arquivo retornado não existe."
                )

            if caminho.stat().st_size <= 0:

                raise RuntimeError(
                    "O arquivo retornado está vazio."
                )

            return ResultadoVideo(
                sucesso=True,
                motor=motor.nome,
                arquivo=str(caminho),
                mensagem=(
                    f"Vídeo gerado com sucesso "
                    f"pelo motor {motor.nome}."
                ),
            )

        except Exception as erro:

            mensagem_erro = (
                f"{motor.nome}: "
                f"{type(erro).__name__}: "
                f"{erro}"
            )

            print(
                f"[VÍDEO] FALHA: "
                f"{mensagem_erro}"
            )

            erros.append(
                mensagem_erro
            )

            continue

    # ========================================================
    # TODOS FALHARAM
    # ========================================================

    return ResultadoVideo(
        sucesso=False,
        motor="nenhum",
        mensagem=(
            "❌ NENHUM MOTOR DE VÍDEO "
            "CONSEGUIU GERAR O VÍDEO."
        ),
        erro="\n".join(erros),
    )


# ============================================================
# GERAÇÃO DE VÁRIOS CLIPES
# ============================================================

def gerar_clipes(
    descricoes: list[str],
    camera: str = "Sony FX6",
    proporcao: str = "16:9",
    duracao: int = 8,
) -> list[ResultadoVideo]:

    """
    Gera vários clipes.

    Isso permite montar vídeos maiores usando vários
    segmentos de 8 segundos.
    """

    resultados = []

    for indice, descricao in enumerate(
        descricoes,
        start=1,
    ):

        nome = (
            f"clipe_{indice:03d}.mp4"
        )

        resultado = gerar_video(
            descricao=descricao,
            camera=camera,
            proporcao=proporcao,
            duracao=duracao,
            nome_arquivo=nome,
        )

        resultados.append(resultado)

    return resultados


# ============================================================
# STATUS
# ============================================================

def status_video() -> dict:

    return {
        "pasta": str(
            PASTA_VIDEOS
        ),
        "duracao_padrao": DURACAO_PADRAO,
        "cameras": CAMERAS,
        "proporcoes": PROPORCOES,
        "motores": listar_motores(),
    }


# ============================================================
# MOTOR PLACEHOLDER
# ============================================================

def motor_nao_configurado(
    **kwargs,
):

    raise RuntimeError(
        "Este motor ainda não foi conectado a uma API real."
    )


# ============================================================
# TESTE
# ============================================================

if __name__ == "__main__":

    print(
        "======================================"
    )

    print(
        "Alex IA Ultra - Sistema de Vídeo"
    )

    print(
        "======================================"
    )

    print(
        status_video()
    )

    print()

    print(
        "Nenhum motor de vídeo real foi "
        "ativado automaticamente."
    )
