# ============================================================
# 🧪 TESTE DE IMAGEM — FLUXPOOL
# ============================================================

import os
from pathlib import Path

import streamlit as st


# ============================================================
# ⚙️ CONFIGURAÇÃO
# ============================================================

BASE_URL = "https://api.fluxpool.ai/v1"

MODELO = "flux-1.1-pro"


# ============================================================
# 🔐 API KEY
# ============================================================

def obter_api_key():

    try:
        chave = st.secrets.get(
            "FLUXPOOL_API_KEY",
            ""
        )
    except Exception:
        chave = ""

    if not chave:
        chave = os.environ.get(
            "FLUXPOOL_API_KEY",
            ""
        )

    return str(chave).strip()


# ============================================================
# 📁 PASTA
# ============================================================

def obter_pasta():

    pasta = Path(
        "/tmp/alex_ia_ultra_fluxpool"
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
            "FLUXPOOL_API_KEY não foi encontrada "
            "nos Secrets do Streamlit."
        )

    try:
        from openai import OpenAI
    except Exception as erro:
        raise RuntimeError(
            "A biblioteca openai não está instalada. "
            f"Detalhes: {erro}"
        )

    try:

        cliente = OpenAI(
            base_url=BASE_URL,
            api_key=api_key,
        )

        resposta = cliente.images.generate(
            model=MODELO,
            prompt=prompt.strip(),
            size="1024x1024",
            n=1,
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro na geração pela Fluxpool: {erro}"
        )

    # --------------------------------------------------------
    # Verificar resposta
    # --------------------------------------------------------

    if not resposta:
        raise RuntimeError(
            "A Fluxpool não retornou uma resposta."
        )

    if not resposta.data:
        raise RuntimeError(
            "A Fluxpool não retornou nenhuma imagem."
        )

    imagem_url = resposta.data[0].url

    if not imagem_url:
        raise RuntimeError(
            "A Fluxpool não retornou a URL da imagem."
        )

    # --------------------------------------------------------
    # Baixar imagem
    # --------------------------------------------------------

    try:
        import requests

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
    # Salvar
    # --------------------------------------------------------

    caminho = (
        obter_pasta()
        / "teste_fluxpool.png"
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
        "🧪 TESTE DE IMAGEM — FLUXPOOL"
    )

    st.write(
        "Teste isolado de geração de imagens."
    )

    st.info(
        f"Modelo: {MODELO}"
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
            "🎨 Fluxpool está gerando..."
        ):

            try:

                caminho = gerar_imagem(
                    prompt
                )

                st.image(
                    caminho,
                    caption=(
                        "🖼️ Fluxpool / "
                        "Flux 1.1 Pro"
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
