# ============================================================
# 🧠 CORE / BRAIN.PY — CÉREBRO DA ALEX IA ULTRA
# Gerencia Function Calling e autonomia do modelo
# ============================================================

import re
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
    """Gera um vídeo curto ou animação a partir de uma descrição textual de cena ou ação.
    
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

# Lista de funções expostas nativamente para o Gemini
LISTA_FERRAMENTAS = [ferramenta_gerar_imagem, ferramenta_gerar_video]

# ------------------------------------------------------------
# 2. PROCESSADOR DE MENSAGENS COM AUTONOMIA NATIVA
# ------------------------------------------------------------

def processar_resposta_alex(cliente, modelo_id: str, prompt_sistema: str, historico: list, mensagem_usuario: str, config_video: dict) -> dict:
    """Envia a mensagem ao Gemini com Function Calling ativo. 
    A IA decide se responde com texto normal ou aciona uma ferramenta.
    """
    # Injeta a configuração de vídeo preferida pelo usuário no contexto das ferramentas
    duracao_pref = config_video.get("duracao", 5)
    proporcao_pref = config_video.get("proporcao", "16:9")
    
    instrucao_completa = f"""{prompt_sistema}

Você possui ferramentas nativas para criar imagens e vídeos. 
Quando o usuário solicitar artes visuais ou produções de vídeo, use as ferramentas apropriadas.
Preferências padrão de vídeo ativas: Duração {duracao_pref}s, Proporção {proporcao_pref}.
Responda sempre em português do Brasil de forma amigável e precisa.
"""

    # Formata o histórico recente para contextualizar a chamada
    mensagens_contexto = []
    for msg in historico[-10:]:
        if msg.get("tipo") == "texto":
            role = "user" if msg.get("role") == "user" else "model"
            mensagens_contexto.append({"role": role, "parts": [{"text": msg.get("content", "")}]})

    mensagens_contexto.append({"role": "user", "parts": [{"text": mensagem_usuario}]})

    # Configuração de chamada com Function Calling Habilitado
    config_geracao = types.GenerateContentConfig(
        system_instruction=instrucao_completa,
        tools=LISTA_FERRAMENTAS,
        temperature=0.7,
    )

    # Chamada única ao Gemini: O modelo escolhe a ferramenta se necessário
    resposta = cliente.models.generate_content(
        model=modelo_id,
        contents=mensagem_usuario,
        config=config_geracao
    )

    # Caso a IA decida chamar uma ferramenta autonomamente
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

    # Resposta padrão em texto
    texto_resposta = resposta.text if resposta.text else "Não consegui processar a resposta."
    return {
        "tipo": "texto",
        "texto": texto_resposta,
        "arquivo": None
  }
  
