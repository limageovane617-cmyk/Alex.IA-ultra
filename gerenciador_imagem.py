# ============================================================
# 🖼️ ALEX IA ULTRA — TESTE DE GERAÇÃO DE IMAGENS
# HUGGING FACE INFERENCE PROVIDERS
# Criado por Geovani
# ============================================================

import os
from pathlib import Path

import streamlit as st


# ============================================================
# ⚙️ CONFIGURAÇÃO
# ============================================================

MODELO_IMAGEM = "black-forest-labs/FLUX.1-schnell"
PROVEDOR = "auto"


# ============================================================
# 🔐 TOKEN HUGGING FACE
# ============================================================

def obter_token_huggingface():
    try:
        token = st.secrets.get("HF_TOKEN", "")
    except Exception:
        token = ""

    if not token:
        token = os.environ.get("HF_TOKEN", "")

    return str(token).strip()


# ============================================================
# 📁 PASTA DAS IMAGENS
# ============================================================

def obter_pasta_imagens():
    pasta = Path("/tmp/alex_ia_ultra_imagens")
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


# ============================================================
# 💾 GUARDAR ÚLTIMA IMAGEM
# ============================================================

def guardar_ultima_imagem(imagem, prompt, caminho=None, motor=None):
    try:
        st.session_state.ultima_imagem = imagem
        st.session_state.ultima_imagem_caminho = caminho
        st.session_state.ultimo_prompt_imagem = prompt
        st.session_state.ultimo_motor_imagem = motor
        return True

    except Exception:
        return False


# ============================================================
# 🎨 GERAR IMAGEM COM HUGGING FACE
# ============================================================

def gerar_imagem_huggingface(prompt):

    token = obter_token_huggingface()

    if not token:
        raise RuntimeError(
            "HF_TOKEN não foi encontrado nos Secrets do Streamlit."
        )

    # --------------------------------------------------------
    # Importar Hugging Face
    # --------------------------------------------------------

    try:
        from huggingface_hub import InferenceClient

    except Exception:
        raise RuntimeError(
            "A biblioteca huggingface_hub não está instalada. "
            "Adicione huggingface_hub ao requirements.txt."
        )

    # --------------------------------------------------------
    # Criar cliente
    # --------------------------------------------------------

    try:
        cliente = InferenceClient(
            provider=PROVEDOR,
            api_key=token,
        )

    except Exception as erro:
        raise RuntimeError(
            f"Não foi possível iniciar o Hugging Face: {erro}"
        )

    # --------------------------------------------------------
    # Gerar imagem
    # --------------------------------------------------------

    try:
        imagem = cliente.text_to_image(
            prompt.strip(),
            model=MODELO_IMAGEM,
        )

    except Exception as erro:
        raise RuntimeError(
            f"Erro na geração de imagem pelo Hugging Face: {erro}"
        )

    # --------------------------------------------------------
    # Verificar retorno
    # --------------------------------------------------------

    if imagem is None:
        raise RuntimeError(
            "O Hugging Face não retornou uma imagem."
        )

    # --------------------------------------------------------
    # Salvar imagem
    # --------------------------------------------------------

    caminho = obter_pasta_imagens() / "ultima_imagem.png"

    try:
        imagem.save(caminho)

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
        return None, "❌ O prompt da imagem está vazio."

    try:

        caminho = gerar_imagem_huggingface(prompt)

        guardar_ultima_imagem(
            imagem=caminho,
            prompt=prompt,
            caminho=caminho,
            motor=f"Hugging Face / {MODELO_IMAGEM}",
        )

        return caminho, "🖼️ Imagem gerada com sucesso."

    except Exception as erro:

        return None, (
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

    st.title("🖼️ Teste de Geração de Imagem")

    st.write(
        "Este arquivo testa somente a geração "
        "de imagens pelo Hugging Face."
    )

    st.info(
        f"Modelo: {MODELO_IMAGEM}"
    )

    prompt = st.text_input(
        "Digite o que deseja gerar:",
        value=(
            "Um robô futurista caminhando "
            "em uma cidade cyberpunk à noite, "
            "imagem cinematográfica, muito detalhada"
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
