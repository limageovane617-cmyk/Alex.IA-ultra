# ============================================================
# 🧠 CORE / BRAIN.PY — CÉREBRO DA ALEX IA ULTRA
# Gerencia Function Calling e autonomia do modelo (Estável)
# ============================================================

from concurrent.futures import ThreadPoolExecutor
from google.genai import types

# ------------------------------------------------------------
# 1. DEFINIÇÃO DAS FERRAMENTAS
# ------------------------------------------------------------

def ferramenta_gerar_imagem(prompt: str) -> dict:
    """Gera uma imagem digital ou fotografia realista com base em uma descrição visual detalhada.
    
    Args:
        prompt: Descrição detalhada da imagem a ser gerada.
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
    """Gera um único vídeo curto a partir de uma descrição textual.
    
    Args:
        prompt: Descrição da cena ou ação do vídeo.
        duracao: Tempo em segundos (padrão 5).
        proporcao: Formato (16:9, 9:16 ou 1:1).
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


def ferramenta_gerar_multiplos_videos(prompts_separados_por_barra: str, duracao: int = 5, proporcao: str = "16:9") -> dict:
    """Gera múltiplos vídeos em lote a partir de descrições separadas por barra vertical '|'.
    
    Args:
        prompts_separados_por_barra: Descrições dos vídeos separadas por '|' (ex: "praia futurista | cidade cyberpunk").
        duracao: Tempo em segundos de cada vídeo.
        proporcao: Formato dos vídeos (16:9, 9:16 ou 1:1).
    """
    import video

    lista_prompts = [p.strip() for p in prompts_separados_por_barra.split("|") if p.strip()]

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

    resultados = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(executor.map(processar_um_video, lista_prompts))

    videos_gerados = [r for r in resultados if r["sucesso"]]

    return {
        "sucesso": len(videos_gerados) > 0,
        "tipo": "multiplos_videos",
        "lista_videos": videos_gerados,
        "total": len(videos_gerados)
    }

LISTA_FERRAMENTAS = [
    ferramenta_gerar_imagem, 
    ferramenta_gerar_video, 
    ferramenta_gerar_multiplos_videos
]

# ------------------------------------------------------------
# 2. PROCESSADOR DE MENSAGENS
# ------------------------------------------------------------

def processar_resposta_alex(cliente, modelo_id: str, prompt_sistema: str, historico: list, mensagem_usuario: str, config_video: dict) -> dict:
    duracao_pref = config_video.get("duracao", 5)
    proporcao_pref = config_video.get("proporcao", "16:9")
    
    instrucao_completa = f"""{prompt_sistema}

Você é a Alex IA. Use as ferramentas sempre que o usuário solicitar imagens ou vídeos.
- Quando o usuário pedir 2 ou mais vídeos, use obrigatoriamente 'ferramenta_gerar_multiplos_videos' enviando os prompts separados pelo caractere '|' (ex: "cena 1 | cena 2").
- Quando pedir 1 vídeo, use 'ferramenta_gerar_video'.
- Preferências de vídeo: Duração {duracao_pref}s, Proporção {proporcao_pref}.
"""

    config_geracao = types.GenerateContentConfig(
        system_instruction=instrucao_completa,
        tools=LISTA_FERRAMENTAS,
        temperature=0.3,
    )

    try:
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
                    "texto": f"🖼️ Imagem gerada sobre: **{prompt}**",
                    "arquivo": res.get("arquivo")
                }

            elif nome_funcao == "ferramenta_gerar_video":
                prompt = argumentos.get("prompt", mensagem_usuario)
                duracao = argumentos.get("duracao", duracao_pref)
                proporcao = argumentos.get("proporcao", proporcao_pref)
                res = ferramenta_gerar_video(prompt, duracao, proporcao)
                return {
                    "tipo": "video",
                    "texto": f"🎬 Vídeo gerado ({duracao}s) sobre: **{prompt}**",
                    "arquivo": res.get("arquivo")
                }

            elif nome_funcao == "ferramenta_gerar_multiplos_videos":
                prompts_raw = argumentos.get("prompts_separados_por_barra", mensagem_usuario)
                duracao = argumentos.get("duracao", duracao_pref)
                proporcao = argumentos.get("proporcao", proporcao_pref)
                res = ferramenta_gerar_multiplos_videos(prompts_raw, duracao, proporcao)
                return {
                    "tipo": "multiplos_videos",
                    "texto": f"🎬 Gerados **{res['total']} vídeos** com sucesso!",
                    "lista_videos": res.get("lista_videos", []),
                    "arquivo": None
                }

        texto_resposta = resposta.text if resposta.text else "Não consegui processar a resposta."
        return {
            "tipo": "texto",
            "texto": texto_resposta,
            "arquivo": None
        }

    except Exception as e:
        return {
            "tipo": "texto",
            "texto": f"⚠️ Ocorreu um erro no processamento da requisição: {str(e)}",
            "arquivo": None
                }
        
