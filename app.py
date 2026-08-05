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

api_key = st.text_input(
    "Digite sua chave do OpenRouter:",
    type="password"
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
        st.sidebar.title("📄 Arquivos")

        arquivo = st.sidebar.file_uploader(
            "Envie um arquivo",
            type=["txt", "pdf"]
        )

        if arquivo:

            if arquivo.type == "text/plain":
                st.session_state.arquivo_texto = arquivo.read().decode("utf-8")

            elif arquivo.type == "application/pdf":

                leitor = PyPDF2.PdfReader(arquivo)

                texto = ""

                for pagina in leitor.pages:
                    texto += pagina.extract_text() or ""

                st.session_state.arquivo_texto = texto

            st.sidebar.success("Arquivo carregado com sucesso!")

        if st.sidebar.button("🗑️ Limpar conversa"):
            st.session_state.mensagens = [
                {
                    "role": "system",
                    "content": "Você é a Alex IA Ultra, uma inteligência artificial avançada criada por Geovani."
                }
            ]
            st.session_state.arquivo_texto = ""
            st.rerun()

        # =================================================================
        # NOVA FUNÇÃO: HISTÓRICO E EXPORTAÇÃO (APENAS NA BARRA LATERAL)
        # =================================================================
        st.sidebar.markdown("---")
        st.sidebar.title("📊 Estatísticas & Opções")
        
        # Conta apenas mensagens que não são do sistema
        total_mensagens = len([m for m in st.session_state.mensagens if m["role"] != "system"])
        st.sidebar.metric(label="Total de Mensagens", value=total_mensagens)
        
        # Cria o texto formatado para download do histórico
        historico_texto = ""
        for m in st.session_state.mensagens:
            if m["role"] != "system":
                nome_usuario = "Você" if m["role"] == "user" else "Alex IA Ultra"
                historico_texto += f"{nome_usuario}: {m['content']}\n\n"
        
        if total_mensagens > 0:
            st.sidebar.download_button(
                label="📥 Baixar conversa (.txt)",
                data=historico_texto,
                file_name="historico_alex_ia.txt",
                mime="text/plain",
                use_container_width=True
            )
        # =================================================================

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

            resposta = client.chat.completions.create(
                model="openrouter/free",
                messages=st.session_state.mensagens
            )

            texto_resposta = resposta.choices[0].message.content

            st.session_state.mensagens.append(
                {
                    "role": "assistant",
                    "content": texto_resposta
                }
            )

            with st.chat_message("assistant"):
                st.write(texto_resposta)

    except Exception as e:
        st.error(f"Erro: {e}")
        
