import streamlit as st
from google import genai

# Configuração da página
st.set_page_config(
    page_title="Alex IA",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Alex IA")
st.caption("Olá Geovani! Eu sou sua inteligência artificial pessoal. Estou pronto para criar, escrever, programar e ajudar você no quer vc precisa.")

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []
    
if "personagem" not in st.session_state:
    st.session_state.personagem = {}
# Campo da chave API
api_key = st.text_input(
    "ola Geovani sua chave da API :",
    type="password"
)

if api_key:

    try:
        # Conecta ao Gemini
        cliente = genai.Client(api_key=api_key)
        
        st.success("✅ Gemini conectado com sucesso!")

        st.sidebar.header("⚙️ Ferramentas")
        
        modo = st.sidebar.radio(
         "Escolha o modo:",
         ["🤖 IA normal", "🎭 Personagem"]
        )
        if st.sidebar.button("🗑️ Limpar conversa"):
            st.session_state.mensagens = []
            st.rerun()

        st.sidebar.header("🎭 Personagem")

        nome_personagem = st.sidebar.text_input("Nome")
        idade_personagem = st.sidebar.text_input("Idade")
        aparencia_personagem = st.sidebar.text_area("Aparência")
        roupa_personagem = st.sidebar.text_input("Roupa")
        personalidade_personagem = st.sidebar.text_area("Personalidade")

        if st.sidebar.button("💾 Salvar personagem"):
            st.session_state.personagem = {
                "nome": nome_personagem,
                "idade": idade_personagem,
                "aparencia": aparencia_personagem,
                "roupa": roupa_personagem,
                "personalidade": personalidade_personagem,
            }
            st.sidebar.success("✅ Personagem salvo!")

        # Campo da pergunta
        pergunta = st.chat_input("Digite sua mensagem...")
        
            if pergunta:

            if modo == "🎭 Personagem":
                contexto_personagem = f"""
Personagem principal:

Nome: {nome_personagem}

Idade: {idade_personagem}

Aparência: {aparencia_personagem}

Roupa: {roupa_personagem}

Personalidade: {personalidade_personagem}
"""
            else:
                contexto_personagem = ""

            resposta = cliente.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=f"""
Você é o Alex IA, uma inteligência artificial avançada.

Modo atual:
{modo}

Regras:

Se o modo for "🤖 IA normal":
- Responda normalmente ao usuário.
- Não peça informações de personagem.
- Não crie personagem automaticamente.

Se o modo for "🎭 Personagem":
- Use os dados do personagem salvo.
- Crie histórias, cenas e roteiros usando o personagem.

Você sempre responde em português do Brasil.

Seja criativo, organizado e ajude Geovani a desenvolver seus projetos.

{contexto_personagem}

Pergunta do usuário:
{pergunta}
"""
            )

            st.subheader("🤖 Alex IA respondeu:")
            st.write(resposta.text)

    except Exception as e:
        st.error(f"Erro: {e}")
