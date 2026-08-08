# ============================================================
# 🎬 ALEX IA ULTRA — SISTEMA DE VÍDEO
# Criada por Geovani
# ============================================================

import os
import time
import tempfile
from pathlib import Path

import streamlit as st
from google.genai import types

from servicos import criar_cliente_gemini


# ============================================================
# 🎥 CONFIGURAÇÕES
# ============================================================

CAMERAS = [
    "Sony FX5",
    "Sony FX6",
    "Canon EOS C80",
    "ARRI Alexa Mini LF",
]

PROPORCOES = [
    "16:9",
    "9:16",
]

DURACAO_VIDEO = 8

MODELO_VEO = "veo-3.1-generate-preview"

EXTENSAO_SEGUNDOS = 7

DURACAO_MAXIMA_VIDEO = 148


# ============================================================
# 🎬 PROMPT CINEMATOGRÁFICO
# ============================================================

def preparar_prompt_video(
    descricao,
    camera="ARRI Alexa Mini LF",
    proporcao="16:9",
    duracao=8,
):
    """
    Cria o prompt cinematográfico enviado ao Veo.
    """

    if not descricao or not descricao.strip():
        return None

    if camera not in CAMERAS:
        camera = "ARRI Alexa Mini LF"

    if proporcao not in PROPORCOES:
        proporcao = "16:9"

    duracao = DURACAO_VIDEO

    return f"""
Crie um vídeo cinematográfico baseado na seguinte descrição:

{descricao.strip()}

DIREÇÃO CINEMATOGRÁFICA

Câmera de referência: {camera}
Proporção: {proporcao}
Duração: aproximadamente {duracao} segundos.

Use linguagem visual cinematográfica de alta qualidade.

Utilize iluminação realista, composição profissional,
profundidade de campo cinematográfica e movimentos de
câmera naturais e fisicamente plausíveis.

CONTINUIDADE VISUAL — REGRA PRIORITÁRIA

Mantenha consistência visual durante toda a cena.

Preserve:

- identidade dos personagens;
- rosto;
- cabelos;
- olhos;
- idade aparente;
- roupas;
- acessórios;
- características físicas;
- objetos importantes;
- ambiente;
- iluminação;
- clima;
- horário;
- estilo visual.

Não altere características importantes do personagem
sem instrução explícita.

Não troque a identidade do personagem.

Não transforme o personagem em outra pessoa.

Não troque roupas ou acessórios sem motivo narrativo explícito.

Evite:

- deformações;
- duplicações;
- membros extras;
- alterações bruscas de aparência;
- mudanças inexplicáveis de cenário.

FOCO NO PERSONAGEM PRINCIPAL

Quando houver um personagem principal,
mantenha-o como foco visual da cena.

A câmera pode realizar:

- travelling;
- pan;
- tilt;
- dolly;
- orbit;
- aproximação;
- afastamento;
- movimentos cinematográficos naturais.

Se o personagem sair temporariamente do enquadramento,
faça um reenquadramento natural e cinematográfico.

Volte o foco para o personagem.

Preserve sua identidade, rosto, cabelo, roupa e acessórios.

Não substitua o personagem.

MOVIMENTO

Os movimentos devem parecer naturais,
fisicamente plausíveis e cinematográficos.

Evite movimentos de câmera impossíveis,
mudanças bruscas de perspectiva e deformações.

ÁUDIO

Quando apropriado, inclua:

- áudio ambiente;
- efeitos sonoros;
- sons naturais;
- diálogos quando solicitados;
- atmosfera sonora;
- sons coerentes com o ambiente.

O resultado deve parecer uma sequência cinematográfica
profissional, coerente, realista e imersiva.
""".strip()


# ============================================================
# 📁 PASTA DOS VÍDEOS
# ============================================================

def obter_pasta_videos():
    """
    Cria uma pasta temporária para os vídeos do Alex IA Ultra.
    """

    pasta = Path(tempfile.gettempdir()) / "alex_ia_ultra"

    pasta.mkdir(
        parents=True,
        exist_ok=True
    )

    return pasta


# ============================================================
# 💾 SALVAR VÍDEO
# ============================================================

