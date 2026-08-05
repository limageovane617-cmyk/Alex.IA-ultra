import streamlit as st
import requests
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

# Seletor de Modelos Dinâmico
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
    if not api_key:
        st.error("🔑 Por favor, insira sua chave do OpenRouter na barra lateral primeiro!")
    else:
        # Exibe e guarda a pergunta do usuário no histórico visível
        with st.chat_message("user"):
            st.write(pergunta)
        
        st.session_state.mensagens.append({"role": "user", "content": pergunta})

        # Prepara a estrutura do prompt de sistema
        mensagens_api = [
            {
                "role": "system",
                "content": "Você é a Alex IA Ultra, uma inteligência artificial avançada criada por Geovani. Responda sempre em português de forma inteligente, prestativa e objetiva."
            }
        ]

        # Injeta o contexto do arquivo se ele existir
        if st.session_state.arquivo_texto:
            mensagens_api.append({
                "role": "system",
                "content": f"Use estritamente os dados abaixo para responder o usuário se a pergunta for sobre o documento:\n```{st.session_state.arquivo_texto}```"
            })

        # Alinha o histórico do chat acumulado
        mensagens_api.extend(st.session_state.mensagens)

        # Resposta da IA via HTTP Direto (Evita o bloqueio de código HTML)
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    # Cabeçalhos manuais simulando um navegador real para passar pelo bloqueio
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "HTTP-Referer": "http://localhost:8501",
                        "X-Title": "Alex IA Ultra"
                    }
                    
                    payload = {
                        "model": modelo_selecionado,
                        "messages": mensagens_api
                    }

                    # Faz a requisição POST direto no endpoint da OpenRouter
                    response = requests.post(
                        "https://openrouter.ai",
                        headers=headers,
                        json=payload
                    )

                    # Verifica se deu algum erro HTTP de autenticação ou limites
                    if response.status_code == 200:
                        dados = response.json()
                        texto_resposta = dados["choices"][0]["message"]["content"]
                        
                        # Mostra o texto finalizado na tela
                        st.write(texto_resposta)

                        # Salva a resposta gerada no histórico do session_state
                        st.session_state.mensagens.append({"role": "assistant", "content": texto_resposta})
                    elif response.status_code == 401:
                        st.error("❌ Erro 401: Chave de API inválida ou incorreta. Verifique suas configurações na barra lateral.")
                    else:
                        st.error(f"❌ Erro do OpenRouter (Código {response.status_code}): {response.text[:200]}")
                
                except Exception as api_error:
                    st.error(f"Erro ao processar requisição: {api_error}")
                    
