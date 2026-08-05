import streamlit as st
from openai import OpenAI
from pypdf import PdfReader
import base64
import io

st.set_page_config(
    page_title="🤖 Alex IA Ultra",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Alex IA Ultra")
st.caption("Sua inteligência artificial pessoal")

# ------------------------------------------------------------------
# CONFIGURAÇÃO
# ------------------------------------------------------------------

MODELO_TEXTO = "meta-llama/llama-3.3-70b-instruct:free"   # modelo de texto gratuito
MODELO_IMAGEM = "google/gemini-2.5-flash-image-preview"   # modelo com geração de imagem

SYSTEM_PROMPT = (
    "Você é a Alex IA Ultra, uma inteligência artificial avançada criada por "
    "Geovani. Responda sempre em português de forma inteligente. "
    "Se o usuário pedir para gerar, criar ou desenhar uma imagem, diga que "
    "ele pode usar o comando /imagem seguido da descrição."
)

api_key = st.text_input(
    "Digite sua chave do OpenRouter:",
    type="password"
)

if api_key:
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        # --------------------------------------------------------
        # ESTADO DA SESSÃO
        # --------------------------------------------------------
        if "mensagens" not in st.session_state:
            st.session_state.mensagens = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]

        if "arquivo_texto" not in st.session_state:
            st.session_state.arquivo_texto = ""

        # --------------------------------------------------------
        # SIDEBAR - ARQUIVOS
        # --------------------------------------------------------
        st.sidebar.title("📄 Arquivos")

        arquivo = st.sidebar.file_uploader(
            "Envie um arquivo",
            type=["txt", "pdf"]
        )

        if arquivo:
            if arquivo.type == "text/plain":
                st.session_state.arquivo_texto = arquivo.read().decode("utf-8")

            elif arquivo.type == "application/pdf":
                leitor = PdfReader(arquivo)
                texto = ""
                for pagina in leitor.pages:
                    texto += pagina.extract_text() or ""
                st.session_state.arquivo_texto = texto

            st.sidebar.success("Arquivo carregado com sucesso!")

        st.sidebar.divider()
        st.sidebar.title("🎨 Geração de imagem")
        st.sidebar.info(
            "Digite `/imagem sua descrição aqui` no chat para gerar uma imagem.\n\n"
            "Ex: `/imagem um gato astronauta no espaço`"
        )

        st.sidebar.divider()
        if st.sidebar.button("🗑️ Limpar conversa"):
            st.session_state.mensagens = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
            st.session_state.arquivo_texto = ""
            st.rerun()

        # --------------------------------------------------------
        # MOSTRAR CONVERSA
        # --------------------------------------------------------
        for mensagem in st.session_state.mensagens:
            if mensagem["role"] != "system":
                with st.chat_message(mensagem["role"]):
                    if isinstance(mensagem["content"], list):
                        for bloco in mensagem["content"]:
                            if bloco.get("type") == "image":
                                st.image(bloco["data"])
                            elif bloco.get("type") == "text":
                                st.write(bloco["text"])
                    else:
                        st.write(mensagem["content"])

        pergunta = st.chat_input("Converse com a Alex IA Ultra... (ou use /imagem)")

        if pergunta:
            # ---------------- MODO IMAGEM ----------------
            if pergunta.strip().lower().startswith("/imagem"):
                prompt_imagem = pergunta.strip()[7:].strip()

                if not prompt_imagem:
                    st.warning("Descreva a imagem depois de /imagem. Ex: /imagem um pôr do sol na praia")
                else:
                    st.session_state.mensagens.append(
                        {"role": "user", "content": f"/imagem {prompt_imagem}"}
                    )
                    with st.chat_message("user"):
                        st.write(f"/imagem {prompt_imagem}")

                    with st.chat_message("assistant"):
                        with st.spinner("Gerando imagem..."):
                            try:
                                resposta = client.chat.completions.create(
                                    model=MODELO_IMAGEM,
                                    messages=[
                                        {"role": "user", "content": prompt_imagem}
                                    ],
                                    modalities=["image", "text"]
                                )

                                msg = resposta.choices[0].message
                                imagens = getattr(msg, "images", None)

                                if imagens:
                                    url_imagem = imagens[0]["image_url"]["url"]
                                    st.image(url_imagem)
                                    st.session_state.mensagens.append(
                                        {
                                            "role": "assistant",
                                            "content": [
                                                {"type": "image", "data": url_imagem}
                                            ]
                                        }
                                    )
                                else:
                                    st.error(
                                        "O modelo não retornou uma imagem. "
                                        "Verifique se o modelo configurado (MODELO_IMAGEM) "
                                        "suporta geração de imagens no OpenRouter."
                                    )
                            except Exception as e:
                                st.error(f"Erro ao gerar imagem: {e}")

            # ---------------- MODO TEXTO NORMAL ----------------
            else:
                contexto = ""
                if st.session_state.arquivo_texto:
                    contexto = (
                        "\n\nUse este arquivo como base para responder:\n\n"
                        + st.session_state.arquivo_texto
                    )

                st.session_state.mensagens.append(
                    {"role": "user", "content": pergunta}
                )

                with st.chat_message("user"):
                    st.write(pergunta)

                # Monta o payload enviado à API SEM salvar o contexto repetido no histórico
                mensagens_para_api = list(st.session_state.mensagens)
                if contexto:
                    mensagens_para_api = mensagens_para_api[:-1] + [
                        {"role": "user", "content": pergunta + contexto}
                    ]

                with st.chat_message("assistant"):
                    with st.spinner("Pensando..."):
                        try:
                            resposta = client.chat.completions.create(
                                model=MODELO_TEXTO,
                                messages=mensagens_para_api
                            )
                            texto_resposta = resposta.choices[0].message.content
                            st.write(texto_resposta)

                            st.session_state.mensagens.append(
                                {"role": "assistant", "content": texto_resposta}
                            )
                        except Exception as e:
                            st.error(f"Erro ao gerar resposta: {e}")

    except Exception as e:
        st.error(f"Erro: {e}")

# ------------------------------------------------------------------
# ESTRUTURA RESERVADA PARA VÍDEO (desativada)
# ------------------------------------------------------------------
# O OpenRouter não oferece geração de vídeo. Para ativar essa função,
# você precisaria integrar outro provedor (ex: Runway, Luma, Stability
# AI Video) com sua própria chave de API, e criar uma função aqui,
# semelhante à de geração de imagem acima, chamando o endpoint desse
# provedor e exibindo o vídeo com st.video(url_do_video).
