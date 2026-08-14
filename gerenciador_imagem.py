# ============================================================
# 🧪 TESTE NVIDIA — ALEX IA ULTRA
# NÃO GERA IMAGEM AINDA
# Criado por Geovani
# ============================================================

import os
import requests
import streamlit as st


# ============================================================
# ⚙️ ENDPOINTS OFICIAIS NVIDIA
# ============================================================

NVIDIA_BASE_URL = "https://ai.api.nvidia.com"

ENDPOINT_INFER = (
    "https://ai.api.nvidia.com/v1/genai/"
    "black-forest-labs/flux.1-dev"
)

ENDPOINT_IMAGES = (
    "https://ai.api.nvidia.com/v1/images/generations"
)


# ============================================================
# 🔐 PEGAR CHAVE
# ============================================================

def obter_chave_nvidia():

    try:

        chave = st.secrets.get(
            "NVIDIA_API_KEY",
            ""
        )

        if chave:

            return str(chave).strip()

    except Exception as erro:

        st.warning(
            f"⚠️ Erro ao ler Secrets: {erro}"
        )

    chave = os.environ.get(
        "NVIDIA_API_KEY",
        ""
    )

    return str(chave).strip()


# ============================================================
# 🧪 TESTAR ENDPOINT
# ============================================================

def testar_endpoint(
    nome,
    url,
    chave
):

    st.subheader(
        f"🌐 Testando: {nome}"
    )

    st.code(
        url
    )

    try:

        resposta = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {chave}",
                "Accept": "application/json",
            },
            timeout=30,
        )

        st.write(
            f"HTTP: `{resposta.status_code}`"
        )

        st.write(
            "Resposta:"
        )

        try:

            st.json(
                resposta.json()
            )

        except Exception:

            st.code(
                resposta.text[:3000]
            )

        return resposta.status_code

    except Exception as erro:

        st.error(
            f"❌ Erro de conexão: {erro}"
        )

        return None


# ============================================================
# 🧪 MOSTRAR IMAGEM
# ============================================================

def mostrar_imagem(prompt):

    st.title(
        "🧪 TESTE NVIDIA"
    )

    st.warning(
        "⚠️ Este é apenas um teste de conexão. "
        "Nenhuma imagem será gerada."
    )

    chave = obter_chave_nvidia()

    # --------------------------------------------------------
    # Verificar chave
    # --------------------------------------------------------

    if not chave:

        st.error(
            "❌ NVIDIA_API_KEY NÃO FOI ENCONTRADA."
        )

        st.info(
            "A chave precisa estar nos Secrets "
            "do Streamlit com o nome NVIDIA_API_KEY."
        )

        return False

    st.success(
        "✅ NVIDIA_API_KEY foi encontrada."
    )

    # NÃO mostrar a chave na tela.

    st.write(
        f"🔑 Chave encontrada: "
        f"`{chave[:6]}...{chave[-4:]}`"
    )

    # --------------------------------------------------------
    # Teste 1 — endpoint principal
    # --------------------------------------------------------

    status_infer = testar_endpoint(
        "FLUX.1-dev / endpoint NIM",
        ENDPOINT_INFER,
        chave
    )

    # --------------------------------------------------------
    # Teste 2 — endpoint OpenAI-compatible
    # --------------------------------------------------------

    status_images = testar_endpoint(
        "FLUX.1-dev / OpenAI Images",
        ENDPOINT_IMAGES,
        chave
    )

    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "📊 RESULTADO DO TESTE"
    )

    st.write(
        f"Endpoint NIM: `{status_infer}`"
    )

    st.write(
        f"Endpoint Images: `{status_images}`"
    )

    if (
        status_infer == 200
        or status_images == 200
    ):

        st.success(
            "🎉 A NVIDIA respondeu! "
            "Temos um endpoint funcionando."
        )

        st.info(
            "Agora podemos montar o gerador "
            "usando exatamente o endpoint que respondeu."
        )

    elif (
        status_infer == 401
        or status_images == 401
    ):

        st.error(
            "🔐 A NVIDIA recusou a autenticação. "
            "Nesse caso o problema é a autorização/chave."
        )

    elif (
        status_infer == 404
        and status_images == 404
    ):

        st.error(
            "🌐 Os dois endpoints retornaram 404."
        )

        st.warning(
            "Isso indica que precisamos verificar "
            "qual endpoint público está associado "
            "à sua chave NVIDIA/API Catalog."
        )

    else:

        st.warning(
            "⚠️ A NVIDIA respondeu, mas precisamos "
            "analisar os códigos acima."
        )

    return False


# ============================================================
# 🔧 FUNÇÕES COMPATÍVEIS COM O APP
# ============================================================

def gerar_imagem(prompt):

    return (
        None,
        "🧪 Teste NVIDIA ativo. "
        "Nenhuma imagem foi gerada."
    )


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


def obter_motor_ultima_imagem():

    return st.session_state.get(
        "ultimo_motor_imagem",
        ""
    )


def limpar_ultima_imagem():

    for chave in [
        "ultima_imagem",
        "ultima_imagem_caminho",
        "ultimo_prompt_imagem",
        "ultimo_motor_imagem",
    ]:

        st.session_state.pop(
            chave,
            None
    )
