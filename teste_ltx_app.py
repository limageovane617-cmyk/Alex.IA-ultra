import streamlit as st
from gradio_client import Client

st.set_page_config(
    page_title="Teste LTX-2.3",
    page_icon="🎬"
)

st.title("🎬 Teste LTX-2.3")
st.write("Este aplicativo testa a conexão com a Space oficial do LTX-2.3.")

prompt = st.text_area(
    "Descrição do vídeo",
    "Uma bola vermelha rolando lentamente sobre uma mesa de madeira, iluminação cinematográfica, movimento suave de câmera."
)

if st.button("🎬 Gerar vídeo de teste"):

    with st.spinner("Conectando ao LTX-2.3..."):

        try:
            client = Client(
                "https://lightricks-ltx-2-3.hf.space"
            )

            st.success("✅ Conectado ao LTX-2.3!")

            with st.spinner("🎥 Gerando vídeo..."):

                resultado = client.predict(
                    input_image=None,
                    prompt=prompt,
                    duration=1.0,
                    enhance_prompt=True,
                    seed=0,
                    randomize_seed=True,
                    height=512,
                    width=512,
                    api_name="/generate_video"
                )

            st.success("🎉 O LTX-2.3 respondeu!")

            st.write("Resultado recebido:")

            st.write(resultado)

        except Exception as erro:

            st.error("❌ Ocorreu um erro")

            st.code(
                str(erro)
            )
