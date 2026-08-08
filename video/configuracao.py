# ============================================================
# 🎬 ALEX IA ULTRA — CONFIGURAÇÃO DO SISTEMA DE VÍDEO
# Criada por Geovani
# ============================================================

# Motores disponíveis
MOTORES_VIDEO = [
    "Google Veo",
    "Wan",
]

# Câmeras cinematográficas disponíveis
CAMERAS = [
    "Sony FX5",
    "Sony FX6",
    "Canon EOS C80",
    "ARRI Alexa Mini LF",
]

# Proporções
PROPORCOES = [
    "16:9",
    "9:16",
]

# Duração padrão
DURACAO_PADRAO = 8

# Modelo principal do Google
MODELO_VEO = "veo-3.1-generate-preview"


def obter_motores():
    """Retorna os motores disponíveis."""
    return MOTORES_VIDEO


def obter_cameras():
    """Retorna as câmeras disponíveis."""
    return CAMERAS


def obter_proporcoes():
    """Retorna as proporções disponíveis."""
    return PROPORCOES


def obter_duracao():
    """Retorna a duração padrão do vídeo."""
    return DURACAO_PADRAO
