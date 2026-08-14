import os
from pathlib import Path

import requests
import streamlit as st


# ============================================================
# 🖼️ TESTE PIXAZO — FLUX SCHNELL
# ============================================================

PIXAZO_URL = (
    "https://gateway.pixazo.ai/"
    "flux-1-schnell/v1/getDataBatch"
)

MODELO = "Flux 1 Schnell"


# ============================================================
# 🔐 API KEY
# ============================================================

def obter_api_key():

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
# 📁 PASTA
# ============================================================

def obter_pasta():

    pasta = Path(
        "/tmp/alex_ia_ultra_pixazo"
    )

    pasta.mkdir(
        parents=True,
        exist_ok=True
    )

    return pasta


# ============================================================
# 🎨 GERAR IMAGEM
# ============================================================

def gerar_imagem(prompt):

    api_key = obter_api_key()

    if not api_key:

        raise RuntimeError(
            "PIXAZO_API_KEY não foi encontrada "
            "nos Secrets do Streamlit."
        )

    headers = {
        "Content-Type": "application/json",
        "X-Secret-Key": api_key,
        "Cache-Control": "no-cache",
    }

    dados = {
        "prompt": prompt.strip(),
        "num_steps": 4,
        "height": 1024,
        "width": 1024,
    }

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

    try:

        resultado = resposta.json()

    except Exception as erro:

        raise RuntimeError(
            f"A Pixazo não retornou JSON válido: {erro}"
        )

    # --------------------------------------------------------
    # URL da imagem
    # --------------------------------------------------------

    imagem_url = resultado.get(
        "output"
    )

    if not imagem_url:

        raise RuntimeError(
            "A Pixazo respondeu, mas não "
            "encontramos o endereço da imagem.\n\n"
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
            "A Pixazo gerou a resposta, "
            "mas não foi possível baixar "
            f"a imagem. HTTP {imagem.status_code}"
        )

    # --------------------------------------------------------
    # Salvar
    # --------------------------------------------------------

    caminho = (
        obter_pasta()
        / "teste_pixazo_flux.png"
    )

    try:

        caminho.write_bytes(
            imagem.content
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro ao salvar a imagem: {erro}"
        )

    return str(caminho)


# ============================================================
# 🧪 INTERFACE
# ============================================================

def mostrar_teste():

    st.title(
        "🧪 TESTE DE IMAGEM — PIXAZO"
    )

    st.write(
        "Teste isolado usando o Flux 1 Schnell."
    )

    st.info(
        "Modelo: Flux 1 Schnell"
    )

    prompt = st.text_area(
        "Digite o que você quer criar:",
        value=(
            "Um robô futurista caminhando "
            "em uma cidade cyberpunk à noite, "
            "cinematográfico, extremamente detalhado, "
            "iluminação profissional."
        ),
        height=130,
    )

    if st.button(
        "🎨 GERAR IMAGEM",
        use_container_width=True,
    ):

        if not prompt.strip():

            st.warning(
                "Digite uma descrição para a imagem."
            )

            return

        with st.spinner(
            "🎨 Pixazo está criando sua imagem..."
        ):

            try:

                caminho = gerar_imagem(
                    prompt
                )

                st.image(
                    caminho,
                    caption=(
                        "🖼️ Flux 1 Schnell — Pixazo"
                    ),
                    use_container_width=True,
                )

                st.success(
                    "✅ Imagem gerada com sucesso!"
                )

            except Exception as erro:

                st.error(
                    f"❌ Erro ao gerar imagem:\n\n{erro}"
                )


# ============================================================
# 🚀 EXECUTAR
# ============================================================

if __name__ == "__main__":

    mostrar_teste()
