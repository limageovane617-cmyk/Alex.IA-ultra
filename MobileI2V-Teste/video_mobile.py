# ============================================================
# Alex IA Ultra
# video_mobile.py
#
# Motor local: MobileI2V
#
# Objetivo:
#   - Receber imagem + descrição do movimento
#   - Preparar o arquivo asset/test.txt
#   - Executar o MobileI2V oficial
#   - Encontrar o MP4 gerado
#   - Copiar o resultado para a pasta de vídeos do Alex IA
#
# NÃO usa:
#   - Replicate
#   - Magic Hour
#   - ZeroGPU
#   - API de geração de vídeo
#
# O modelo é executado pelo código oficial do MobileI2V.
# ============================================================

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional


# ============================================================
# CONFIGURAÇÃO
# ============================================================

NOME_MOTOR = "MobileI2V — Local"

RAIZ = Path(__file__).resolve().parent

# Se video_mobile.py estiver dentro de uma pasta do projeto
# MobileI2V, estas pastas continuam funcionando.
MOBILE_ROOT = RAIZ

SCRIPT_MOBILE = MOBILE_ROOT / "scripts" / "inference_i2v.py"

CONFIG_MOBILE = (
    MOBILE_ROOT
    / "configs"
    / "mobilei2v_config"
    / "MobileI2V_300M_img512.yaml"
)

ASSET_DIR = MOBILE_ROOT / "asset"

TEST_TXT = ASSET_DIR / "test.txt"

MODEL_DIR = MOBILE_ROOT / "model"

MODEL_PATH = MODEL_DIR / "hybrid_371.pth"

OUTPUT_DIR = MOBILE_ROOT / "output" / "alex_ia"

# Diretório onde o vídeo final será colocado.
VIDEO_DIR = RAIZ / "videos_gerados"

# Arquivos de imagem aceitos.
EXTENSOES_IMAGEM = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
}

# Arquivos de vídeo aceitos como referência.
EXTENSOES_VIDEO = {
    ".mp4",
    ".mov",
    ".avi",
    ".webm",
}

# Valor usado pelo projeto oficial.
FLOW_SCORE_PADRAO = 2.0

# Segurança contra execução de arquivos muito antigos.
MAX_IDADE_RESULTADO_SEGUNDOS = 60 * 60


# ============================================================
# UTILIDADES
# ============================================================

def _agora() -> float:
    return time.time()


def _normalizar_texto(texto: Any) -> str:
    if texto is None:
        return ""

    texto = str(texto)

    # Remove caracteres que podem quebrar o arquivo.
    texto = texto.replace("\x00", " ")
    texto = texto.replace("\r", " ")
    texto = texto.replace("\n", " ")

    return " ".join(texto.split()).strip()


def _garantir_pastas() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def _caminho_absoluto(caminho: str | Path) -> Path:
    p = Path(caminho)

    if p.is_absolute():
        return p

    return (Path.cwd() / p).resolve()


def _arquivo_valido(caminho: str | Path) -> bool:
    try:
        p = _caminho_absoluto(caminho)
        return p.exists() and p.is_file()
    except Exception:
        return False


def _arquivo_e_imagem(caminho: str | Path) -> bool:
    return Path(caminho).suffix.lower() in EXTENSOES_IMAGEM


def _arquivo_e_video(caminho: str | Path) -> bool:
    return Path(caminho).suffix.lower() in EXTENSOES_VIDEO


# ============================================================
# VERIFICAÇÃO DO MOTOR
# ============================================================

def verificar_instalacao() -> dict[str, Any]:
    """
    Verifica se o projeto MobileI2V está completo o suficiente
    para tentar uma execução.
    """

    _garantir_pastas()

    problemas: list[str] = []

    if not SCRIPT_MOBILE.exists():
        problemas.append(
            f"Arquivo ausente: {SCRIPT_MOBILE}"
        )

    if not CONFIG_MOBILE.exists():
        problemas.append(
            f"Configuração ausente: {CONFIG_MOBILE}"
        )

    if not MODEL_PATH.exists():
        problemas.append(
            f"Modelo ausente: {MODEL_PATH}"
        )

    # Verificação opcional de módulos Python.
    modulos = {}

    for nome in (
        "torch",
        "torchvision",
        "PIL",
        "pyrallis",
    ):
        try:
            __import__(nome)
            modulos[nome] = True
        except Exception:
            modulos[nome] = False

    return {
        "ok": len(problemas) == 0,
        "problemas": problemas,
        "modulos": modulos,
        "script": str(SCRIPT_MOBILE),
        "config": str(CONFIG_MOBILE),
        "modelo": str(MODEL_PATH),
    }


