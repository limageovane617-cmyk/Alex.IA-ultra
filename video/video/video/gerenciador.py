# ============================================================
# 🎬 ALEX IA ULTRA — GERENCIADOR DE MOTORES DE VÍDEO
# Criada por Geovani
# ============================================================

from .configuracao import (
    MOTORES_VIDEO,
    MOTOR_PADRAO,
)


def listar_motores():
    """Retorna todos os motores disponíveis na configuração."""
    return MOTORES_VIDEO.copy()


def obter_motor_padrao():
    """Retorna o motor definido como padrão."""
    return MOTOR_PADRAO


def motor_existe(nome_motor):
    """Verifica se um motor está cadastrado."""
    return nome_motor in MOTORES_VIDEO


def escolher_motor(nome_motor=None):
    """
    Escolhe um motor de vídeo.

    Se nenhum motor for informado,
    utiliza o motor automático.
    """

    if not nome_motor:
        return MOTOR_PADRAO

    if motor_existe(nome_motor):
        return nome_motor

    return MOTOR_PADRAO


def status_motores():
    """Retorna o estado básico dos motores cadastrados."""

    resultado = {}

    for motor in MOTORES_VIDEO:
        resultado[motor] = {
            "nome": motor,
            "disponivel": motor == "Automático",
        }

    return resultado
