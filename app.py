import streamlit as st
from openai import OpenAI
import PyPDF2

st.set_page_config(
    page_title="🤖 Alex IA Ultra",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Alex IA Ultra")
st.caption("Sua inteligência artificial avançada e personalizada")

# Barra Lateral Organizável
st.sidebar.title("⚙️ Configurações")

api_key = st.sidebar.text_input(
    "Chave do OpenRouter:",
    type="password"
)

# Seletor de Modelos Dinâmico (Modelos free estáveis da OpenRouter)
modelo_selecionado = st.sidebar.selectbox(
    "Escolha o cérebro da IA:",
    options=[
        "openrouter/free", 
        "meta-llama/llama-3-8b-instruct:free", 
        "mistralai/mistral-7b-instruct:free",
        "google/gemma-2-9b-it:free"
    ],
    index=0,
    help="Selecione o modelo de IA que processará suas mensagens."
)

if api_key:
    try:
        # Inicializa o cliente OpenRouter com cabeçalhos recomendados
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai",
            default_headers={
                "HTTP-Referer": "http://localhost:8501",
                "X-Title": "Alex IA Ultra"
            }
        )

        if "mensagens" not in st.session_state:
            st.session_state.mensagens = []

        if "arquivo_texto" not in st.session_state:
            st.session_state.arquivo_texto = ""

        # Área de arquivos na barra lateral
        st.sidebar.markdown("---")
        st.sidebar.title("📄 Upload de Documentos")

        arquivo = st.sidebar.file_uploader(
            "Envie um arquivo para contextualizar a IA",
            type=["txt", "pdf"]
        )

        if arquivo:
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
            
            # Mini-Indicador de tamanho do documento
            tamanho_caracteres = len(st.session_state.arquivo_texto)
            st.sidebar.info(f"O documento possui aprox. {tamanho_caracteres} caracteres.")

        # Botão para limpar o histórico
        st.sidebar.markdown("---")
        if st.sidebar.button("🗑️ Limpar Conversa", use_container_width=True):
            st.session_state.mensagens = []
            st.session_state.arquivo_texto = ""
            st.rerun()

        # Mostrar o histórico de conversas na tela
        for mensagem in st.session_state.mensagens:
            with st.chat_message(mensagem["role"]):
                st.write(mensagem["content"])

        # Input do usuário
        pergunta = st.chat_input("Converse com a Alex IA Ultra...")

        if pergunta:
            # Exibe e guarda a pergunta do usuário no histórico visível
            with st.chat_message("user"):
                st.write(pergunta)
            
            st.session_state.mensagens.append({"role": "user", "content": pergunta})

            # Prepara a estrutura do prompt de sistema (invisível no chat direto)
            mensagens_api = [
                {
                    "role": "system",
                    "content": "Você é a Alex IA Ultra, uma inteligência artificial avançada criada por Geovani. Responda sempre em português de forma inteligente, prestativa e objetiva."
                }
            ]

            # Injeta o contexto do arquivo se ele existir (separado do histórico de perguntas)
            if st.session_state.arquivo_texto:
                mensagens_api.append({
                    "role": "system",
                    "content": f"Use estritamente os dados abaixo para responder o usuário se a pergunta for sobre o documento:\n```{st.session_state.arquivo_texto}```"
                })

            # Alinha o histórico do chat acumulado
            mensagens_api.extend(st.session_state.mensagens)

            # Resposta da IA (Modo Normal Seguro - Sem Streaming que trava)
            with st.chat_message("assistant"):
                # Adiciona um spinner visual simples enquanto a IA pensa
                with st.spinner("Pensando..."):
                    try:
                        # Chamada padrão segura
                        resposta = client.chat.completions.create(
                            model=modelo_selecionado,
                            messages=mensagens_api
                        )

                        # Captura o texto da resposta vindo direto do objeto estruturado
                        texto_resposta = resposta.choices[0].message.content
                        
                        # Mostra o texto finalizado na tela
                        st.write(texto_resposta)

                        # Salva a resposta gerada no histórico do session_state
                        st.session_state.mensagens.append({"role": "assistant", "content": texto_resposta})
                    
                    except Exception as api_error:
                        st.error(f"Erro ao obter resposta da IA: {api_error}")

    except Exception as e:
        st.error(f"Erro de inicialização do cliente: {e}")
else:
    st.info("💡 Por favor, insira sua chave do OpenRouter na barra lateral esquerda para começar.")
    
