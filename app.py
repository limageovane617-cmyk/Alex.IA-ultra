import streamlit as st
from google import genai
import json
import sqlite3
from config import SYSTEM_PROMPT


# Configuração da página
st.set_page_config(
    page_title="Alex IA",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Alex IA")
st.caption(
    "Olá Geovani! Eu sou sua inteligência artificial pessoal. "
    "Estou pronto para criar, escrever, programar e ajudar você no que precisar."
)


# Memória da conversa
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []


# Personagem atual
if "personagem" not in st.session_state:
    st.session_state.personagem = {}


# Banco de dados
conn = sqlite3.connect("alexia.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS personagens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE,
    idade TEXT,
    aparencia TEXT,
    roupa TEXT,
    personalidade TEXT
)
""")

conn.commit()
cursor.execute("""
CREATE TABLE IF NOT EXISTS memoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    informacao TEXT NOT NULL
)
""")

conn.commit()


# Personagens salvos em JSON
try:
    with open("personagens.json", "r", encoding="utf-8") as arquivo:
        personagens_salvos = json.load(arquivo)
except Exception:
    personagens_salvos = {}


# Chave da API
api_key = st.text_input(
    "Olá Geovani, sua chave da API:",
    type="password"
)


if api_key:

    try:

        # Conecta ao Gemini
        cliente = genai.Client(api_key=api_key)

        st.success("✅ Gemini conectado com sucesso!")


        # Barra lateral
        st.sidebar.header("⚙️ Ferramentas")


        # Limpar conversa
        if st.sidebar.button("🗑️ Limpar conversa"):

            st.session_state.mensagens = []

            st.rerun()


        # Área de personagens
        st.sidebar.header("🎭 Personagem")
        st.sidebar.subheader("📚 Personagens salvos")


        cursor.execute(
            "SELECT nome FROM personagens ORDER BY nome"
        )

        lista_personagens = cursor.fetchall()


        # Valores padrão
        nome_personagem = ""
        idade_personagem = ""
        aparencia_personagem = ""
        roupa_personagem = ""
        personalidade_personagem = ""


        # Lista de personagens salvos
        if lista_personagens:

            personagem_escolhido = st.sidebar.selectbox(
                "Escolha um personagem",
                [p[0] for p in lista_personagens]
            )


            if personagem_escolhido:

                cursor.execute("""
                    SELECT idade, aparencia, roupa, personalidade
                    FROM personagens
                    WHERE nome = ?
                """, (personagem_escolhido,))

                dados = cursor.fetchone()


                if dados:

                    nome_personagem = personagem_escolhido
                    idade_personagem = dados[0]
                    aparencia_personagem = dados[1]
                    roupa_personagem = dados[2]
                    personalidade_personagem = dados[3]


        # Campos do personagem
        nome_personagem = st.sidebar.text_input(
            "Nome",
            value=nome_personagem
        )

        idade_personagem = st.sidebar.text_input(
            "Idade",
            value=idade_personagem
        )

        aparencia_personagem = st.sidebar.text_area(
            "Aparência",
            value=aparencia_personagem
        )

        roupa_personagem = st.sidebar.text_input(
            "Roupa",
            value=roupa_personagem
        )

        personalidade_personagem = st.sidebar.text_area(
            "Personalidade",
            value=personalidade_personagem
        )


        # Salvar personagem
        if st.sidebar.button("💾 Salvar personagem"):

            if not nome_personagem.strip():

                st.sidebar.warning(
                    "Digite um nome para o personagem."
                )

            else:

                st.session_state.personagem = {
                    "nome": nome_personagem,
                    "idade": idade_personagem,
                    "aparencia": aparencia_personagem,
                    "roupa": roupa_personagem,
                    "personalidade": personalidade_personagem,
                }


                personagens_salvos[nome_personagem] = (
                    st.session_state.personagem
                )


                with open(
                    "personagens.json",
                    "w",
                    encoding="utf-8"
                ) as arquivo:

                    json.dump(
                        personagens_salvos,
                        arquivo,
                        ensure_ascii=False,
                        indent=4
                    )


                cursor.execute("""
                    INSERT OR REPLACE INTO personagens
                    (nome, idade, aparencia, roupa, personalidade)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    nome_personagem,
                    idade_personagem,
                    aparencia_personagem,
                    roupa_personagem,
                    personalidade_personagem
                ))


                conn.commit()


                st.sidebar.success(
                    "✅ Personagem salvo!"
                )


        # Campo da pergunta
        pergunta = st.chat_input(
            "Digite sua mensagem..."
        )


        if pergunta:

            # Guarda a mensagem do usuário
            st.session_state.mensagens.append({
                "role": "user",
                "content": pergunta
            })


            # Contexto do personagem
            contexto_personagem = ""


            if nome_personagem.strip():

                contexto_personagem = f"""
Existe um personagem criado pelo usuário.

Nome: {nome_personagem}
Idade: {idade_personagem}
Aparência: {aparencia_personagem}
Roupa: {roupa_personagem}
Personalidade: {personalidade_personagem}

Use esse personagem somente quando o usuário pedir.
"""


            # Monta o histórico da conversa
            historico = ""

            for mensagem in st.session_state.mensagens:

                if mensagem["role"] == "user":

                    historico += (
                        f"Geovani: {mensagem['content']}\n"
                    )

                elif mensagem["role"] == "assistant":

                    historico += (
                        f"Alex IA: {mensagem['content']}\n"
                    )


            # Envia para o Gemini
            resposta = cliente.models.generate_content(

                model="gemini-3.1-flash-lite",

                contents=f"""
{SYSTEM_PROMPT}

Converse naturalmente com o usuário.

Regras:

- Entenda o contexto da conversa.
- Lembre-se das mensagens anteriores.
- Use o histórico da conversa para manter continuidade.
- Se o usuário pedir um personagem, crie ou interprete esse personagem.
- Se o usuário não pedir personagem, responda normalmente como Alex IA.
- Não obrigue o usuário a escolher um modo.
- Sempre responda em português do Brasil.
- Seja criativo, organizado e ajude Geovani em seus projetos.

{contexto_personagem}

Histórico da conversa:

{historico}

Pergunta atual de Geovani:

{pergunta}
"""
            )


            # Texto da resposta
            texto_resposta = resposta.text


            # Guarda a resposta na memória
            st.session_state.mensagens.append({
                "role": "assistant",
                "content": texto_resposta
            })


            # Mostra resposta
            st.subheader("🤖 Alex IA respondeu:")

            st.write(texto_resposta)


    except Exception as e:

        st.error(
            f"Erro: {e}"
        )


    finally:

        conn.close()
