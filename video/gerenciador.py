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

from .motores.registro import (
    obter_motores,
    listar_motores as listar_motores_registrados,
    buscar_motor,
)


def listar_motores():
    """Retorna os motores registrados na Alex IA Ultra."""

    return listar_motores_registrados()


def escolher_motor(preferido=None):
    """
    Escolhe automaticamente um motor de vídeo.

    Se um motor específico for informado e estiver registrado,
    ele será utilizado.

    Caso contrário, o sistema procura um motor disponível.
    """

    motores = obter_motores()

    if not motores:
        return None

    if preferido:
        motor = buscar_motor(preferido)

        if motor is not None:
            return motor

    for motor in motores:
        if getattr(motor, "disponivel", False):
            return motor

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

    Nesta etapa o sistema organiza o pedido e
    seleciona o motor registrado.
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
        "motor": motor_escolhido.nome,
        "camera": camera,
        "proporcao": proporcao,
        "duracao": duracao,
    }

    return pedido, None


def status_motores():
    """
    Retorna o estado dos motores registrados.
    """

    motores = obter_motores()

    return {
        motor.nome: {
            "disponivel": getattr(
                motor,
                "disponivel",
                False,
            ),
            "status": (
                "pronto"
                if getattr(motor, "disponivel", False)
                else "indisponível"
            ),
        }
        for motor in motores
    }
