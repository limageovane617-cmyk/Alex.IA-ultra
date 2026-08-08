# ============================================================
# 🎬 ALEX IA ULTRA — GERENCIADOR DE VÍDEO
# Criada por Geovani
# ============================================================

from .configuracao import (
    MOTORES_VIDEO,
    CAMERAS,
    PROPORCOES,
    DURACAO_PADRAO,
)


def listar_motores():
    """Retorna todos os motores de vídeo disponíveis."""
    return MOTORES_VIDEO


def escolher_motor(preferido=None):
    """
    Escolhe um motor de vídeo.

    Por enquanto o primeiro motor disponível é usado.
    Depois vamos adicionar o sistema automático de fallback,
    para a Ultra tentar outro motor quando um deles atingir
    limite ou estiver indisponível.
    """

    if preferido and preferido in MOTORES_VIDEO:
        return preferido

    if MOTORES_VIDEO:
        return MOTORES_VIDEO[0]

    return None


def validar_configuracao(
    camera,
    proporcao,
    duracao,
):
    """Valida as configurações recebidas pelo gerador."""

    if camera not in CAMERAS:
        camera = CAMERAS[-1]

    if proporcao not in PROPORCOES:
        proporcao = PROPORCOES[0]

    try:
        duracao = int(duracao)
    except (TypeError, ValueError):
        duracao = DURACAO_PADRAO

    if duracao <= 0:
        duracao = DURACAO_PADRAO

    return camera, proporcao, duracao


def preparar_video(
    descricao,
    camera=None,
    proporcao=None,
    duracao=None,
    motor=None,
):
    """
    Prepara uma solicitação de vídeo.

    Esta função ainda não gera o vídeo.
    Ela organiza todas as informações para que os
    motores possam ser conectados posteriormente.
    """

    if not descricao or not descricao.strip():
        return None, "A descrição do vídeo está vazia."

    camera = camera or CAMERAS[-1]
    proporcao = proporcao or PROPORCOES[0]
    duracao = duracao or DURACAO_PADRAO

    camera, proporcao, duracao = validar_configuracao(
        camera,
        proporcao,
        duracao,
    )

    motor_escolhido = escolher_motor(motor)

    if not motor_escolhido:
        return None, "Nenhum motor de vídeo está disponível."

    pedido = {
        "descricao": descricao.strip(),
        "motor": motor_escolhido,
        "camera": camera,
        "proporcao": proporcao,
        "duracao": duracao,
    }

    return pedido, None


def status_motores():
    """
    Retorna o estado básico dos motores.

    O sistema real de disponibilidade será conectado
    posteriormente a cada motor.
    """

    return {
        motor: {
            "disponivel": True,
            "status": "pronto",
        }
        for motor in MOTORES_VIDEO
    }
