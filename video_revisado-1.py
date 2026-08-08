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

# O Veo 3.1 permite extensões de 7 segundos, até 20 vezes,
# para vídeos Veo compatíveis. A saída da extensão é o vídeo
# anterior + a nova extensão.
EXTENSAO_SEGUNDOS = 7
DURACAO_MAXIMA_VIDEO = 148


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
            "❌ A chave GEMINI_API_KEY não foi encontrada. "
            "Adicione-a aos Secrets do Streamlit."
        )

    try:
        return genai.Client(api_key=chave), None
    except Exception as erro:
        return None, f"❌ Não foi possível conectar ao Gemini: {erro}"


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

    return f"""Crie um vídeo cinematográfico baseado na seguinte descrição:

{descricao.strip()}

DIREÇÃO CINEMATOGRÁFICA

Câmera de referência: {camera}
Proporção: {proporcao}
Duração: aproximadamente {DURACAO_VIDEO} segundos

Use linguagem visual cinematográfica de alta qualidade, iluminação realista,
profundidade de campo cinematográfica, composição profissional e movimentos
de câmera naturais e fisicamente plausíveis.

CONTINUIDADE VISUAL — REGRA PRIORITÁRIA

Mantenha consistência visual durante toda a cena.
Preserve a identidade dos personagens, rosto, cabelos, olhos, idade aparente,
roupas, acessórios, características físicas, objetos importantes, ambiente,
iluminação, clima, horário e estilo visual.

Não altere características importantes do personagem sem instrução explícita.
Não troque a identidade do personagem nem transforme o personagem em outra pessoa.
Não troque roupas ou acessórios sem motivo narrativo explícito.
Evite deformações, duplicações, membros extras e alterações bruscas de aparência.

FOCO NO PERSONAGEM PRINCIPAL

Quando houver um personagem principal, mantenha-o como foco visual da cena.
A câmera pode fazer travelling, pan, tilt, dolly, orbit, aproximação ou afastamento.

Se um movimento de câmera fizer o personagem sair temporariamente do enquadramento,
faça um reenquadramento natural e cinematográfico e volte o foco para o personagem.
Preserve sua identidade, rosto, cabelo, roupa e acessórios.
Não substitua o personagem.

ÁUDIO

Quando apropriado, inclua áudio ambiente, efeitos sonoros, sons naturais,
diálogos quando solicitados e atmosfera sonora cinematográfica coerente com a cena.

O resultado deve parecer uma sequência cinematográfica profissional, coerente e imersiva.
""".strip()


def obter_pasta_videos():
    pasta = Path(tempfile.gettempdir()) / "alex_ia_ultra"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def salvar_video(cliente, video, nome):
    """Baixa o objeto Video do SDK e salva em MP4."""
    pasta = obter_pasta_videos()
    caminho = pasta / nome

    cliente.files.download(file=video)
    video.save(str(caminho))

    if not caminho.exists() or caminho.stat().st_size == 0:
        return None

    return str(caminho)


def aguardar_video(cliente, operacao):
    """Espera a operação do Veo terminar e retorna o objeto Video."""
    while not operacao.done:
        time.sleep(10)
        operacao = cliente.operations.get(operacao)

    erro_operacao = getattr(operacao, "error", None)
    if erro_operacao:
        return None, f"❌ Erro na geração do vídeo: {erro_operacao}"

    resposta = getattr(operacao, "response", None)
    if resposta is None:
        return None, "❌ O Veo terminou, mas não retornou uma resposta."

    videos = getattr(resposta, "generated_videos", None)
    if not videos:
        return None, "❌ O Veo terminou, mas não retornou nenhum vídeo."

    video = getattr(videos[0], "video", None)
    if video is None:
        return None, "❌ A resposta do Veo não contém o arquivo de vídeo."

    return video, None


