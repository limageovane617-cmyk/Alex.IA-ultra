import os
from pathlib import Path
import streamlit as st

MODELO_IMAGEM = "black-forest-labs/FLUX.1-schnell"

def obter_token_huggingface():
    try:
        token = st.secrets.get("HF_TOKEN", "")
    except Exception:
        token = ""
    if not token:
        token = os.environ.get("HF_TOKEN", "")
    return str(token).strip()

def obter_pasta_imagens():
    pasta = Path("/tmp/alex_ia_ultra_imagens_teste")
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta

def guardar_ultima_imagem(imagem, prompt, caminho=None, motor=None):
    st.session_state.ultima_imagem = imagem
    st.session_state.ultima_imagem_caminho = caminho
    st.session_state.ultimo_prompt_imagem = prompt
    st.session_state.ultimo_motor_imagem = motor
    return True

def gerar_imagem_teste(prompt):
    token = obter_token_huggingface()
    if not token:
        raise RuntimeError("HF_TOKEN não encontrado nos Secrets do Streamlit.")

    try:
        from huggingface_hub import InferenceClient
    except Exception as erro:
        raise RuntimeError(
            "huggingface_hub não está instalado. "
            f"Detalhes: {erro}"
        )

    cliente = InferenceClient(
        provider="auto",
        api_key=token
    )

    imagem = cliente.text_to_image(
        prompt.strip(),
        model=MODELO_IMAGEM
    )

    if imagem is None:
        raise RuntimeError("O Hugging Face não retornou uma imagem.")

    caminho = obter_pasta_imagens() / "teste_flux_schnell.png"
    imagem.save(caminho)
    return str(caminho)

def mostrar_teste():
    st.title("🧪 TESTE ISOLADO — HUGGING FACE")
    st.write("Este arquivo não altera o gerenciador_imagem.py atual.")

    prompt = st.text_input(
        "Prompt",
        "Um robô futurista em uma cidade cinematográfica à noite"
    )

    if st.button("🎨 Testar geração"):
        with st.spinner("Gerando imagem..."):
            try:
                caminho = gerar_imagem_teste(prompt)
                st.image(
                    caminho,
                    caption="FLUX.1-schnell — teste isolado",
                    use_container_width=True
                )
                st.success("✅ Imagem gerada com sucesso!")
            except Exception as erro:
                st.error(f"❌ Erro: {erro}")

if __name__ == "__main__":
    mostrar_teste()
