# ============================================================
# 🎬 ALEX IA ULTRA — SISTEMA DE VÍDEO
# Criada por Geovani
# ============================================================

import os
import time
import tempfile
from pathlib import Path

import streamlit as st
from google import genai
from google.genai import types


CAMERAS = [
    "Sony FX5",
    "Sony FX6",
    "Canon EOS C80",
    "ARRI Alexa Mini LF",
]

PROPORCOES = ["16:9", "9:16"]
DURACAO_VIDEO = 8
MODELO_VEO = "veo-3.1-generate-preview"


def obter_chave_gemini():
    """Obtém a chave sem pedir ao usuário na interface."""
    try:
        chave = st.secrets.get("GEMINI_API_KEY")
        if chave:
            return str(chave).strip()
    except Exception:
        pass
    chave = os.getenv("GEMINI_API_KEY")
    return chave.strip() if chave else None


def criar_cliente_gemini():
    chave = obter_chave_gemini()
    if not chave:
        return None, (
            "A chave GEMINI_API_KEY não foi encontrada. "
            "Adicione-a aos Secrets do Streamlit."
        )
    try:
        return genai.Client(api_key=chave), None
    except Exception as erro:
        return None, f"Não foi possível conectar ao Gemini: {erro}"


def preparar_prompt_video(
    descricao,
    camera="ARRI Alexa Mini LF",
    proporcao="16:9",
    duracao=8,
):
    """Monta o prompt cinematográfico enviado ao Veo."""
    if not descricao or not descricao.strip():
        return None

    if camera not in CAMERAS:
        camera = "ARRI Alexa Mini LF"
    if proporcao not in PROPORCOES:
        proporcao = "16:9"

    # A integração atual usa 8 segundos.
    duracao = DURACAO_VIDEO

    return f"""Crie um vídeo cinematográfico baseado na seguinte descrição:

{descricao.strip()}

DIREÇÃO CINEMATOGRÁFICA

Câmera de referência: {camera}
Proporção: {proporcao}
Duração: {duracao} segundos

Use linguagem visual cinematográfica de alta qualidade, iluminação realista,
profundidade de campo cinematográfica, composição profissional e movimentos
de câmera naturais e fisicamente plausíveis.

CONTINUIDADE

Mantenha consistência visual dos personagens, rostos, cabelos, roupas,
acessórios, ambiente, objetos e elementos importantes durante toda a cena.
Não altere características importantes do personagem sem instrução explícita.
Não troque a identidade do personagem nem modifique roupas ou aparência sem
motivo. Evite deformações, duplicações e alterações bruscas.

ÁUDIO

Quando apropriado, inclua áudio ambiente, efeitos sonoros e sons
cinematográficos coerentes com a cena. O resultado deve ser imersivo,
detalhado e visualmente profissional.
""".strip()


def gerar_video(
    descricao,
    camera="ARRI Alexa Mini LF",
    proporcao="16:9",
    duracao=8,
):
    """Gera um vídeo real com o Google Veo 3.1 e retorna (caminho, mensagem)."""
    prompt = preparar_prompt_video(descricao, camera, proporcao, duracao)
    if not prompt:
        return None, "A descrição do vídeo está vazia."

    cliente, erro = criar_cliente_gemini()
    if erro:
        return None, erro

    try:
        operacao = cliente.models.generate_videos(
            model=MODELO_VEO,
            prompt=prompt,
            config=types.GenerateVideosConfig(
                number_of_videos=1,
                aspect_ratio=proporcao,
                resolution="720p",
            ),
        )

        while not operacao.done:
            time.sleep(10)
            operacao = cliente.operations.get(operacao)

        if getattr(operacao, "error", None):
            return None, f"Erro na geração do vídeo: {operacao.error}"

        resposta = getattr(operacao, "response", None)
        videos = getattr(resposta, "generated_videos", None) if resposta else None
        if not videos:
            return None, "O Veo terminou, mas não retornou um vídeo."

        video = videos[0].video
        pasta = Path(tempfile.gettempdir()) / "alex_ia_ultra"
        pasta.mkdir(parents=True, exist_ok=True)
        caminho = pasta / "video_gerado.mp4"

        # O SDK oficial baixa o arquivo e permite salvá-lo em MP4.
        cliente.files.download(file=video)
        video.save(str(caminho))

        if not caminho.exists() or caminho.stat().st_size == 0:
            return None, "O vídeo foi gerado, mas não pôde ser salvo."

        return str(caminho), "Vídeo gerado com sucesso."

    except Exception as erro:
        return None, f"Erro ao gerar o vídeo: {erro}"


def mostrar_configuracao_video():
    camera = st.selectbox(
        "🎥 Câmera cinematográfica",
        CAMERAS,
        index=3,
        key="video_camera",
    )
    proporcao = st.selectbox(
        "📐 Proporção",
        PROPORCOES,
        index=0,
        key="video_proporcao",
    )
    st.info("🎬 O Veo 3.1 gera vídeos de aproximadamente 8 segundos nesta integração.")
    return camera, proporcao, DURACAO_VIDEO


def mostrar_gerador_video():
    """Interface pronta para ser chamada pelo app.py."""
    st.subheader("🎬 Gerador de Vídeo Cinematográfico")
    camera, proporcao, duracao = mostrar_configuracao_video()

    descricao = st.text_area(
        "🎞️ Descreva o vídeo que deseja criar",
        placeholder=(
            "Exemplo: uma cidade futurista à noite, com carros voadores "
            "atravessando os prédios enquanto a câmera avança lentamente."
        ),
        height=150,
        key="video_descricao",
    )

    if st.button("🎬 Gerar vídeo", type="primary", key="gerar_video_ultra"):
        if not descricao.strip():
            st.warning("Digite uma descrição para o vídeo.")
            return

        with st.spinner("🎬 O Veo está criando seu vídeo cinematográfico..."):
            caminho, mensagem = gerar_video(
                descricao=descricao,
                camera=camera,
                proporcao=proporcao,
                duracao=duracao,
            )

        if caminho:
            st.success(mensagem)
            st.video(caminho)
            with open(caminho, "rb") as arquivo:
                st.download_button(
                    "⬇️ Baixar vídeo MP4",
                    data=arquivo.read(),
                    file_name="alex_ia_video.mp4",
                    mime="video/mp4",
                    key="baixar_video_ultra",
                )
        else:
            st.error(mensagem)


if __name__ == "__main__":
    st.set_page_config(
        page_title="Alex IA Ultra — Vídeo",
        page_icon="🎬",
        layout="wide",
    )
    st.title("🤖 Alex IA Ultra")
    st.caption("🎬 Sistema de geração de vídeo cinematográfico")
    mostrar_gerador_video()
