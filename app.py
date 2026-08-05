import streamlit as st
from openai import OpenAI
import PyPDF2

st.set_page_config(
    page_title="🤖 Alex IA Ultra",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Alex IA Ultra")
st.caption("Sua inteligência artificial pessoal")

# Área de configurações na barra lateral
st.sidebar.title("⚙️ Configurações")

api_key = st.sidebar.text_input(
    "Digite sua chave do OpenRouter:",
    type="password"
)

# NOVA FUNÇÃO 1: Seletor de Modelos na barra lateral
modelo_selecionado = st.sidebar.selectbox(
    "Escolha o cérebro da IA:",
    options=[
        "openrouter/free", 
        "meta-llama/llama-3-8b-instruct:free", 
        "mistralai/mistral-7b-instruct:free",
        "google/gemma-2-9b-it:free"
    ],
    index=0,
    help="Selecione o modelo do OpenRouter que processará as mensagens."
)

if api_key:

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai"
        )

        if "mensagens" not in st.session_state:
            st.session_state.mensagens = [
                {
                    "role": "system",
                    "content": "Você é a Alex IA Ultra, uma inteligência artificial avançada criada por Geovani. Responda sempre em português de forma inteligente."
                }
            ]

        if "arquivo_texto" not in st.session_state:
            st.session_state.arquivo_texto = ""

        # Área de arquivos
        st.sidebar.markdown("---")
        st.sidebar.title("📄 Arquivos")

        arquivo = st.sidebar.file_uploader(
            "Envie um arquivo",
            type=["txt", "pdf"]
        )

        if arquivo:
            # NOVA FUNÇÃO 3: Spinner visual para indicar leitura do arquivo
            with st.sidebar.spinner("Processando documento..."):
                if arquivo.type == "text/plain":
                    st.session_state.arquivo_texto = arquivo.read().decode("utf-8")

                elif arquivo.type == "application/pdf":

                    leitor = PyPDF2.PdfReader(arquivo)

                    texto = ""

                    for pagina in leitor.pages:
                        texto += pagina.extract_text() or ""

                    st.session_state.arquivo_texto = texto

            st.sidebar.success("Arquivo carregado com sucesso!")
            
            # NOVA FUNÇÃO 2: Indicador estatístico do tamanho do documento
            tamanho_caracteres = len(st.session_state.arquivo_texto)
            st.sidebar.info(f"O documento possui aprox. {tamanho_caracteres} caracteres.")

        if st.sidebar.button("🗑️ Limpar conversa"):
            st.session_state.mensagens = [
                {
                    "role": "system",
                    "content": "Você é a Alex IA Ultra, uma inteligência artificial avançada criada por Geovani."
                }
            ]
            st.session_state.arquivo_texto = ""
            st.rerun()

        # Mostrar conversa
        for mensagem in st.session_state.mensagens:

            if mensagem["role"] != "system":

                with st.chat_message(mensagem["role"]):
                    st.write(mensagem["content"])

        pergunta = st.chat_input(
            "Converse com a Alex IA Ultra..."
        )

        if pergunta:

            contexto = ""

            if st.session_state.arquivo_texto:

                contexto = f"""

Use este arquivo como base para responder:

{st.session_state.arquivo_texto}

"""

            st.session_state.mensagens.append(
                {
                    "role": "user",
                    "content": pergunta + contexto
                }
            )

            with st.chat_message("user"):
                st.write(pergunta)

            with st.chat_message("assistant"):
                # NOVA FUNÇÃO 3: Spinner visual de carregamento para a IA pensando
                with st.spinner("Pensando..."):
                    resposta = client.chat.completions.create(
                        model=modelo_selecionado, # Vinculado à NOVA FUNÇÃO 1
                        messages=st.session_state.mensagens
                    )

                    texto_resposta = resposta.choices[0].message.content
                    st.write(texto_resposta)

            st.session_state.mensagens.append(
                {
                    "role": "assistant",
                    "content": texto_resposta
                }
            )

    except Exception as e:
        st.error(f"Erro: {e}")
else:
    # NOVA FUNÇÃO 4: Mensagem informativa amigável inicial
    st.info("💡 Por favor, insira sua chave do OpenRouter na barra lateral esquerda para iniciar a Alex IA Ultra.")
    
