# ============================================================
# 🎬 ALEX IA ULTRA — GERENCIADOR DE VÍDEO
# Criada por Geovani
# ============================================================

from .configuracao import (
    CAMERAS,
    PROPORCOES,
    DURACAO_PADRAO,
)

from .motores.registro import (
    obter_motores,
    listar_motores as listar_motores_registrados,
    buscar_motor,
    primeiro_motor_disponivel,
    status_motores as status_motores_registrados,
)


# ============================================================
# 🎬 MOTORES
# ============================================================

def listar_motores():
    """Retorna os nomes dos motores realmente registrados."""
    return listar_motores_registrados()


def escolher_motor(preferido=None):
    """
    Escolhe um motor registrado.

    Se o usuário indicar um motor existente,
    ele será utilizado.

    Caso contrário, a Ultra procura automaticamente
    o primeiro motor disponível.
    """

    if preferido:
        motor = buscar_motor(preferido)

        if motor is not None and getattr(
            motor,
            "disponivel",
            False
        ):
            return motor

    return primeiro_motor_disponivel()


# ============================================================
# ⚙️ CONFIGURAÇÃO
# ============================================================

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


# ============================================================
# 🎬 PREPARAÇÃO DO VÍDEO
# ============================================================

def preparar_video(
    descricao,
    camera=None,
    proporcao=None,
    duracao=None,
    motor=None,
):
    """
    Prepara uma solicitação de vídeo.

    O gerenciador escolhe um motor registrado e
    organiza todas as configurações necessárias.
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

    if motor_escolhido is None:
        return None, (
            "Nenhum motor de vídeo está disponível."
        )

    pedido = {
        "descricao": descricao.strip(),
        "motor": motor_escolhido.nome,
        "camera": camera,
        "proporcao": proporcao,
        "duracao": duracao,
    }

    return pedido, None


# ============================================================
# 🎬 GERAÇÃO
# ============================================================

def gerar_com_motor(
    descricao,
    camera=None,
    proporcao=None,
    duracao=None,
    motor=None,
    imagem=None,
):
    """
    Envia o pedido para o motor escolhido.

    Nesta etapa o motor Wan prepara a solicitação.
    A conexão real com o serviço de geração será
    adicionada separadamente.
    """

    pedido, erro = preparar_video(
        descricao=descricao,
        camera=camera,
        proporcao=proporcao,
        duracao=duracao,
        motor=motor,
    )

    if erro:
        return None, erro

    motor_objeto = buscar_motor(
        pedido["motor"]
    )

    if motor_objeto is None:
        return None, (
            f"O motor '{pedido['motor']}' "
            "não foi encontrado."
        )

    try:
        resultado = motor_objeto.gerar(
            prompt=pedido["descricao"],
            imagem=imagem,
            camera=pedido["camera"],
            proporcao=pedido["proporcao"],
            duracao=pedido["duracao"],
        )

        return resultado, None

    except Exception as erro_motor:
        return None, (
            f"Erro no motor {pedido['motor']}: "
            f"{erro_motor}"
        )


# ============================================================
# 📊 STATUS DOS MOTORES
# ============================================================

def status_motores():
    """Retorna o status dos motores registrados."""

    return status_motores_registrados()


# ============================================================
# 🧪 TESTE DO SISTEMA
# ============================================================

def testar_gerenciador():
    """
    Faz um teste simples da central de motores.
    Não gera vídeo real.
    """

    motores = obter_motores()

    if not motores:
        return False, "Nenhum motor registrado."

    motor = primeiro_motor_disponivel()

    if motor is None:
        return False, "Nenhum motor está disponível."

    return True, (
        f"Gerenciador funcionando. "
        f"Motor selecionado: {motor.nome}"
    )
