# ============================================================
# 🎬 ALEX IA ULTRA — MÓDULO DE VÍDEO
# Criada por Geovani
# ============================================================

from .configuracao import (
    MOTORES_VIDEO,
    CAMERAS,
    PROPORCOES,
    DURACAO_PADRAO,
    MODELO_VEO,
)

from .gerenciador import (
    listar_motores,
    escolher_motor,
    validar_configuracao,
    preparar_video,
    status_motores,
)