# ============================================================
# PREPARAR IMAGEM
# ============================================================

def preparar_imagem(
    imagem: str | Path,
) -> Path:
    """
    Copia a imagem para asset/ mantendo o arquivo original.
    """

    origem = _caminho_absoluto(imagem)

    if not origem.exists():
        raise FileNotFoundError(
            f"Imagem não encontrada: {origem}"
        )

    if not origem.is_file():
        raise ValueError(
            f"O caminho informado não é um arquivo: {origem}"
        )

    if not _arquivo_e_imagem(origem):
        raise ValueError(
            "Formato de imagem não suportado. "
            f"Use: {', '.join(sorted(EXTENSOES_IMAGEM))}"
        )

    _garantir_pastas()

    destino = ASSET_DIR / f"alex_input{origem.suffix.lower()}"

    shutil.copy2(origem, destino)

    return destino


# ============================================================
# PREPARAR REFERÊNCIA DE VÍDEO
# ============================================================

def preparar_referencia(
    arquivo: str | Path,
) -> Path:
    """
    Copia imagem ou vídeo para asset/.

    O MobileI2V oficial aceita referência de imagem ou vídeo
    no fluxo de inferência.
    """

    origem = _caminho_absoluto(arquivo)

    if not origem.exists():
        raise FileNotFoundError(
            f"Arquivo de referência não encontrado: {origem}"
        )

    if not origem.is_file():
        raise ValueError(
            f"O caminho informado não é um arquivo: {origem}"
        )

    extensao = origem.suffix.lower()

    if (
        extensao not in EXTENSOES_IMAGEM
        and extensao not in EXTENSOES_VIDEO
    ):
        raise ValueError(
            "Formato de referência não suportado."
        )

    _garantir_pastas()

    destino = ASSET_DIR / f"alex_reference{extensao}"

    shutil.copy2(origem, destino)

    return destino


# ============================================================
# PROMPT
# ============================================================

def montar_prompt(
    descricao: str,
    camera: str = "Sony FX6",
    proporcao: str = "16:9",
) -> str:
    """
    Converte a descrição simples do usuário em um prompt
    mais apropriado para I2V.

    Exemplo:
        "O menino vira para a direita"
    """

    descricao = _normalizar_texto(descricao)

    if not descricao:
        descricao = (
            "movimento natural e suave, "
            "mantendo a aparência original da pessoa"
        )

    camera = _normalizar_texto(camera) or "Sony FX6"
    proporcao = _normalizar_texto(proporcao) or "16:9"

    prompt = (
        f"{descricao}. "
        "Manter exatamente a identidade, rosto, cabelo, "
        "roupa e aparência do personagem da imagem de referência. "
        "Não trocar a pessoa, não alterar a roupa e não criar "
        "outro personagem. "
        "Movimento natural e consistente, sem deformações. "
        f"Estética cinematográfica capturada com {camera}, "
        f"enquadramento {proporcao}."
    )

    return _normalizar_texto(prompt)


# ============================================================
# ESCREVER asset/test.txt
# ============================================================

def criar_test_txt(
    referencia: str | Path,
) -> Path:
    """
    O MobileI2V oficial espera que asset/test.txt contenha
    o caminho da imagem/vídeo de referência.
    """

    _garantir_pastas()

    referencia_path = _caminho_absoluto(referencia)

    # O projeto oficial trabalha com caminhos relativos.
    try:
        relativo = referencia_path.relative_to(MOBILE_ROOT)
        texto = "./" + relativo.as_posix()
    except ValueError:
        texto = str(referencia_path)

    TEST_TXT.write_text(
        texto + "\n",
        encoding="utf-8",
    )

    return TEST_TXT


# ============================================================
# EXECUTAR MOBILEI2V
# ============================================================

