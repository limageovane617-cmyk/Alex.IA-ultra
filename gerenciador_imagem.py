# ============================================================
# 🖼️ ALEX IA ULTRA — GERENCIADOR DE IMAGENS
# PIXAZO — FLUX 1 SCHNELL
# Criado por Geovani
# ============================================================

import os
from pathlib import Path

import requests
import streamlit as st


# ============================================================
# ⚙️ CONFIGURAÇÃO
# ============================================================

PIXAZO_URL = (
    "https://gateway.pixazo.ai/"
    "flux-1-schnell/v1/getData"
)

MODELO_IMAGEM = "Flux 1 Schnell"
MOTOR_IMAGEM = "Pixazo / Flux 1 Schnell"


# ============================================================
# 🔐 API KEY PIXAZO
# ============================================================

def obter_api_key_pixazo():

    try:
        chave = st.secrets.get(
            "PIXAZO_API_KEY",
            ""
        )
    except Exception:
        chave = ""

    if not chave:
        chave = os.environ.get(
            "PIXAZO_API_KEY",
            ""
        )

    return str(chave).strip()


# ============================================================
# 📁 PASTA DAS IMAGENS
# ============================================================

def obter_pasta_imagens():

    pasta = Path(
        "/tmp/alex_ia_ultra_imagens"
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
    prompt,
    caminho=None,
    motor=None,
):

    try:

        st.session_state.ultima_imagem = imagem
        st.session_state.ultima_imagem_caminho = caminho
        st.session_state.ultimo_prompt_imagem = prompt
        st.session_state.ultimo_motor_imagem = motor

        return True

    except Exception:

        return False


# ============================================================
# 🎨 GERAR IMAGEM COM PIXAZO
# ============================================================

def gerar_imagem_pixazo(prompt):

    api_key = obter_api_key_pixazo()

    if not api_key:

        raise RuntimeError(
            "PIXAZO_API_KEY não foi encontrada "
            "nos Secrets do Streamlit."
        )

    # --------------------------------------------------------
    # Cabeçalhos
    # --------------------------------------------------------

    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "Ocp-Apim-Subscription-Key": api_key,
    }

    # --------------------------------------------------------
    # Dados da geração
    # --------------------------------------------------------

    dados = {
        "prompt": prompt.strip(),
        "num_steps": 4,
        "height": 1024,
        "width": 1024,
    }

    # --------------------------------------------------------
    # Enviar para Pixazo
    # --------------------------------------------------------

    try:

        resposta = requests.post(
            PIXAZO_URL,
            headers=headers,
            json=dados,
            timeout=120,
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro de conexão com a Pixazo: {erro}"
        )

    # --------------------------------------------------------
    # Verificar resposta HTTP
    # --------------------------------------------------------

    if resposta.status_code != 200:

        try:
            detalhes = resposta.json()

        except Exception:
            detalhes = resposta.text

        raise RuntimeError(
            f"Pixazo retornou HTTP "
            f"{resposta.status_code}:\n\n"
            f"{detalhes}"
        )

    # --------------------------------------------------------
    # Ler resposta
    # --------------------------------------------------------

    try:

        resultado = resposta.json()

    except Exception as erro:

        raise RuntimeError(
            f"A Pixazo não retornou JSON válido: {erro}"
        )

    # --------------------------------------------------------
    # Procurar URL da imagem
    # --------------------------------------------------------

    imagem_url = None

    if isinstance(resultado, dict):

        imagem_url = (
            resultado.get("output")
            or resultado.get("image")
            or resultado.get("image_url")
            or resultado.get("url")
        )

    elif isinstance(resultado, list):

        if resultado:

            primeiro = resultado[0]

            if isinstance(primeiro, str):

                imagem_url = primeiro

            elif isinstance(primeiro, dict):

                imagem_url = (
                    primeiro.get("output")
                    or primeiro.get("image")
                    or primeiro.get("image_url")
                    or primeiro.get("url")
                )

    # --------------------------------------------------------
    # Verificar URL
    # --------------------------------------------------------

    if not imagem_url:

        raise RuntimeError(
            "A Pixazo respondeu, mas não encontramos "
            "a URL da imagem.\n\n"
            f"Resposta recebida:\n{resultado}"
        )

    # --------------------------------------------------------
    # Baixar imagem
    # --------------------------------------------------------

    try:

        imagem = requests.get(
            imagem_url,
            timeout=120,
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro ao baixar a imagem: {erro}"
        )

    if imagem.status_code != 200:

        raise RuntimeError(
            "Não foi possível baixar a imagem. "
            f"HTTP {imagem.status_code}"
        )

    # --------------------------------------------------------
    # Salvar imagem
    # --------------------------------------------------------

    caminho = (
        obter_pasta_imagens()
        / "ultima_imagem.png"
    )

    try:

        caminho.write_bytes(
            imagem.content
        )

    except Exception as erro:

        raise RuntimeError(
            f"Não foi possível salvar a imagem: {erro}"
        )

    return str(caminho)


# ============================================================
# 🖼️ GERADOR PRINCIPAL
# ============================================================

def gerar_imagem(prompt):

    if not prompt or not prompt.strip():

        return (
            None,
            "❌ O prompt da imagem está vazio."
        )

    try:

        caminho = gerar_imagem_pixazo(
            prompt
        )

        guardar_ultima_imagem(
            imagem=caminho,
            prompt=prompt,
            caminho=caminho,
            motor=MOTOR_IMAGEM,
        )

        return (
            caminho,
            "🖼️ Imagem gerada com sucesso."
        )

    except Exception as erro:

        return (
            None,
            "❌ Erro ao gerar imagem:\n\n"
            f"{erro}"
        )


# ============================================================
# 🖼️ MOSTRAR IMAGEM
# ============================================================

def mostrar_imagem(prompt):

    with st.spinner(
        "🎨 Alex IA está criando sua imagem..."
    ):

        imagem, mensagem = gerar_imagem(
            prompt
        )

    if imagem is None:

        st.error(mensagem)

        return False

    st.image(
        imagem,
        caption=(
            "🖼️ Imagem gerada pela "
            "Alex IA Ultra"
        ),
        use_container_width=True,
    )

    motor = st.session_state.get(
        "ultimo_motor_imagem",
        "",
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
        "",
    )


def obter_motor_ultima_imagem():

    return st.session_state.get(
        "ultimo_motor_imagem",
        "",
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

        st.session_state.pop(
            chave,
            None,
        )


# ============================================================
# 🧪 TESTE DIRETO
# ============================================================

def executar_teste():

    st.title(
        "🖼️ Teste de Geração de Imagem"
    )

    st.write(
        "Teste da geração de imagens "
        "usando Pixazo / Flux 1 Schnell."
    )

    st.info(
        f"Motor: {MOTOR_IMAGEM}"
    )

    prompt = st.text_input(
        "Digite o que deseja gerar:",
        value=(
            "Um robô futurista caminhando "
            "em uma cidade cyberpunk à noite, "
            "imagem cinematográfica, "
            "muito detalhada"
        ),
    )

    if st.button(
        "🎨 Gerar imagem",
        use_container_width=True,
    ):

        if not prompt.strip():

            st.warning(
                "Digite um prompt para gerar a imagem."
            )

            return

        mostrar_imagem(prompt)


# ============================================================
# 🚀 EXECUÇÃO DO TESTE
# ============================================================

if __name__ == "__main__":

    executar_teste()
