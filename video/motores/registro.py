# ============================================================
# 🎬 ALEX IA ULTRA — REGISTRO DE MOTORES
# Criada por Geovani
# ============================================================

from .wan import WanMotor


def obter_motores():
    """
    Cria e retorna todos os motores de vídeo
    atualmente registrados na Ultra.
    """

    return [
        WanMotor(),
    ]


def listar_motores():
    """
    Retorna somente os nomes dos motores registrados.
    """

    motores = obter_motores()

    return [
        motor.nome
        for motor in motores
    ]


def buscar_motor(nome):
    """
    Procura um motor pelo nome.

    Retorna o motor encontrado ou None.
    """

    if not nome:
        return None

    nome = str(nome).strip().lower()

    for motor in obter_motores():

        nome_motor = getattr(
            motor,
            "nome",
            "",
        )

        if nome_motor.lower() == nome:
            return motor

    return None


def motor_disponivel(nome):
    """
    Verifica se determinado motor está disponível.
    """

    motor = buscar_motor(nome)

    if motor is None:
        return False

    return bool(
        getattr(
            motor,
            "disponivel",
            False,
        )
    )


def status_motores():
    """
    Retorna o status de todos os motores registrados.
    """

    resultado = {}

    for motor in obter_motores():

        nome = getattr(
            motor,
            "nome",
            "Desconhecido",
        )

        disponivel = bool(
            getattr(
                motor,
                "disponivel",
                False,
            )
        )

        resultado[nome] = {
            "disponivel": disponivel,
            "status": (
                "pronto"
                if disponivel
                else "indisponível"
            ),
        }

    return resultado