def executar_mobile_i2v(
    prompt: str,
    flow_score: float = FLOW_SCORE_PADRAO,
    timeout: int = 60 * 30,
    gpu_id: Optional[int] = 0,
) -> dict[str, Any]:
    """
    Executa o script oficial:

    scripts/inference_i2v.py

    """

    verificacao = verificar_instalacao()

    if not verificacao["ok"]:
        return {
            "sucesso": False,
            "motor": NOME_MOTOR,
            "video": None,
            "erro": (
                "MobileI2V não está pronto para execução."
            ),
            "detalhes": verificacao,
        }

    prompt = _normalizar_texto(prompt)

    if not prompt:
        prompt = (
            "Natural movement while preserving the identity "
            "and appearance of the reference image."
        )

    _garantir_pastas()

    # Cada execução recebe uma pasta própria.
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    execucao_dir = OUTPUT_DIR / timestamp
    execucao_dir.mkdir(parents=True, exist_ok=True)

    # O projeto oficial aceita flow_score.
    try:
        flow_score = float(flow_score)
    except Exception:
        flow_score = FLOW_SCORE_PADRAO

    comando = [
        sys.executable,
        str(SCRIPT_MOBILE),
        "--config",
        str(CONFIG_MOBILE),
        "--save_path",
        str(execucao_dir),
        "--model_path",
        str(MODEL_PATH),
        "--txt_file",
        str(TEST_TXT),
        "--flow_score",
        str(flow_score),
        "--prompt",
        prompt,
    ]

    ambiente = os.environ.copy()

    if gpu_id is not None:
        ambiente["CUDA_VISIBLE_DEVICES"] = str(gpu_id)

    inicio = _agora()

    try:
        processo = subprocess.run(
            comando,
            cwd=str(MOBILE_ROOT),
            env=ambiente,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )

    except subprocess.TimeoutExpired as exc:
        return {
            "sucesso": False,
            "motor": NOME_MOTOR,
            "video": None,
            "erro": (
                "O MobileI2V demorou mais do que o tempo limite "
                "permitido."
            ),
            "timeout": timeout,
            "saida_parcial": (
                exc.stdout.decode(errors="replace")
                if isinstance(exc.stdout, bytes)
                else (exc.stdout or "")
            ),
        }

    except Exception as exc:
        return {
            "sucesso": False,
            "motor": NOME_MOTOR,
            "video": None,
            "erro": f"Falha ao iniciar MobileI2V: {exc}",
        }

    duracao = round(_agora() - inicio, 2)

    saida = processo.stdout or ""

    # ========================================================
    # PROCURAR MP4
    # ========================================================

    videos = []

    for pasta in (
        execucao_dir,
        OUTPUT_DIR,
        MOBILE_ROOT / "test_video",
    ):
        if not pasta.exists():
            continue

        try:
            for arquivo in pasta.rglob("*.mp4"):
                try:
                    idade = _agora() - arquivo.stat().st_mtime
                except Exception:
                    idade = 0

                # Evita pegar vídeos muito antigos.
                if idade <= MAX_IDADE_RESULTADO_SEGUNDOS:
                    videos.append(arquivo)

        except Exception:
            continue

    # Remover duplicados.
    videos_unicos = []

    vistos = set()

    for video in videos:
        chave = str(video.resolve())

        if chave not in vistos:
            vistos.add(chave)
            videos_unicos.append(video)

    videos = sorted(
        videos_unicos,
        key=lambda p: p.stat().st_mtime
        if p.exists()
        else 0,
        reverse=True,
    )

    if processo.returncode != 0 and not videos:
        return {
            "sucesso": False,
            "motor": NOME_MOTOR,
            "video": None,
            "erro": (
                "O MobileI2V encerrou com erro."
            ),
            "codigo_saida": processo.returncode,
            "tempo_segundos": duracao,
            "saida": saida[-12000:],
            "comando": comando,
        }

    if not videos:
        return {
            "sucesso": False,
            "motor": NOME_MOTOR,
            "video": None,
            "erro": (
                "O MobileI2V terminou, mas nenhum arquivo MP4 "
                "foi encontrado."
            ),
            "codigo_saida": processo.returncode,
            "tempo_segundos": duracao,
            "saida": saida[-12000:],
        }

    video_origem = videos[0]

    # ========================================================
    # COPIAR PARA A PASTA FINAL
    # ========================================================

    nome_final = (
        f"mobilei2v_{time.strftime('%Y%m%d_%H%M%S')}.mp4"
    )

    video_final = VIDEO_DIR / nome_final

    shutil.copy2(
        video_origem,
        video_final,
    )

    return {
        "sucesso": True,
        "motor": NOME_MOTOR,
        "video": str(video_final),
        "video_origem": str(video_origem),
        "codigo_saida": processo.returncode,
        "tempo_segundos": duracao,
        "saida": saida[-12000:],
    }


