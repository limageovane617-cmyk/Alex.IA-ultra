# ============================================================
# 🖼️ ALEX IA ULTRA — GERENCIADOR DE IMAGENS
# Criada por Geovani
# ============================================================

import base64
import os
from pathlib import Path

import streamlit as st

from servicos import criar_cliente_gemini


# ============================================================
# 🎨 MOTORES DE IMAGEM
# ============================================================

MOTORES_IMAGEM = [
    "gemini-3.1-flash-image",
    "gemini-3-pro-image",
]


# ============================================================
# 📁 PASTA DAS IMAGENS
# ============================================================

def obter_pasta_imagens():

    pasta = Path(
        os.path.join(
            os.getcwd(),
            "imagens_geradas"
        )
    )

    pasta.mkdir(
        parents=True,
        exist_ok=True
    )

    return pasta


# ============================================================
# 💾 GUARDAR ÚLTIMA IMAGEM
# ============================================================

def guardar_ultima_imagem(
    imagem,
    prompt
):

    try:

        caminho = None

        if isinstance(imagem, str):

            caminho = imagem

        elif hasattr(imagem, "path"):

            caminho = imagem.path

        elif hasattr(imagem, "filename"):

            caminho = imagem.filename

        st.session_state.ultima_imagem = imagem

        st.session_state.ultima_imagem_caminho = caminho

        st.session_state.ultimo_prompt_imagem = prompt

        return True

    except Exception:

        st.session_state.ultima_imagem = imagem

        st.session_state.ultima_imagem_caminho = None

        st.session_state.ultimo_prompt_imagem = prompt

        return False


# ============================================================
# 🔍 OBTER DADOS DA IMAGEM
# ============================================================

def extrair_imagem_resposta(resposta):

    """
    Procura uma imagem na resposta do Gemini.
    """

    try:

        candidatos = []

        if hasattr(resposta, "candidates"):

            candidatos = resposta.candidates

        for candidato in candidatos:

            content = getattr(
                candidato,
                "content",
                None
            )

            if content is None:
                continue

            partes = getattr(
                content,
                "parts",
                []
            )

            for parte in partes:

                inline_data = getattr(
                    parte,
                    "inline_data",
                    None
                )

                if inline_data:

                    dados = getattr(
                        inline_data,
                        "data",
                        None
                    )

                    mime_type = getattr(
                        inline_data,
                        "mime_type",
                        "image/png"
                    )

                    if dados:

                        return (
                            dados,
                            mime_type
                        )

        return (
            None,
            None
        )

    except Exception:

        return (
            None,
            None
        )


# ============================================================
# 💾 SALVAR BYTES DA IMAGEM
# ============================================================

def salvar_imagem_bytes(
    dados,
    mime_type="image/png"
):

    try:

        pasta = obter_pasta_imagens()

        extensao = ".png"

        if "jpeg" in mime_type:

            extensao = ".jpg"

        elif "webp" in mime_type:

            extensao = ".webp"

        nome = (
            "alex_ia_imagem_"
            + str(
                len(
                    list(
                        pasta.glob("*")
                    )
                ) + 1
            )
            + extensao
        )

        caminho = pasta / nome

        if isinstance(
            dados,
            str
        ):

            dados = base64.b64decode(
                dados
            )

        with open(
            caminho,
            "wb"
        ) as arquivo:

            arquivo.write(
                dados
            )

        if not caminho.exists():

            return None

        if caminho.stat().st_size == 0:

            return None

        return str(caminho)

    except Exception:

        return None


# ============================================================
# 🖼️ GERAR COM GEMINI
# ============================================================

def gerar_com_gemini(
    cliente,
    modelo,
    prompt
):

    resposta = cliente.models.generate_content(
        model=modelo,
        contents=prompt,
    )

    dados, mime_type = (
        extrair_imagem_resposta(
            resposta
        )
    )

    if dados is None:

        raise RuntimeError(
            "O modelo terminou, "
            "mas não retornou uma imagem."
        )

    caminho = salvar_imagem_bytes(
        dados,
        mime_type
    )

    if caminho is None:

        raise RuntimeError(
            "A imagem foi recebida, "
            "mas não pôde ser salva."
        )

    return caminho


# ============================================================
# 🖼️ GERAR IMAGEM COM FALLBACK
# ============================================================

def gerar_imagem(prompt):

    if not prompt or not prompt.strip():

        return (
            None,
            "❌ O prompt da imagem está vazio."
        )

    cliente = criar_cliente_gemini()

    if cliente is None:

        return (
            None,
            "❌ Não foi possível criar o cliente Gemini. "
            "Verifique GEMINI_API_KEY nos Secrets."
        )

    erros = []

    # ========================================================
    # 🔄 TENTA OS MOTORES EM ORDEM
    # ========================================================

    for modelo in MOTORES_IMAGEM:

        try:

            st.session_state.motor_imagem_atual = (
                modelo
            )

            caminho = gerar_com_gemini(
                cliente,
                modelo,
                prompt.strip()
            )

            if caminho:

                return (
                    caminho,
                    f"Imagem gerada usando {modelo}."
                )

        except Exception as erro:

            mensagem_erro = str(
                erro
            )

            erros.append(
                f"{modelo}: {mensagem_erro}"
            )

            # Continua automaticamente
            # para o próximo motor.
            continue

    # ========================================================
    # ❌ TODOS FALHARAM
    # ========================================================

    detalhes = "\n\n".join(
        erros
    )

    return (
        None,
        "❌ Todos os motores de imagem "
        "disponíveis falharam.\n\n"
        + detalhes
    )


# ============================================================
# 🖼️ MOSTRAR IMAGEM
# ============================================================

def mostrar_imagem(prompt):

    with st.spinner(
        "🎨 Alex IA está criando sua imagem..."
    ):

        caminho, mensagem = (
            gerar_imagem(
                prompt
            )
        )

    if caminho is None:

        st.error(
            mensagem
        )

        return False

    # --------------------------------------------------------
    # 🧠 Guarda a última imagem
    # --------------------------------------------------------

    guardar_ultima_imagem(
        caminho,
        prompt
    )

    # --------------------------------------------------------
    # 🖼️ Mostra a imagem
    # --------------------------------------------------------

    st.image(
        caminho,
        caption=(
            "🖼️ Imagem gerada pela Alex IA Ultra"
        ),
        use_container_width=True
    )

    st.caption(
        f"🎨 {mensagem}"
    )

    # --------------------------------------------------------
    # ⬇️ Download
    # --------------------------------------------------------

    try:

        with open(
            caminho,
            "rb"
        ) as arquivo:

            st.download_button(
                "⬇️ Baixar imagem",
                data=arquivo.read(),
                file_name="alex_ia_imagem.png",
                mime="image/png",
                key=(
                    "download_imagem_"
                    + str(
                        hash(caminho)
                    )
                )
            )

    except Exception:

        pass

    return True
