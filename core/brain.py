# ============================================================
# 🧠 CORE / BRAIN.PY — CÉREBRO DA ALEX IA ULTRA
# Gerencia Function Calling e autonomia do modelo (Com Vídeos em Lote)
# ============================================================

from concurrent.futures import ThreadPoolExecutor
from google.genai import types

# ------------------------------------------------------------
# 1. DEFINIÇÃO DAS FERRAMENTAS QUE A ALEX PODE CHAMAR
# ------------------------------------------------------------

def ferramenta_gerar_imagem(prompt: str) -> dict:
    """Gera uma imagem digital ou fotografia realista com base em uma descrição visual detalhada.
    
    Args:
        prompt: Descrição detalhada e criativa da imagem a ser gerada.
    """
    from gerenciador_imagem import mostrar_imagem
    import streamlit as st
    
    sucesso = mostrar_imagem(prompt)
    caminho = st.session_state.get("ultima_imagem_caminho") if sucesso else None
    
    return {
        "sucesso": sucesso,
        "tipo": "imagem",
        "prompt": prompt,
        "arquivo": caminho
    }


def ferramenta_gerar_video(prompt: str, duracao: int = 5, proporcao: str = "16:9") -> dict:
    """Gera um único vídeo curto a partir de uma descrição textual de cena.
    
    Args:
        prompt: Descrição da cena, ação e movimento de câmera do vídeo.
        duracao: Tempo em segundos do vídeo (padrão 5s).
        proporcao: Formato do vídeo (16:9, 9:16 ou 1:1).
    """
    import video
    
    resultado = video.gerar_video(
        descricao=prompt,
        camera="Sony FX6",
        proporcao=proporcao,
        duracao=duracao,
        width=512,
        height=512
    )
    
    if isinstance(resultado, dict) and resultado.get("sucesso"):
        return {
            "sucesso": True,
            "tipo": "video",
            "prompt": prompt,
            "arquivo": resultado.get("video")
        }
    
    return {"sucesso": False, "erro": "Falha na geração do vídeo."}


def ferramenta_gerar_multiplos_videos(prompts: list[str], duracao: int = 5, proporcao: str = "16:9") -> dict:
    """Gera uma lista com vários vídeos de forma paralela/assíncrona a partir de múltiplas descrições.
    
    Args:
        prompts: Lista de descrições textuais (uma para cada vídeo desejado).
        duracao: Duração de cada vídeo em segundos.
        proporcao: Formato dos vídeos (16:9, 9:16 ou 1:1).
    """
    import video

    def processar_um_video(p):
        res = video.gerar_video(
            descricao=p,
            camera="Sony FX6",
            proporcao=proporcao,
            duracao=duracao,
            width=512,
            height=512
        )
        if isinstance(res, dict) and res.get("sucesso"):
            return {"prompt": p, "arquivo": res.get("video"), "sucesso": True}
        return {"prompt": p, "arquivo": None, "sucesso": False}

    # Processa até 3 vídeos em paralelo para acelerar sem estourar limite
    resultados = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        resultados = list(executor.map(processar_um_video, prompts))

    videos_gerados = [r for r in resultados if r["sucesso"]]

    return {
        "sucesso": len(videos_gerados) > 0,
        "tipo": "multiplos_videos",
        "lista_videos": videos_gerados,
        "total": len(videos_gerados)
    }

# Lista de funções expostas nativamente para o Gemini
LISTA_FERRAMENTAS = [
    ferramenta_gerar_imagem, 
    ferramenta_gerar_video, 
    ferramenta_gerar_multiplos_videos
]

# ------------------------------------------------------------
# 2. PROCESSADOR DE MENSAGENS COM AUTONOMIA NATIVA
# ------------------------------------------------------------

def processar_resposta_alex(cliente, modelo_id: str, prompt_sistema: str, historico: list, mensagem_usuario: str, config_video: dict) -> dict:
    """Envia a mensagem ao Gemini com Function Calling ativo."""
    duracao_pref = config_video.get("duracao", 5)
    proporcao_pref = config_video.get("proporcao", "16:9")
    
    instrucao_completa = f"""{prompt_sistema}

Você possui ferramentas nativas para criar imagens, vídeos individuais e múltiplos vídeos simultâneos.
Quando o usuário pedir 2 ou mais vídeos (ex: "crie 3 vídeos de...", "gera vídeos sobre X, Y e Z"), use 'ferramenta_gerar_multiplos_videos'.
Preferências de vídeo: Duração {duracao_pref}s, Proporção {proporcao_pref}.
Responda sempre em português do Brasil de forma amigável e precisa.
"""

    config_geracao = types.GenerateContentConfig(
        system_instruction=instrucao_completa,
        tools=LISTA_FERRAMENTAS,
        temperature=0.7,
    )

    resposta = cliente.models.generate_content(
        model=modelo_id,
        contents=mensagem_usuario,
        config=config_geracao
    )

    if resposta.function_calls:
        chamada = resposta.function_calls[0]
        nome_funcao = chamada.name
        argumentos = chamada.args

        if nome_funcao == "ferramenta_gerar_imagem":
            prompt = argumentos.get("prompt", mensagem_usuario)
            res = ferramenta_gerar_imagem(prompt)
            return {
                "tipo": "imagem",
                "texto": f"🖼️ Aqui está a imagem gerada sobre: **{prompt}**",
                "arquivo": res.get("arquivo")
            }

        elif nome_funcao == "ferramenta_gerar_video":
            prompt = argumentos.get("prompt", mensagem_usuario)
            duracao = argumentos.get("duracao", duracao_pref)
            proporcao = argumentos.get("proporcao", proporcao_pref)
            res = ferramenta_gerar_video(prompt, duracao, proporcao)
            return {
                "tipo": "video",
                "texto": f"🎬 Aqui está o vídeo gerado ({duracao}s) sobre: **{prompt}**",
                "arquivo": res.get("arquivo")
            }

        elif nome_funcao == "ferramenta_gerar_multiplos_videos":
            prompts = argumentos.get("prompts", [mensagem_usuario])
            duracao = argumentos.get("duracao", duracao_pref)
            proporcao = argumentos.get("proporcao", proporcao_pref)
            res = ferramenta_gerar_multiplos_videos(prompts, duracao, proporcao)
            return {
                "tipo": "multiplos_videos",
                "texto": f"🎬 Gerados **{res['total']} vídeos** com sucesso!",
                "lista_videos": res.get("lista_videos", [])
            }

    texto_resposta = resposta.text if resposta.text else "Não consegui processar a resposta."
    return {
        "tipo": "texto",
        "texto": texto_resposta,
        "arquivo": None
            }
    