# ============================================================
# FUNÇÃO PRINCIPAL PARA O ALEX IA ULTRA
# ============================================================

def gerar_video(
    imagem: str | Path,
    descricao: str,
    camera: str = "Sony FX6",
    proporcao: str = "16:9",
    duracao: float = 5.0,
    flow_score: float = FLOW_SCORE_PADRAO,
    timeout: int = 60 * 30,
) -> dict[str, Any]:
    """
    Função principal.

    Uso:

        resultado = gerar_video(
            imagem="foto.jpg",
            descricao="O menino vira lentamente para a direita.",
        )

    Retorna:

        {
            "sucesso": True/False,
            "video": "...mp4",
            "motor": "MobileI2V — Local",
            ...
        }
    """

    del duracao  # MobileI2V oficial trabalha com quantidade fixa de frames.

    try:
        _garantir_pastas()

        # ----------------------------------------------------
        # Verificar arquivo
        # ----------------------------------------------------

        imagem_path = _caminho_absoluto(imagem)

        if not imagem_path.exists():
            return {
                "sucesso": False,
                "motor": NOME_MOTOR,
                "video": None,
                "erro": (
                    f"Imagem não encontrada: {imagem_path}"
                ),
            }

        # ----------------------------------------------------
        # Preparar imagem
        # ----------------------------------------------------

        referencia = preparar_imagem(imagem_path)

        # ----------------------------------------------------
        # Criar asset/test.txt
        # ----------------------------------------------------

        criar_test_txt(referencia)

        # ----------------------------------------------------
        # Criar prompt
        # ----------------------------------------------------

        prompt = montar_prompt(
            descricao=descricao,
            camera=camera,
            proporcao=proporcao,
        )

        # ----------------------------------------------------
        # Executar
        # ----------------------------------------------------

        resultado = executar_mobile_i2v(
            prompt=prompt,
            flow_score=flow_score,
            timeout=timeout,
        )

        resultado["prompt"] = prompt
        resultado["referencia"] = str(referencia)
        resultado["duracao_solicitada"] = duracao

        return resultado

    except Exception as exc:
        return {
            "sucesso": False,
            "motor": NOME_MOTOR,
            "video": None,
            "erro": f"Erro inesperado no MobileI2V: {exc}",
        }


# ============================================================
# ALIAS PARA COMPATIBILIDADE COM GERENCIADORES ANTIGOS
# ============================================================

def gerar(
    imagem: str | Path,
    descricao: str,
    camera: str = "Sony FX6",
    proporcao: str = "16:9",
    duracao: float = 5.0,
    **kwargs,
) -> dict[str, Any]:

    return gerar_video(
        imagem=imagem,
        descricao=descricao,
        camera=camera,
        proporcao=proporcao,
        duracao=duracao,
        **kwargs,
    )


def criar_video(
    imagem: str | Path,
    descricao: str,
    **kwargs,
) -> dict[str, Any]:

    return gerar_video(
        imagem=imagem,
        descricao=descricao,
        **kwargs,
    )


# ============================================================
# TESTE DIRETO
# ============================================================

def _teste_terminal() -> None:

    print("=" * 60)
    print("🎬 ALEX IA ULTRA — MOBILEI2V")
    print("=" * 60)

    estado = verificar_instalacao()

    print()
    print("📦 Verificação do projeto:")
    print(json.dumps(
        estado,
        indent=2,
        ensure_ascii=False,
    ))

    if not estado["ok"]:
        print()
        print("❌ MobileI2V ainda não está completo.")
        print()
        for problema in estado["problemas"]:
            print("•", problema)

        return

    print()
    print("✅ Estrutura encontrada.")
    print()
    print("Para gerar um vídeo pelo terminal:")
    print()
    print(
        "python video_mobile.py "
        "\"imagem.jpg\" "
        "\"O personagem vira lentamente para a direita.\""
    )


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":

    # Permite teste:
    #
    # python video_mobile.py imagem.jpg "movimento"
    #

    if len(sys.argv) >= 3:

        imagem = sys.argv[1]
        descricao = " ".join(sys.argv[2:])

        print()
        print("🎬 Gerando vídeo com MobileI2V...")
        print()

        resultado = gerar_video(
            imagem=imagem,
            descricao=descricao,
        )

        print()
        print(
            json.dumps(
                resultado,
                indent=2,
                ensure_ascii=False,
            )
        )

    else:
        _teste_terminal()