def salvar_video(
    cliente,
    video,
    nome,
):
    """
    Baixa o vídeo gerado pelo Google
    e salva como MP4.
    """

    try:

        pasta = obter_pasta_videos()

        caminho = pasta / nome

        cliente.files.download(
            file=video
        )

        video.save(
            str(caminho)
        )

        if not caminho.exists():
            return None

        if caminho.stat().st_size == 0:
            return None

        return str(caminho)

    except Exception:
        return None


# ============================================================
# ⏳ AGUARDAR GERAÇÃO
# ============================================================

def aguardar_video(
    cliente,
    operacao,
):
    """
    Aguarda o Veo terminar a geração.
    """

    while not operacao.done:

        time.sleep(10)

        operacao = cliente.operations.get(
            operacao
        )

    erro_operacao = getattr(
        operacao,
        "error",
        None
    )

    if erro_operacao:

        return (
            None,
            f"❌ Erro na geração do vídeo: "
            f"{erro_operacao}"
        )

    resposta = getattr(
        operacao,
        "response",
        None
    )

    if resposta is None:

        return (
            None,
            "❌ O Veo terminou, mas não retornou uma resposta."
        )

    videos = getattr(
        resposta,
        "generated_videos",
        None
    )

    if not videos:

        return (
            None,
            "❌ O Veo terminou, mas não retornou nenhum vídeo."
        )

    video = getattr(
        videos[0],
        "video",
        None
    )

    if video is None:

        return (
            None,
            "❌ A resposta do Veo não contém o arquivo de vídeo."
        )

    return video, None


# ============================================================
# 🎬 GERAR VÍDEO
# ============================================================

def gerar_video(
    descricao,
    camera="ARRI Alexa Mini LF",
    proporcao="16:9",
    duracao=8,
    imagem_referencia=None,
):
    """
    Gera um vídeo cinematográfico usando o Veo 3.1.
    Mantém a assinatura utilizada pelo app.py.
    """

    prompt = preparar_prompt_video(
        descricao=descricao,
        camera=camera,
        proporcao=proporcao,
        duracao=duracao,
    )

    if not prompt:

        return (
            None,
            "❌ A descrição do vídeo está vazia."
        )

    # --------------------------------------------------------
    # 🔐 Cliente Gemini
    # --------------------------------------------------------

    cliente = criar_cliente_gemini()

    if cliente is None:

        return (
            None,
            "❌ Não foi possível criar o cliente Gemini. "
            "Verifique GEMINI_API_KEY nos Secrets."
        )

    # --------------------------------------------------------
    # 🎬 Configuração
    # --------------------------------------------------------

    try:

        config = types.GenerateVideosConfig(
            number_of_videos=1,
            aspect_ratio=proporcao,
            resolution="720p",
        )

        # ----------------------------------------------------
        # 🖼️ Imagem inicial
        # ----------------------------------------------------

        if imagem_referencia:

            imagem = types.Image.from_file(
                location=str(imagem_referencia)
            )

            operacao = cliente.models.generate_videos(
                model=MODELO_VEO,
                prompt=prompt,
                image=imagem,
                config=config,
            )

        # ----------------------------------------------------
        # 🎬 Texto para vídeo
        # ----------------------------------------------------

        else:

            operacao = cliente.models.generate_videos(
                model=MODELO_VEO,
                prompt=prompt,
                config=config,
            )

        # ----------------------------------------------------
        # ⏳ Esperar
        # ----------------------------------------------------

        video, erro_video = aguardar_video(
            cliente,
            operacao
        )

        if erro_video:

            return (
                None,
                erro_video
            )

        # ----------------------------------------------------
        # 💾 Salvar
        # ----------------------------------------------------

        caminho = salvar_video(
            cliente,
            video,
            "video_inicial.mp4"
        )

        if not caminho:

            return (
                None,
                "❌ O vídeo foi gerado, "
                "mas não pôde ser salvo."
            )

        # ----------------------------------------------------
        # 🧠 Guardar estado
        # ----------------------------------------------------

        st.session_state.video_veo_atual = video

        st.session_state.video_caminho_atual = caminho

        st.session_state.video_duracao_aproximada = (
            DURACAO_VIDEO
        )

        st.session_state.video_cenas = 1

        st.session_state.video_camera_atual = camera

        st.session_state.video_proporcao_atual = proporcao

        st.session_state.video_descricao_atual = descricao

        return (
            caminho,
            "🎬 Vídeo inicial gerado com sucesso."
        )

    except Exception as erro:

        return (
            None,
            f"❌ Erro ao gerar o vídeo: {erro}"
        )


