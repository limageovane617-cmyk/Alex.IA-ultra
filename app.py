import streamlit as st
from openai import OpenAI
import PyPDF2
import time

st.set_page_config(
    page_title="🤖 Alex IA Ultra",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Alex IA Ultra")
st.caption("Sua inteligência artificial avançada criada por Geovani")

api_key = st.text_input(
    "Digite sua chave do OpenRouter:",
    type="password",
    placeholder="sk-or-v1-..."
)

if api_key:
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        # Inicializar estado da sessão
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {
                    "role": "system",
                    "content": "Você é um Alex IA Ultra, uma inteligência artificial avançada criada por Geovani. Responda sempre em português de forma inteligente."
                }
            ]

        if "file_text" not in st.session_state:
            st.session_state.file_text = ""

        if "images" not in st.session_state:
            st.session_state.images = []

        # ========== SIDEBAR ==========
        st.sidebar.title("📄 Arquivos")

        # Upload de arquivos
        uploaded_file = st.sidebar.file_uploader(
            "Envie um arquivo (PDF ou TXT)",
            type=["txt", "pdf"],
            help="Aceita arquivos de texto e PDF"
        )

        if uploaded_file is not None:
            try:
                file_type = uploaded_file.type

                if file_type == "text/plain":
                    content = uploaded_file.read().decode("utf-8")
                    st.session_state.file_text = content
                    st.sidebar.success("✅ Arquivo TXT carregado!")

                elif file_type == "application/pdf":
                    reader = PyPDF2.PdfReader(uploaded_file)
                    text = ""
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += extracted + "\n"
                    st.session_state.file_text = text.strip()
                    st.sidebar.success("✅ PDF carregado com sucesso!")

                else:
                    st.sidebar.warning("Formato não suportado. Use TXT ou PDF.")

            except Exception as file_error:
                st.sidebar.error(f"Erro ao ler arquivo: {str(file_error)}")
                st.session_state.file_text = ""

        # Botão limpar
        if st.sidebar.button("🗑️ Limpar conversa", use_container_width=True):
            st.session_state.messages = [
                {
                    "role": "system",
                    "content": "Você é um Alex IA Ultra, uma inteligência artificial avançada criada por Geovani. Responda sempre em português de forma inteligente."
                }
            ]
            st.session_state.file_text = ""
            st.rerun()

        # ========== GERADOR DE IMAGENS ==========
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🎨 Gerador de Imagens")

        image_prompt = st.sidebar.text_area(
            "Descreva a imagem:",
            placeholder="Ex: Um gato astronauta voando em Marte ao pôr do sol, estilo cyberpunk...",
            height=100,
            help="Quanto mais detalhado, melhor o resultado"
        )

        # Opções de imagem
        col1, col2 = st.sidebar.columns(2)

        with col1:
            image_size = st.selectbox(
                "Tamanho:",
                ["1024x1024", "1792x1024", "1024x1792"],
                index=0,
                help="1792x1024 para paisagem, 1024x1792 para retrato"
            )

        with col2:
            image_quality = st.selectbox(
                "Qualidade:",
                ["standard", "hd"],
                index=0,
                help="HD tem mais detalhes mas custa mais tokens"
            )

        # Botão gerar com validação
        if st.sidebar.button("🎨 Gerar Imagem", type="primary", use_container_width=True):
            # Validação prévia
            if not image_prompt.strip():
                st.sidebar.error("⚠️ Por favor, descreva o que deseja!")
                st.stop()

            if len(image_prompt) < 10:
                st.sidebar.warning("⚠️ Descreva um pouco mais para melhor resultado")

            # Verificar se API key é válida (básico)
            if not api_key.startswith("sk-"):
                st.sidebar.error("⚠️ Chave de API inválida!")
                st.stop()

            # Gerar imagem
            with st.spinner("🎨 Gerando imagem... Isso pode levar alguns segundos."):
                try:
                    response = client.images.generate(
                        model="dall-e-3",  # Modelo padrão, ajuste se necessário no OpenRouter
                        prompt=image_prompt,
                        size=image_size,
                        quality=image_quality,
                        n=1,
                        response_format="url"
                    )

                    # Extrair URL da imagem
                    image_url = response.data[0].url

                    # Exibir imagem
                    st.image(image_url, caption="Imagem Gerada", use_column_width=True)

                    # Salvar no histórico
                    st.session_state.images.append({
                        "prompt": image_prompt,
                        "url": image_url,
                        "timestamp": time.strftime("%H:%M:%S")
                    })

                    st.sidebar.success("✅ Imagem gerada com sucesso!")

                    # Botão para baixar (se disponível)
                    try:
                        import requests
                        img_data = requests.get(image_url).content
                        st.sidebar.download_button(
                            label="📥 Baixar Imagem",
                            data=img_data,
                            file_name=f"alex_ia_{int(time.time())}.png",
                            mime="image/png",
                            use_container_width=True
                        )
                    except:
                        pass  # Se não conseguir baixar, não bloqueia

                except Exception as img_error:
                    error_msg = str(img_error)

                    # Erros específicos com mensagens amigáveis
                    if "API key" in error_msg or "401" in error_msg:
                        st.sidebar.error("❌ Chave de API inválida ou expirada!")
                        st.error("Erro de autenticação. Verifique sua chave.")

                    elif "quota" in error_msg.lower() or "limit" in error_msg.lower() or "429" in error_msg:
                        st.sidebar.error("❌ Limite de uso atingido!")
                        st.error("Quota da API excedida. Tente novamente mais tarde.")

                    elif "content" in error_msg.lower() or "policy" in error_msg.lower():
                        st.sidebar.error("❌ Conteúdo não permitido!")
                        st.error("A imagem viola políticas de conteúdo. Tente outra descrição.")

                    elif "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                        st.sidebar.error("❌ Erro de conexão!")
                        st.error("Tempo esgotado ao conectar ao servidor. Verifique sua internet.")

                    else:
                        st.sidebar.error(f"❌ Erro ao gerar imagem: {error_msg[:100]}")
                        st.error(f"Detalhes técnicos: {error_msg}")

        # Histórico de imagens
        if st.session_state.images:
            st.sidebar.markdown("---")
            st.sidebar.markdown("#### 📜 Últimas Imagens")
            for idx, img in enumerate(st.session_state.images[-3:]):  # Últimas 3
                with st.sidebar.expander(f"📷 {img['timestamp']}"):
                    st.image(img['url'], width=200)
                    st.caption(img['prompt'][:50] + "...")

        # ========== CHAT PRINCIPAL ==========
        st.markdown("---")
        st.markdown("### 💬 Chat")

        # Exibir mensagens do chat
        for message in st.session_state.messages:
            if message["role"] == "system":
                continue

            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Input do usuário
        prompt = st.chat_input("Converse com a Alex IA Ultra...")

        if prompt:
            # Adicionar mensagem do usuário
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            # Preparar contexto do arquivo se existir
            context = ""
            if st.session_state.file_text:
                context = f"""

                Use este conteúdo como referência se necessário:

                {st.session_state.file_text[:3000]}  # Limitar a 3000 chars para não estourar o contexto
                """

            full_prompt = prompt + context

            # Obter resposta da IA
            try:
                with st.spinner("Pensando..."):
                    response = client.chat.completions.create(
                        model="openrouter/livre",  # Ajuste o modelo conforme necessário
                        messages=st.session_state.messages,
                        max_tokens=4000,
                        temperature=0.7
                    )

                    assistant_response = response.choices[0].message.content

                    # Adicionar resposta ao histórico
                    st.session_state.messages.append(
                        {"role": "assistant", "content": assistant_response}
                    )

                    with st.chat_message("assistant"):
                        st.markdown(assistant_response)

            except Exception as chat_error:
                st.error(f"Erro na comunicação com a IA: {str(chat_error)}")
                # Remover mensagem do usuário se deu erro
                if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                    st.session_state.messages.pop()

    except Exception as e:
        st.error(f"Erro geral no sistema: {str(e)}")
        st.info("Verifique sua conexão e chave de API.")

else:
    st.info("👆 Por favor, insira sua chave da API para começar.")
