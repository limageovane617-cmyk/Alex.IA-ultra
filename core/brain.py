# ============================================================
# 🧠 CORE / BRAIN.PY — CÉREBRO DA ALEX IA ULTRA
# ============================================================

from concurrent.futures import ThreadPoolExecutor
from google.genai import types

# ------------------------------------------------------------
# 1. DEFINIÇÃO DAS FERRAMENTAS
# ------------------------------------------------------------

def ferramenta_gerar_imagem(prompt: str) -> dict:
    """Gera uma imagem digital ou fotografia realista a partir de um prompt."""
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
    """Gera um único vídeo curto a partir de uma descrição textual."""
    import video
    
    resultado = video.gerar_video(
        prompt=prompt,
        descricao=prompt,
        duracao=duracao,
        proporcao=proporcao
    )
    
    if isinstance(resultado, dict) and resultado.get("sucesso"):
        return {
            "sucesso": True,
            "tipo": "video",
            "prompt": prompt,
            "arquivo": resultado.get("video") or resultado.get("arquivo")
        }
    
    return {"sucesso": False, "erro": "Falha na geração do vídeo."}


def ferramenta_gerar_multiplos_videos(prompts_separados_por_barra: str, duracao: int = 5, proporcao: str = "16:9") -> dict:
    """Gera múltiplos vídeos em lote a partir de descrições separadas por '|'."""
    import video

    lista_prompts = [p.strip() for p in prompts_separados_por_barra.split("|") if p.strip()]

    def processar_um_video(p):
        res = video.gerar_video(
            prompt=p,
            descricao=p,
            duracao=duracao,
            proporcao=proporcao
        )
        caminho = res.get("video") or res.get("arquivo") if isinstance(res, dict) else None
        if caminho:
            return {"prompt": p, "arquivo": caminho, "sucesso": True}
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

REGRAS DE EXECUÇÃO OBRIGATÓRIA:
- Quando o usuário pedir para criar, gerar ou mostrar um VÍDEO, você DEVE OBRIGATORIAMENTE acionar 'ferramenta_gerar_video' ou 'ferramenta_gerar_multiplos_videos'.
- JAMAIS responda em texto dizendo que está indisponível ou com instabilidade. Sempre execute a ferramenta.
- Se o pedido tiver 2 ou mais vídeos, use 'ferramenta_gerar_multiplos_videos' separando por '|'.
- Duração padrão: {duracao_pref}s | Proporção: {proporcao_pref}.
"""

    config_geracao = types.GenerateContentConfig(
        system_instruction=instrucao_completa,
        tools=LISTA_FERRAMENTAS,
        temperature=0.2,
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
                    "tipo": "imagem" if res.get("sucesso") else "texto",
                    "texto": f"🖼️ Imagem gerada: **{prompt}**" if res.get("sucesso") else "Não foi possível gerar a imagem.",
                    "arquivo": res.get("arquivo")
                }

            elif nome_funcao == "ferramenta_gerar_video":
                prompt = argumentos.get("prompt", mensagem_usuario)
                duracao = argumentos.get("duracao", duracao_pref)
                proporcao = argumentos.get("proporcao", proporcao_pref)
                res = ferramenta_gerar_video(prompt, duracao, proporcao)
                sucesso = res.get("sucesso")
                return {
                    "tipo": "video" if sucesso else "texto",
                    "texto": f"🎬 Vídeo gerado ({duracao}s): **{prompt}**" if sucesso else "⚠️ Não foi possível processar este vídeo no momento.",
                    "arquivo": res.get("arquivo")
                }

            elif nome_funcao == "ferramenta_gerar_multiplos_videos":
                prompts_raw = argumentos.get("prompts_separados_por_barra", mensagem_usuario)
                duracao = argumentos.get("duracao", duracao_pref)
                proporcao = argumentos.get("proporcao", proporcao_pref)
                res = ferramenta_gerar_multiplos_videos(prompts_raw, duracao, proporcao)
                return {
                    "tipo": "multiplos_videos" if res.get("sucesso") else "texto",
                    "texto": f"🎬 Gerados **{res.get('total', 0)} vídeo(s)** com sucesso!" if res.get("sucesso") else "⚠️ Falha ao gerar os vídeos em lote.",
                    "lista_videos": res.get("lista_videos", []),
                    "arquivo": None
                }

        texto_resposta = resposta.text if resposta.text else "Processado."
        return {
            "tipo": "texto",
            "texto": texto_resposta,
            "arquivo": None
        }

    except Exception as e:
        return {
            "tipo": "texto",
            "texto": f"⚠️ Ocorreu um erro no processamento: {str(e)}",
            "arquivo": None
        }
        