def gerar_video(
    descricao,
    camera="ARRI Alexa Mini LF",
    proporcao="16:9",
    duracao=8,
    imagem_referencia=None,
):
    """Gera o primeiro vídeo. Mantém a assinatura usada pelo app.py."""
    prompt = preparar_prompt_video(
        descricao=descricao,
        camera=camera,
        proporcao=proporcao,
        duracao=duracao,
    )

    if not prompt:
        return None, "❌ A descrição do vídeo está vazia."

    cliente, erro = criar_cliente_gemini()
    if erro:
        return None, erro

    try:
        config = types.GenerateVideosConfig(
            number_of_videos=1,
            aspect_ratio=proporcao,
            resolution="720p",
        )

        if imagem_referencia:
            # A imagem é usada como frame inicial/referência visual.
            imagem = types.Image.from_file(location=imagem_referencia)
            operacao = cliente.models.generate_videos(
                model=MODELO_VEO,
                prompt=prompt,
                image=imagem,
                config=config,
            )
        else:
            operacao = cliente.models.generate_videos(
                model=MODELO_VEO,
                prompt=prompt,
                config=config,
            )

        video, erro_video = aguardar_video(cliente, operacao)
        if erro_video:
            return None, erro_video

        caminho = salvar_video(
            cliente,
            video,
            "video_inicial.mp4",
        )

        if not caminho:
            return None, "❌ O vídeo foi gerado, mas não pôde ser salvo."

        # Guardamos o objeto Video retornado pelo Veo porque a extensão
        # precisa receber um vídeo que veio de uma geração anterior do Veo.
        st.session_state.video_veo_atual = video
        st.session_state.video_caminho_atual = caminho
        st.session_state.video_duracao_aproximada = DURACAO_VIDEO
        st.session_state.video_cenas = 1
        st.session_state.video_camera_atual = camera
        st.session_state.video_proporcao_atual = proporcao
        st.session_state.video_descricao_atual = descricao

        return caminho, "🎬 Vídeo inicial gerado com sucesso."

    except Exception as erro:
        return None, f"❌ Erro ao gerar o vídeo: {erro}"


def continuar_video(descricao_continuacao):
    """Estende o último vídeo Veo em aproximadamente 7 segundos."""
    video_anterior = st.session_state.get("video_veo_atual")

    if video_anterior is None:
        return None, "❌ Ainda não existe um vídeo para continuar."

    cliente, erro = criar_cliente_gemini()
    if erro:
        return None, erro

    duracao_atual = st.session_state.get(
        "video_duracao_aproximada",
        DURACAO_VIDEO,
    )

    if duracao_atual >= DURACAO_MAXIMA_VIDEO:
        return None, (
            "⚠️ O limite aproximado de extensão desta sequência foi alcançado."
        )

    descricao_continuacao = (descricao_continuacao or "").strip()
    if not descricao_continuacao:
        descricao_continuacao = (
            "Continue naturalmente a ação a partir do último momento do vídeo anterior."
        )

    camera = st.session_state.get(
        "video_camera_atual",
        "ARRI Alexa Mini LF",
    )

    proporcao = st.session_state.get(
        "video_proporcao_atual",
        "16:9",
    )

    prompt = f"""CONTINUAÇÃO DIRETA DO VÍDEO ANTERIOR

Continue a ação exatamente a partir do final do vídeo anterior.

NOVA AÇÃO:
{descricao_continuacao}

CONTINUIDADE OBRIGATÓRIA

Preserve a identidade dos personagens, rosto, cabelos, olhos, idade aparente,
roupas, acessórios, cenário, iluminação, clima, horário, objetos importantes,
estilo visual, perspectiva e direção cinematográfica.

Não reinicie a cena.
Não transforme o personagem.
Não troque a roupa sem instrução explícita.
Não mude repentinamente o cenário.

A continuação deve começar de forma natural a partir do último momento do vídeo anterior.

FOCO DA CÂMERA

Mantenha o personagem principal como foco quando ele estiver presente.
Se a câmera perder o personagem durante o movimento, faça um reenquadramento
cinematográfico natural e retorne o foco ao personagem sem alterar sua identidade.

Câmera de referência: {camera}
Proporção: {proporcao}

Continue a ação de maneira cinematográfica, natural e fisicamente plausível.
""".strip()

    try:
        operacao = cliente.models.generate_videos(
            model=MODELO_VEO,
            video=video_anterior,
            prompt=prompt,
            config=types.GenerateVideosConfig(
                number_of_videos=1,
                resolution="720p",
            ),
        )

        video_novo, erro_video = aguardar_video(cliente, operacao)
        if erro_video:
            return None, erro_video

        numero_cena = st.session_state.get("video_cenas", 1) + 1

        caminho = salvar_video(
            cliente,
            video_novo,
            f"video_cena_{numero_cena}.mp4",
        )

        if not caminho:
            return None, "❌ A continuação foi gerada, mas não pôde ser salva."

        # A nova saída já contém o vídeo anterior + a extensão.
        st.session_state.video_veo_atual = video_novo
        st.session_state.video_caminho_atual = caminho
        st.session_state.video_cenas = numero_cena
        st.session_state.video_duracao_aproximada = min(
            duracao_atual + EXTENSAO_SEGUNDOS,
            DURACAO_MAXIMA_VIDEO,
        )

        return (
            caminho,
            f"🎬 Continuação gerada! Cena {numero_cena} — "
            f"aproximadamente {st.session_state.video_duracao_aproximada} segundos no total.",
        )

    except Exception as erro:
        return None, f"❌ Erro ao continuar o vídeo: {erro}"


