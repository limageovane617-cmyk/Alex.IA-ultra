# ============================================================
# 🧪 TESTE DE IMAGEM — STABLE DIFFUSION API
# ============================================================

import os
from pathlib import Path

import requests
import streamlit as st


# ============================================================
# ⚙️ CONFIGURAÇÃO
# ============================================================

API_URL = (
    "https://stablediffusionapi.com/api/v3/text2img"
)

MODELO = "Stable Diffusion"


# ============================================================
# 🔐 API KEY
# ============================================================

def obter_api_key():

    try:
        chave = st.secrets.get(
            "STABLE_DIFFUSION_API_KEY",
            ""
        )
    except Exception:
        chave = ""

    if not chave:
        chave = os.environ.get(
            "STABLE_DIFFUSION_API_KEY",
            ""
        )

    return str(chave).strip()


# ============================================================
# 📁 PASTA
# ============================================================

def obter_pasta():

    pasta = Path(
        "/tmp/alex_ia_ultra_stable_diffusion"
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
            "STABLE_DIFFUSION_API_KEY "
            "não foi encontrada nos "
            "Secrets do Streamlit."
        )

    dados = {
        "key": api_key,
        "prompt": prompt.strip(),
        "negative_prompt": (
            "blurry, low quality, distorted, "
            "bad anatomy, extra limbs"
        ),
        "width": "512",
        "height": "512",
        "samples": "1",
        "num_inference_steps": "20",
        "guidance_scale": 7.5,
        "enhance_prompt": "yes",
        "safety_checker": "yes",
        "seed": None,
        "webhook": None,
        "track_id": None,
    }

    try:

        resposta = requests.post(
            API_URL,
            json=dados,
            headers={
                "Content-Type": "application/json"
            },
            timeout=180,
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro de conexão com a API: {erro}"
        )

    # --------------------------------------------------------
    # VERIFICAR HTTP
    # --------------------------------------------------------

    if resposta.status_code != 200:

        try:
            detalhes = resposta.json()
        except Exception:
            detalhes = resposta.text

        raise RuntimeError(
            f"API retornou HTTP "
            f"{resposta.status_code}:\n\n"
            f"{detalhes}"
        )

    # --------------------------------------------------------
    # LER JSON
    # --------------------------------------------------------

    try:

        resultado = resposta.json()

    except Exception as erro:

        raise RuntimeError(
            f"Resposta inválida da API: {erro}"
        )

    # --------------------------------------------------------
    # VERIFICAR STATUS
    # --------------------------------------------------------

    if resultado.get("status") != "success":

        raise RuntimeError(
            "A API não informou sucesso.\n\n"
            f"Resposta:\n{resultado}"
        )

    # --------------------------------------------------------
    # PEGAR URL DA IMAGEM
    # --------------------------------------------------------

    imagens = resultado.get(
        "output",
        []
    )

    if not imagens:

        # Algumas gerações podem entrar
        # em fila de processamento.
        fetch_result = resultado.get(
            "fetch_result"
        )

        if fetch_result:

            raise RuntimeError(
                "A imagem entrou em processamento "
                "assíncrono.\n\n"
                f"fetch_result:\n{fetch_result}"
            )

        raise RuntimeError(
            "A API respondeu com sucesso, "
            "mas não retornou nenhuma imagem.\n\n"
            f"Resposta:\n{resultado}"
        )

    imagem_url = imagens[0]

    # --------------------------------------------------------
    # BAIXAR IMAGEM
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
            "Não foi possível baixar "
            f"a imagem. HTTP {imagem.status_code}"
        )

    # --------------------------------------------------------
    # SALVAR
    # --------------------------------------------------------

    caminho = (
        obter_pasta()
        / "teste_stable_diffusion.png"
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
        "🧪 TESTE DE IMAGEM — "
        "STABLE DIFFUSION"
    )

    st.write(
        "Teste isolado de geração de imagens."
    )

    st.info(
        "Motor: Stable Diffusion API"
    )

    prompt = st.text_area(
        "Digite o que você quer criar:",
        value=(
            "Um robô futurista caminhando "
            "em uma cidade cyberpunk à noite, "
            "cinematográfico, extremamente "
            "detalhado, iluminação profissional."
        ),
        height=140,
    )

    if st.button(
        "🎨 GERAR IMAGEM",
        use_container_width=True,
    ):

        if not prompt.strip():

            st.warning(
                "Digite uma descrição "
                "para a imagem."
            )

            return

        with st.spinner(
            "🎨 Gerando imagem..."
        ):

            try:

                caminho = gerar_imagem(
                    prompt
                )

                st.image(
                    caminho,
                    caption=(
                        "🖼️ Stable Diffusion"
                    ),
                    use_container_width=True,
                )

                st.success(
                    "✅ Imagem gerada com sucesso!"
                )

            except Exception as erro:

                st.error(
                    "❌ Erro ao gerar imagem:"
                )

                st.code(
                    str(erro)
                )


# ============================================================
# 🚀 EXECUTAR
# ============================================================

if __name__ == "__main__":

    mostrar_teste()
