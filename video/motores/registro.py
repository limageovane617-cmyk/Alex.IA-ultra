# ============================================================
# 🎬 ALEX IA ULTRA — REGISTRO DE MOTORES
# Criada por Geovani
# ============================================================

from .wan import WanMotor


def obter_motores():
    """
    Cria e retorna todos os motores de vídeo
    atualmente cadastrados na Ultra.
    """

    return [
        WanMotor(),
    ]


def listar_motores():
    """
    Retorna somente os nomes dos motores cadastrados.
    """

    motores = obter_motores()

    return [motor.nome for motor in motores]


def buscar_motor(nome):
    """
    Procura um motor pelo nome.

    Retorna o motor encontrado ou None.
    """

    if not nome:
        return None

    nome = nome.strip().lower()

    for motor in obter_motores():
        if motor.nome.lower() == nome:
            return motor

    return None


def primeiro_motor_disponivel():
    """
    Retorna o primeiro motor disponível.
    """

    for motor in obter_motores():
        if getattr(motor, "disponivel", False):
            return motor

    return None


def status_motores():
    """
    Retorna o estado atual de todos os motores.
    """

    resultado = []

    for motor in obter_motores():
        resultado.append(
            {
                "nome": motor.nome,
                "disponivel": getattr(
                    motor,
                    "disponivel",
                    False
                ),
            }
        )

    return resultado


if __name__ == "__main__":
    print("🎬 ALEX IA ULTRA — REGISTRO DE MOTORES")
    print()

    print("Motores cadastrados:")
    for nome in listar_motores():
        print(f"  • {nome}")

    print()
    print("Status:")

    for item in status_motores():
        estado = "OK" if item["disponivel"] else "INDISPONÍVEL"
        print(f"  • {item['nome']}: {estado}")
