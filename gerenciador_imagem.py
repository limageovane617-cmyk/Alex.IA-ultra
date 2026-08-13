# ============================================================
# 🖼️ ALEX IA ULTRA — GERENCIADOR DE IMAGENS
# Criado por Geovani
# ============================================================

import os
from pathlib import Path
import streamlit as st

try:
    from google.genai import types
except Exception:
    types = None

try:
    from servicos import criar_cliente_gemini
except Exception:
    criar_cliente_gemini = None


# ============================================================
# ⚙️ MOTORES DE IMAGEM
# ============================================================

MOTORES_IMAGEM = [
    "gemini-3.1-flash-image",
    "gemini-2.5-flash-image",
]


# ============================================================
# 💾 GUARDAR ÚLTIMA IMAGEM
# ============================================================

def guardar_ultima_imagem(imagem, prompt, caminho=None, motor=None):
    """Guarda a última imagem para análise posterior."""

    try:
        st.session_state.ultima_imagem = imagem
        st.session_state.ultima_imagem_caminho = caminho
        st.session_state.ultimo_prompt_imagem = prompt
        st.session_state.ultimo_motor_imagem = motor
        return True
    except Exception:
        return False


# ============================================================
# 📁 PASTA DAS IMAGENS
# ============================================================

def obter_pasta_imagens():
    pasta = Path(os.path.join("/tmp", "alex_ia_ultra_imagens"))
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


# ============================================================
# 🎨 GERAR COM GEMINI
# ============================================================

def _gerar_com_gemini(prompt, modelo):

    if criar_cliente_gemini is None:
        raise RuntimeError("Não foi possível importar criar_cliente_gemini().")

    cliente = criar_cliente_gemini()

    if cliente is None:
        raise RuntimeError(
            "Não foi possível criar o cliente Gemini. "
            "Verifique GEMINI_API_KEY nos Secrets."
        )

    if types is None:
        raise RuntimeError("O pacote google-genai não está instalado.")

    resposta = cliente.models.generate_content(
        model=modelo,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"]
        ),
    )

    candidatos = getattr(resposta, "candidates", None) or []

    for candidato in candidatos:

        conteudo = getattr(candidato, "content", None)

        if not conteudo:
            continue

        partes = getattr(conteudo, "parts", None) or []

        for parte in partes:

            dados = getattr(parte, "inline_data", None)

            if dados is None:
                continue

            imagem_bytes = getattr(dados, "data", None)

            if not imagem_bytes:
                continue

            pasta = obter_pasta_imagens()
            caminho = pasta / "ultima_imagem.png"

            with open(caminho, "wb") as arquivo:
                arquivo.write(imagem_bytes)

            return str(caminho)

    raise RuntimeError(
        "O Gemini terminou, mas não retornou uma imagem."
    )


# ============================================================
# 🖼️ GERAR IMAGEM — FALLBACK AUTOMÁTICO
# ============================================================

def gerar_imagem(prompt):
    """
    Tenta os motores de imagem em sequência.
    Se um motor estiver sem cota (429), tenta o próximo.
    """

    if not prompt or not prompt.strip():
        return None, "❌ O prompt da imagem está vazio."

    erros = []

    for modelo in MOTORES_IMAGEM:

        try:

            caminho = _gerar_com_gemini(
                prompt.strip(),
                modelo,
            )

            guardar_ultima_imagem(
                imagem=caminho,
                prompt=prompt,
                caminho=caminho,
                motor=modelo,
            )

            return (
                caminho,
                f"🖼️ Imagem gerada pelo motor {modelo}."
            )

        except Exception as erro:

            erros.append(
                f"{modelo}: {erro}"
            )

            # Se este motor falhou, continua automaticamente.
            continue

    return (
        None,
        "❌ Todos os motores de imagem falharam.\n\n"
        + "\n\n".join(erros)
    )


# ============================================================
# 🖼️ MOSTRAR IMAGEM
# ============================================================

def mostrar_imagem(prompt):

    with st.spinner(
        "🎨 Alex IA está criando sua imagem..."
    ):

        imagem, mensagem = gerar_imagem(prompt)

    if imagem is None:

        st.error(mensagem)
        return False

    st.image(
        imagem,
        caption="🖼️ Imagem gerada pela Alex IA Ultra",
        use_container_width=True,
    )

    motor = st.session_state.get(
        "ultimo_motor_imagem"
    )

    if motor:
        st.caption(
            f"🎨 Motor utilizado: {motor}"
        )

    return True


# ============================================================
# 🔎 ACESSO À ÚLTIMA IMAGEM
# ============================================================

def obter_ultima_imagem():
    return st.session_state.get(
        "ultima_imagem"
    )


def obter_caminho_ultima_imagem():
    return st.session_state.get(
        "ultima_imagem_caminho"
    )


def obter_prompt_ultima_imagem():
    return st.session_state.get(
        "ultimo_prompt_imagem",
        ""
    )


# ============================================================
# 🧹 LIMPAR ÚLTIMA IMAGEM
# ============================================================

def limpar_ultima_imagem():

    for chave in [
        "ultima_imagem",
        "ultima_imagem_caminho",
        "ultimo_prompt_imagem",
        "ultimo_motor_imagem",
    ]:
        st.session_state.pop(chave, None)