# ============================================================
# 🔄 CONTINUAR VÍDEO
# ============================================================

def continuar_video(
    descricao_continuacao
):
    """
    Estende o último vídeo Veo em aproximadamente 7 segundos.
    """

    video_anterior = st.session_state.get(
        "video_veo_atual"
    )

    if video_anterior is None:

        return (
            None,
            "❌ Ainda não existe um vídeo para continuar."
        )

    cliente = criar_cliente_gemini()

    if cliente is None:

        return (
            None,
            "❌ Não foi possível criar o cliente Gemini. "
            "Verifique GEMINI_API_KEY nos Secrets."
        )

    duracao_atual = st.session_state.get(
        "video_duracao_aproximada",
        DURACAO_VIDEO
    )

    if duracao_atual >= DURACAO_MAXIMA_VIDEO:

        return (
            None,
            "⚠️ O limite aproximado de extensão "
            "desta sequência foi alcançado."
        )

    descricao_continuacao = (
        descricao_continuacao or ""
    ).strip()

    if not descricao_continuacao:

        descricao_continuacao = (
            "Continue naturalmente a ação "
            "a partir do último momento do vídeo anterior."
        )

    camera = st.session_state.get(
        "video_camera_atual",
        "ARRI Alexa Mini LF"
    )

    proporcao = st.session_state.get(
        "video_proporcao_atual",
        "16:9"
    )

    # --------------------------------------------------------
    # 🎬 Prompt da continuação
    # --------------------------------------------------------

    prompt = f"""
CONTINUAÇÃO DIRETA DO VÍDEO ANTERIOR

Continue a ação exatamente a partir do
último momento do vídeo anterior.

NOVA AÇÃO:

{descricao_continuacao}

CONTINUIDADE OBRIGATÓRIA

Preserve:

- identidade dos personagens;
- rosto;
- cabelos;
- olhos;
- idade aparente;
- roupas;
- acessórios;
- cenário;
- iluminação;
- clima;
- horário;
- objetos importantes;
- estilo visual;
- perspectiva;
- direção cinematográfica.

Não reinicie a cena.

Não transforme o personagem.

Não troque a roupa sem instrução explícita.

Não mude repentinamente o cenário.

A continuação deve começar naturalmente
a partir do último momento do vídeo anterior.

FOCO DA CÂMERA

Mantenha o personagem principal como foco
quando ele estiver presente.

Se a câmera perder o personagem durante
o movimento, faça um reenquadramento
cinematográfico natural.

Retorne o foco ao personagem sem alterar
sua identidade.

Câmera de referência: {camera}

Proporção: {proporcao}

Continue a ação de maneira cinematográfica,
natural, coerente e fisicamente plausível.
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

        # ----------------------------------------------------
        # ⏳ Esperar
        # ----------------------------------------------------

        video_novo, erro_video = aguardar_video(
            cliente,
            operacao
        )

        if erro_video:

            return (
                None,
                erro_video
            )

        # ----------------------------------------------------
        # 🔢 Número da cena
        # ----------------------------------------------------

        numero_cena = (
            st.session_state.get(
                "video_cenas",
                1
            ) + 1
        )

        # ----------------------------------------------------
        # 💾 Salvar
        # ----------------------------------------------------

        caminho = salvar_video(
            cliente,
            video_novo,
            f"video_cena_{numero_cena}.mp4"
        )

        if not caminho:

            return (
                None,
                "❌ A continuação foi gerada, "
                "mas não pôde ser salva."
            )

        # ----------------------------------------------------
        # 🧠 Atualizar estado
        # ----------------------------------------------------

        st.session_state.video_veo_atual = (
            video_novo
        )

        st.session_state.video_caminho_atual = (
            caminho
        )

        st.session_state.video_cenas = (
            numero_cena
        )

        st.session_state.video_duracao_aproximada = min(
            duracao_atual + EXTENSAO_SEGUNDOS,
            DURACAO_MAXIMA_VIDEO,
        )

        return (
            caminho,
            f"🎬 Continuação gerada! "
            f"Cena {numero_cena} — aproximadamente "
            f"{st.session_state.video_duracao_aproximada} "
            f"segundos no total."
        )

    except Exception as erro:

        return (
            None,
            f"❌ Erro ao continuar o vídeo: {erro}"
        )


# ============================================================
# 🧹 RESETAR PROJETO DE VÍDEO
# ============================================================

def resetar_video():
    """
    Limpa o projeto de vídeo atual.
    """

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

        st.session_state.pop(
            chave,
            None
        )


# ============================================================
# ⚙️ CONFIGURAÇÃO DO VÍDEO
# ============================================================

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
        "🎬 O Veo 3.1 gera vídeos de aproximadamente "
        "8 segundos. Depois você pode usar "
        "'Continuar vídeo' para acrescentar "
        "aproximadamente 7 segundos."
    )

    return (
        camera,
        proporcao,
        DURACAO_VIDEO
    )


# ============================================================
# 🎬 GERADOR INDEPENDENTE
# ============================================================

def mostrar_gerador_video():

    st.subheader(
        "🎬 Gerador de Vídeo Cinematográfico"
    )

    camera, proporcao, duracao = (
        mostrar_configuracao_video()
    )

    descricao = st.text_area(
        "🎞️ Descreva o vídeo que deseja criar",
        placeholder=(
            "Exemplo: uma mulher caminhando por "
            "uma cidade futurista à noite enquanto "
            "a câmera acompanha seus passos..."
        ),
        height=150,
        key="video_descricao",
    )

    imagem_referencia = st.file_uploader(
        "🖼️ Imagem de referência do personagem ou cena",
        type=[
            "png",
            "jpg",
            "jpeg",
            "webp"
        ],
        key="video_imagem_referencia",
    )

    caminho_imagem = None

    if imagem_referencia:

        pasta = obter_pasta_videos()

        caminho_imagem = (
            pasta /
            f"referencia_{imagem_referencia.name}"
        )

        with open(
            caminho_imagem,
            "wb"
        ) as arquivo:

            arquivo.write(
                imagem_referencia.getbuffer()
            )

        st.image(
            imagem_referencia,
            caption="🖼️ Referência selecionada",
            use_container_width=True,
        )

    # ========================================================
    # 🎬 GERAR
    # ========================================================

    if st.button(
        "🎬 Gerar vídeo",
        type="primary",
        key="gerar_video_ultra",
    ):

        if not descricao.strip():

            st.warning(
                "Digite uma descrição para o vídeo."
            )

        else:

            with st.spinner(
                "🎬 O Veo 3.1 está criando "
                "seu vídeo cinematográfico..."
            ):

                caminho, mensagem = gerar_video(
                    descricao=descricao,
                    camera=camera,
                    proporcao=proporcao,
                    duracao=duracao,
                    imagem_referencia=caminho_imagem,
                )

            if caminho:

                st.success(
                    mensagem
                )

                st.video(
                    caminho
                )

                st.info(
                    "🎬 Cena 1 — aproximadamente "
                    "8 segundos."
                )

            else:

                st.error(
                    mensagem
                )

    # ========================================================
    # 🔄 CONTINUAR
    # ========================================================

    if "video_veo_atual" in st.session_state:

        st.divider()

        st.subheader(
            "🔄 Continuar vídeo"
        )

        duracao_atual = st.session_state.get(
            "video_duracao_aproximada",
            DURACAO_VIDEO
        )

        cenas = st.session_state.get(
            "video_cenas",
            1
        )

        st.write(
            f"🎞️ Cenas/extensões: **{cenas}**"
        )

        st.write(
            f"⏱️ Duração aproximada: "
            f"**{duracao_atual} segundos**"
        )

        if duracao_atual < DURACAO_MAXIMA_VIDEO:

            descricao_continuacao = st.text_area(
                "🎞️ O que deve acontecer depois?",
                placeholder=(
                    "Exemplo: o personagem continua "
                    "caminhando e entra em uma estação "
                    "subterrânea futurista..."
                ),
                height=120,
                key=f"continuacao_{cenas}",
            )

            if st.button(
                "🔄 Continuar vídeo",
                type="primary",
                key=f"continuar_video_{cenas}",
            ):

                with st.spinner(
                    "🎬 Continuando o vídeo por "
                    "mais aproximadamente 7 segundos..."
                ):

                    caminho, mensagem = (
                        continuar_video(
                            descricao_continuacao
                        )
               