def resetar_video():
    """Limpa o projeto de vídeo atual."""
    chaves = [
        "video_veo_atual",
        "video_caminho_atual",
        "video_duracao_aproximada",
        "video_cenas",
        "video_camera_atual",
        "video_proporcao_atual",
        "video_descricao_atual",
    ]

    for chave in chaves:
        st.session_state.pop(chave, None)


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

    st.info(
        "🎬 O Veo 3.1 gera aproximadamente 8 segundos por geração. "
        "Depois você pode usar 'Continuar vídeo' para acrescentar cerca de 7 segundos."
    )

    return camera, proporcao, DURACAO_VIDEO


def mostrar_gerador_video():
    """Interface independente do gerador de vídeo."""
    st.subheader("🎬 Gerador de Vídeo Cinematográfico")

    camera, proporcao, duracao = mostrar_configuracao_video()

    descricao = st.text_area(
        "🎞️ Descreva o vídeo que deseja criar",
        placeholder=(
            "Exemplo: uma mulher caminhando por uma cidade futurista à noite "
            "enquanto a câmera acompanha seus passos..."
        ),
        height=150,
        key="video_descricao",
    )

    imagem_referencia = st.file_uploader(
        "🖼️ Imagem de referência do personagem ou cena",
        type=["png", "jpg", "jpeg", "webp"],
        key="video_imagem_referencia",
    )

    caminho_imagem = None

    if imagem_referencia:
        pasta = obter_pasta_videos()
        caminho_imagem = pasta / f"referencia_{imagem_referencia.name}"

        with open(caminho_imagem, "wb") as arquivo:
            arquivo.write(imagem_referencia.getbuffer())

        st.image(
            imagem_referencia,
            caption="🖼️ Referência selecionada",
            use_container_width=True,
        )

    if st.button(
        "🎬 Gerar vídeo",
        type="primary",
        key="gerar_video_ultra",
    ):
        if not descricao.strip():
            st.warning("Digite uma descrição para o vídeo.")
        else:
            with st.spinner(
                "🎬 O Veo 3.1 está criando seu vídeo cinematográfico..."
            ):
                caminho, mensagem = gerar_video(
                    descricao=descricao,
                    camera=camera,
                    proporcao=proporcao,
                    duracao=duracao,
                    imagem_referencia=caminho_imagem,
                )

            if caminho:
                st.success(mensagem)
                st.video(caminho)
                st.info("🎬 Cena 1 — aproximadamente 8 segundos.")
            else:
                st.error(mensagem)

    if "video_veo_atual" in st.session_state:
        st.divider()
        st.subheader("🔄 Continuar vídeo")

        duracao_atual = st.session_state.get(
            "video_duracao_aproximada",
            DURACAO_VIDEO,
        )

        cenas = st.session_state.get("video_cenas", 1)

        st.write(f"🎞️ Cenas/extensões: **{cenas}**")
        st.write(f"⏱️ Duração aproximada do vídeo: **{duracao_atual} segundos**")

        if duracao_atual < DURACAO_MAXIMA_VIDEO:
            descricao_continuacao = st.text_area(
                "🎞️ O que deve acontecer depois?",
                placeholder=(
                    "Exemplo: o personagem continua caminhando e entra "
                    "em uma estação subterrânea futurista..."
                ),
                height=120,
                key=f"continuacao_{cenas}",
            )

            if st.button(
                "🔄 Continuar vídeo",
                type="primary",
                key=f"continuar_video_{cenas}",
            ):
                with st.spinner("🎬 Continuando o vídeo por mais aproximadamente 7 segundos..."):
                    caminho, mensagem = continuar_video(
                        descricao_continuacao
                    )

                if caminho:
                    st.success(mensagem)
                    st.video(caminho)
                else:
                    st.error(mensagem)
        else:
            st.warning(
                "⚠️ O limite aproximado de extensão desta sequência foi alcançado."
            )

        if st.button(
            "🆕 Começar novo vídeo",
            key="novo_video_ultra",
        ):
            resetar_video()
            st.rerun()


if __name__ == "__main__":
    st.set_page_config(
        page_title="Alex IA Ultra — Vídeo",
        page_icon="🎬",
        layout="wide",
    )

    st.title("🤖 Alex IA Ultra")
    st.caption("🎬 Sistema de geração de vídeo cinematográfico")
    mostrar_gerador_video()
'''
Path('/mnt/data/video_revisado.py').write_text(video_py, encoding='utf-8')
print('OK:', Path('/mnt/data/video_revisado.py').stat().st_size, 'bytes')
