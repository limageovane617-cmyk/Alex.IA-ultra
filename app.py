import streamlit as st
from openai import OpenAI
import PyPDF2
import urllib.parse

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

PALAVRAS_GATILHO_IMAGEM = [
    "gere uma imagem", "gerar uma imagem", "crie uma imagem", "criar uma imagem",
    "desenhe", "desenhar", "faça uma imagem", "fazer uma imagem",
    "gere um desenho", "crie um desenho", "gere uma foto", "gere uma arte"
]


def eh_pedido_de_imagem(texto):
    texto_lower = texto.lower()
    return any(gatilho in texto_lower for gatilho in PALAVRAS_GATILHO_IMAGEM)


def extrair_prompt_imagem(texto):
    texto_lower = texto.lower()
    prompt = texto
    for gatilho in PALAVRAS_GATILHO_IMAGEM:
        if gatilho in texto_lower:
            idx = texto_lower.find(gatilho)
            prompt = texto[idx + len(gatilho):].strip()
            break
    # Remove conectivos comuns no início ("de", "do", "da", ":")
    for prefixo in ["de ", "do ", "da ", ": ", ":"]:
        if prompt.lower().startswith(prefixo):
            prompt = prompt[len(prefixo):].strip()
    return prompt if prompt else texto


def gerar_url_imagem(prompt, largura=1024, altura=1024):
    prompt_codificado = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{prompt_codificado}?width={largura}&height={altura}&nologo=true"


if api_key:

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
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

        if "historico_exibicao" not in st.session_state:
            # Guarda o histórico visual, incluindo imagens geradas
            st.session_state.historico_exibicao = []

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

        st.sidebar.title("🎨 Imagens")
        st.sidebar.caption("Peça imagens direto no chat: \"gere uma imagem de um pôr do sol\"")
        tamanho_imagem = st.sidebar.selectbox(
            "Tamanho das imagens",
            options=["1024x1024", "1024x768", "768x1024", "1280x720"],
            index=0
        )
        largura_img, altura_img = [int(v) for v in tamanho_imagem.split("x")]

        if st.sidebar.button("🗑️ Limpar conversa"):
            st.session_state.mensagens = [
                {
                    "role": "system",
                    "content": "Você é a Alex IA Ultra, uma inteligência artificial avançada criada por Geovani."
                }
            ]
            st.session_state.arquivo_texto = ""
            st.session_state.historico_exibicao = []
            st.rerun()

        # Mostrar conversa (texto + imagens)
        for item in st.session_state.historico_exibicao:

            with st.chat_message(item["role"]):

                if item["tipo"] == "texto":
                    st.write(item["conteudo"])

                elif item["tipo"] == "imagem":
                    st.image(item["conteudo"], caption=item.get("prompt", ""))

        pergunta = st.chat_input(
            "Converse com a Alex IA Ultra..."
        )

        if pergunta:

            st.session_state.historico_exibicao.append(
                {"role": "user", "tipo": "texto", "conteudo": pergunta}
            )

            with st.chat_message("user"):
                st.write(pergunta)

            if eh_pedido_de_imagem(pergunta):

                prompt_imagem = extrair_prompt_imagem(pergunta)
                url_imagem = gerar_url_imagem(prompt_imagem, largura_img, altura_img)

                with st.chat_message("assistant"):
                    with st.spinner("Gerando imagem..."):
                        st.image(url_imagem, caption=prompt_imagem)

                st.session_state.historico_exibicao.append(
                    {
                        "role": "assistant",
                        "tipo": "imagem",
                        "conteudo": url_imagem,
                        "prompt": prompt_imagem
                    }
                )

                # Mantém o modelo de texto ciente de que uma imagem foi gerada
                st.session_state.mensagens.append(
                    {"role": "user", "content": pergunta}
                )
                st.session_state.mensagens.append(
                    {
                        "role": "assistant",
                        "content": f"[Imagem gerada com sucesso para o pedido: {prompt_imagem}]"
                    }
                )

            else:

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

                st.session_state.historico_exibicao.append(
                    {"role": "assistant", "tipo": "texto", "conteudo": texto_resposta}
                )

                with st.chat_message("assistant"):
                    st.write(texto_resposta)

    except Exception as e:
        st.error(f"Erro: {e}")
