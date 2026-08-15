# ============================================================
# 🤖 ALEX IA ULTRA
# APP PRINCIPAL
# ============================================================
# Criado por: Geovani
#
# Funções:
# - Chat com Gemini
# - Memória
# - Personagens
# - Imagens
# - Vídeos
# - Voz
# - Arquivos
# - Código
#
# ============================================================


# ============================================================
# 📦 IMPORTAÇÕES
# ============================================================

import base64
import os
import sys
import importlib
from pathlib import Path

import streamlit as st


# ============================================================
# ⚙️ CONFIGURAÇÃO DO STREAMLIT
# ============================================================

st.set_page_config(

    page_title="Alex IA Ultra",

    page_icon="🤖",

    layout="wide",

    initial_sidebar_state="collapsed"

)


# ============================================================
# 🔄 RECARREGAR GERENCIADOR DE IMAGEM
# ============================================================

if "gerenciador_imagem" in sys.modules:

    importlib.reload(
        sys.modules["gerenciador_imagem"]
    )

else:

    import gerenciador_imagem


from gerenciador_imagem import (
    mostrar_imagem
)


# ============================================================
# 🧠 CONFIGURAÇÕES DA IA
# ============================================================

from config_ultra import (

    SYSTEM_PROMPT,

    GEMINI_MODEL,

    AI_NAME,

    CREATOR_NAME

)


# ============================================================
# 🔐 SERVIÇOS
# ============================================================

from servicos import (

    criar_cliente_gemini,

    verificar_servicos

)


# ============================================================
# 🧠 MEMÓRIA
# ============================================================

from memoria import (

    salvar_memoria,

    carregar_memorias,

    apagar_memoria,

    apagar_todas_memorias

)


# ============================================================
# 🎭 PERSONAGENS
# ============================================================

from personagens import (

    salvar_personagem,

    carregar_personagem,

    listar_personagens,

    apagar_personagem

)


# ============================================================
# 🔊 VOZ
# ============================================================

from voz import (
    mostrar_audio
)


# ============================================================
# 🎬 VÍDEO
# ============================================================

from video import (

    gerar_video,

    mostrar_configuracao_video,

    verificar_magic_hour

)


# ============================================================
# 📂 ARQUIVOS
# ============================================================

from arquivos import (
    ler_arquivo
)


# ============================================================
# 💻 CÓDIGO
# ============================================================

from codigo import (

    preparar_pedido_codigo,

    listar_linguagens

)


# ============================================================
# 🧠 SESSION STATE
# ============================================================

DEFAULTS = {

    "mensagens": [],

    "personagem_atual": None,

    "arquivo_contexto": "",

    "arquivo_nome": "",

    "ferramenta_ativa": None,

    "usar_voz": False,

    "ultima_imagem_caminho": None,

}


for chave, valor in DEFAULTS.items():

    if chave not in st.session_state:

        st.session_state[chave] = valor


# ============================================================
# 🔐 VERIFICAR SERVIÇOS
# ============================================================

servicos = verificar_servicos()


if not servicos.get("gemini"):

    st.error(

        "🔐 A chave GEMINI_API_KEY "
        "não está configurada nos "
        "Secrets do Streamlit."

    )

    st.stop()


# ============================================================
# 🤖 CRIAR CLIENTE GEMINI
# ============================================================

cliente = criar_cliente_gemini()


if cliente is None:

    st.error(

        "❌ Não foi possível criar "
        "a conexão com o Gemini."

    )

    st.stop()


# ============================================================
# 🖼️ FUNDO DO CHAT
# ============================================================

def imagem_fundo_css():

    caminho = Path(
        __file__
    ).with_name(
        "fundo_chat.jpg"
    )


    if not caminho.exists():

        return ""


    try:

        dados = base64.b64encode(

            caminho.read_bytes()

        ).decode(
            "utf-8"
        )


        return (

            "background-image:url("
            "data:image/jpeg;base64,"
            f"{dados});"

        )

    except Exception:

        return ""


# ============================================================
# 🎨 CSS
# ============================================================

st.markdown(

    f"""
    <style>

    .stApp {{
        {imagem_fundo_css()}
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    .stApp::before {{
        content: "";
        position: fixed;
        inset: 0;
        background: rgba(2,8,16,.68);
        z-index: -1;
        pointer-events: none;
    }}

    .main .block-container {{
        max-width: 980px;
        padding-top: 1.2rem;
        padding-bottom: 8rem;
    }}

    .ultra-header {{
        text-align: center;
        margin: 0 auto 1.2rem;
        padding: .65rem 1rem;
        border-radius: 22px;
        background: rgba(4,15,28,.58);
        border: 1px solid rgba(120,200,255,.16);
        backdrop-filter: blur(14px);
    }}

    .ultra-name {{
        font-size: clamp(25px,5vw,39px);
        font-weight: 800;
    }}

    .ultra-subtitle {{
        color: rgba(235,245,255,.72);
        font-size: 13px;
    }}

    .tool-panel {{
        margin: 0 auto .65rem;
        padding: .75rem;
        border-radius: 22px;
        background: rgba(8,17,29,.92);
        border: 1px solid rgba(130,210,255,.16);
    }}

    </style>
    """,

    unsafe_allow_html=True

)


# ============================================================
# 🤖 CABEÇALHO
# ============================================================

st.markdown(

    f"""
    <div class="ultra-header">

        <div class="ultra-name">
            🤖 {AI_NAME}
        </div>

        <div class="ultra-subtitle">
            Criada por {CREATOR_NAME}
            • inteligência artificial pessoal
        </div>

    </div>
    """,

    unsafe_allow_html=True

)


# ============================================================
# 💬 HISTÓRICO DO CHAT
# ============================================================

for mensagem in st.session_state.mensagens:

    role = mensagem.get(
        "role",
        "assistant"
    )


    with st.chat_message(role):

        tipo = mensagem.get(
            "tipo",
            "texto"
        )


        # ----------------------------------------------------
        # 🖼️ IMAGEM
        # ----------------------------------------------------

        if (

            tipo == "imagem"

            and mensagem.get("arquivo")

            and os.path.exists(
                mensagem["arquivo"]
            )

        ):

            st.image(

                mensagem["arquivo"],

                use_container_width=True

            )


        # ----------------------------------------------------
        # 🎬 VÍDEO
        # ----------------------------------------------------

        elif (

            tipo == "video"

            and mensagem.get("arquivo")

            and os.path.exists(
                mensagem["arquivo"]
            )

        ):

            st.video(
                mensagem["arquivo"]
            )


        # ----------------------------------------------------
        # 📝 TEXTO
        # ----------------------------------------------------

        st.write(

            mensagem.get(
                "content",
                ""
            )

        )


# ============================================================
# 🧰 MENU DE FERRAMENTAS
# ============================================================

with st.popover("＋"):

    st.markdown(
        "### 🧰 Ferramentas da Ultra"
    )


    ferramentas = [

        ("imagem", "🖼️ Imagem"),

        ("video", "🎬 Vídeo"),

        ("voz", "🔊 Voz"),

        ("codigo", "💻 Código"),

        ("arquivo", "📎 Arquivo"),

        ("personagem", "🎭 Personagem"),

        ("memoria", "🧠 Memória"),

    ]


    for nome, rotulo in ferramentas:

        if st.button(

            rotulo,

            use_container_width=True

        ):

            st.session_state.ferramenta_ativa = nome

            st.rerun()


    st.divider()


    if st.button(

        "🗑️ Limpar chat",

        use_container_width=True

    ):

        st.session_state.mensagens = []

        st.rerun()


# ============================================================
# 🧰 FERRAMENTA ATIVA
# ============================================================

ferramenta = st.session_state.ferramenta_ativa


if ferramenta:

    st.markdown(

        '<div class="tool-panel">',

        unsafe_allow_html=True

    )


    # ========================================================
    # ❌ FECHAR
    # ========================================================

    if st.button(
        "✕ Fechar ferramenta"
    ):

        st.session_state.ferramenta_ativa = None

        st.rerun()


    # ========================================================
    # 🖼️ IMAGEM
    # ========================================================

    if ferramenta == "imagem":

        prompt_imagem = st.text_area(

            "📝 Prompt da imagem",

            key="tool_prompt_imagem",

            height=100

        )


        if st.button(

            "🖼️ Gerar imagem",

            type="primary"

        ):

            if not prompt_imagem.strip():

                st.warning(
                    "Digite o que você quer na imagem."
                )

            else:

                with st.spinner(
                    "🖼️ Criando imagem..."
                ):

                    sucesso = mostrar_imagem(

                        prompt_imagem.strip()

                    )


                if sucesso:

                    st.session_state.mensagens.append({

                        "role":
                            "assistant",

                        "content":
                            "🖼️ Imagem criada.",

                        "tipo":
                            "imagem",

                        "arquivo":
                            st.session_state.get(
                                "ultima_imagem_caminho"
                            ),

                    })


                    st.session_state.ferramenta_ativa = None

                    st.rerun()


    # ========================================================
    # 🎬 VÍDEO
    # ========================================================

    elif ferramenta == "video":

        st.markdown(
            "### 🎬 Gerador de vídeo"
        )


        camera, proporcao, duracao = (
            mostrar_configuracao_video()
        )


        st.divider()


        imagem = st.file_uploader(

            "📤 Imagem de referência "
            "(opcional)",

            type=[

                "png",

                "jpg",

                "jpeg",

                "webp",

            ],

            key="video_imagem_upload"

        )


        if imagem:

            st.image(

                imagem,

                caption="Imagem de referência",

                use_container_width=True

            )


        descricao = st.text_area(

            "📝 Descrição do vídeo",

            key="tool_prompt_video",

            height=130,

            placeholder=(

                "Exemplo: um personagem "
                "caminhando lentamente "
                "em uma rua cinematográfica..."

            )

        )


        # ====================================================
        # 🎬 BOTÃO
        # ====================================================

        if st.button(

            "🎬 Gerar vídeo",

            type="primary",

            use_container_width=True

        ):

            if not descricao.strip():

                st.warning(

                    "⚠️ Digite a descrição "
                    "do vídeo."

                )

                st.stop()


            # ------------------------------------------------
            # IMAGEM
            # ------------------------------------------------

            if imagem:

                imagem_bytes = (
                    imagem.getvalue()
                )

                nome_imagem = (
                    imagem.name
                )

            else:

                imagem_bytes = None

                nome_imagem = "imagem.png"


            # ------------------------------------------------
            # GERAR
            # ------------------------------------------------

            try:

                with st.spinner(

                    "🎬 Gerando vídeo... "
                    "aguarde o processamento."

                ):

                    resultado = gerar_video(

                        descricao=descricao,

                        imagem_bytes=imagem_bytes,

                        nome_imagem=nome_imagem,

                        duracao=duracao,

                        width=512,

                        height=512,

                        camera=camera,

                        proporcao=proporcao,

                    )


                # =================================================
                # VERIFICAR RESPOSTA
                # =================================================

                if resultado is None:

                    st.error(

                        "❌ O gerenciador de vídeo "
                        "não retornou nenhuma resposta."

                    )

                    st.stop()


                if not isinstance(
                    resultado,
                    dict
                ):

                    st.error(

                        "❌ O gerenciador de vídeo "
                        "retornou uma resposta inválida."

                    )

                    st.code(
                        str(resultado)
                    )

                    st.stop()


                caminho = resultado.get(
                    "video"
                )


                motor = resultado.get(

                    "motor",

                    "desconhecido"

                )


                sucesso = resultado.get(

                    "sucesso",

                    False

                )


                erro = resultado.get(
                    "erro"
                )


                # =================================================
                # SUCESSO
                # =================================================

                if sucesso and caminho:

                    caminho = str(
                        caminho
                    )


                    if not os.path.exists(
                        caminho
                    ):

                        st.error(

                            "❌ O motor informou "
                            "que criou o vídeo, "
                            "mas o arquivo não existe."

                        )

                        st.code(
                            caminho
                        )

                        st.stop()


                    st.success(

                        f"🎉 Vídeo gerado com sucesso!\n\n"
                        f"🎬 Motor: {motor}"

                    )


                    st.video(
                        caminho
                    )


                    st.session_state.mensagens.append({

                        "role":
                            "assistant",

                        "content":
                            (
                                "🎬 Vídeo criado "
                                f"com sucesso usando "
                                f"{motor}."
                            ),

                        "tipo":
                            "video",

                        "arquivo":
                            caminho,

                    })


                    st.session_state.ferramenta_ativa = None

                    st.rerun()


                # =================================================
                # FALHA
                # =================================================

                else:

                    st.error(
                        "❌ Nenhum vídeo foi gerado."
                    )


                    if erro:

                        st.warning(
                            "Detalhes do erro:"
                        )

                        st.code(
                            str(erro)
                        )


                    st.markdown(
                        "### 🔎 Resposta do gerenciador"
                    )


                    st.json(
                        resultado
                    )


            except Exception as erro_video:

                st.error(

                    "❌ O gerador de vídeo "
                    "encontrou um erro."

                )


                st.code(
                    str(erro_video)
                )


    # ========================================================
    # 🔊 VOZ
    # ========================================================

    elif ferramenta == "voz":

        st.session_state.usar_voz = st.checkbox(

            "🔊 Ler respostas da Alex em voz",

            value=st.session_state.usar_voz

        )


        st.info(
            "A voz será usada nas próximas respostas."
        )


    # ========================================================
    # 💻 CÓDIGO
    # ========================================================

    elif ferramenta == "codigo":

        st.selectbox(

            "Linguagem",

            listar_linguagens(),

            key="tool_linguagem_codigo"

        )


    # ========================================================
    # 📎 ARQUIVO
    # ========================================================

    elif ferramenta == "arquivo":

        arquivo = st.file_uploader(

            "📎 Enviar arquivo",

            type=[

                "pdf",

                "txt",

                "docx",

            ],

            key="tool_arquivo_upload"

        )


        if arquivo:

            if st.button(
                "📥 Ler arquivo"
            ):

                texto, erro = ler_arquivo(
                    arquivo
                )


                if erro:

                    st.error(
                        erro
                    )

                else:

                    st.session_state.arquivo_contexto = (
                        texto[:50000]
                    )

                    st.session_state.arquivo_nome = (
                        arquivo.name
                    )


                    st.success(
                        "✅ Arquivo carregado."
                    )


    # ========================================================
    # 🎭 PERSONAGEM
    # ========================================================

    elif ferramenta == "personagem":

        nomes = listar_personagens()


        escolhido = st.selectbox(

            "🎭 Personagem salvo",

            ["Nenhum"] + nomes,

            key="personagem_escolhido"

        )


        dados = (

            carregar_personagem(
                escolhido
            )

            if escolhido != "Nenhum"

            else None

        )


        nome = st.text_input(

            "Nome",

            value=(
                dados.get("nome", "")
                if dados else ""
            )

        )


        idade = st.text_input(

            "Idade",

            value=(
                dados.get("idade", "")
                if dados else ""
            )

        )


        aparencia = st.text_area(

            "Aparência",

            value=(
                dados.get("aparencia", "")
                if dados else ""
            )

        )


        roupa = st.text_input(

            "Roupa",

            value=(
                dados.get("roupa", "")
                if dados else ""
            )

        )


        personalidade = st.text_area(

            "Personalidade",

            value=(
                dados.get("personalidade", "")
                if dados else ""
            )

        )


        if st.button(
            "💾 Salvar personagem"
        ):

            if nome.strip():

                salvar_personagem(

                    nome,

                    idade,

                    aparencia,

                    roupa,

                    personalidade

                )


                st.session_state.personagem_atual = {

                    "nome":
                        nome,

                    "idade":
                        idade,

                    "aparencia":
                        aparencia,

                    "roupa":
                        roupa,

                    "personalidade":
                        personalidade,

                }


                st.success(
                    "✅ Personagem salvo."
                )


                st.rerun()


    # ========================================================
    # 🧠 MEMÓRIA
    # ========================================================

    elif ferramenta == "memoria":

        nova = st.text_area(

            "🧠 Salvar nova memória",

            key="memoria_nova"

        )


        if st.button(
            "💾 Salvar memória"
        ):

            if nova.strip():

                salvar_memoria(
                    nova.strip()
                )


                st.success(
                    "✅ Memória salva."
                )


                st.rerun()


    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# ============================================================
# 💬 CHAT PRINCIPAL
# ============================================================

pergunta = st.chat_input(

    "Digite sua mensagem para a Alex..."

)


# ============================================================
# 📩 PROCESSAR MENSAGEM
# ============================================================

if pergunta:

    pergunta = pergunta.strip()


    if not pergunta:

        st.stop()


    # --------------------------------------------------------
    # Salvar mensagem do usuário
    # --------------------------------------------------------

    st.session_state.mensagens.append({

        "role":
            "user",

        "content":
            pergunta,

    })


    low = pergunta.lower()


    # ========================================================
    # 🎬 COMANDO DE VÍDEO PELO CHAT
    # ========================================================

    if low.startswith(
        "video:"
    ):

        descricao = pergunta[
            6:
        ].strip()


        camera, proporcao, duracao = (
            "Sony FX6",
            "16:9",
            5
        )


        try:

            with st.chat_message(
                "assistant"
            ):

                with st.spinner(
                    "🎬 Gerando vídeo..."
                ):

                    resultado = gerar_video(

                        descricao=descricao,

                        camera=camera,

                        proporcao=proporcao,

                        duracao=duracao,

                        width=512,

                        height=512,

                    )


                if resultado.get(
                    "sucesso"
                ) and resultado.get(
                    "video"
                ):

                    caminho = resultado[
                        "video"
                    ]


                    st.success(

                        "🎬 Vídeo gerado com "
                        f"{resultado.get('motor')}"

                    )


                    st.video(
                        caminho
                    )


                    st.session_state.mensagens.append({

                        "role":
                            "assistant",

                        "content":
                            "🎬 Vídeo gerado com sucesso.",

                        "tipo":
                            "video",

                        "arquivo":
                            caminho,

                    })

                else:

                    st.error(
                        "❌ Não foi possível gerar o vídeo."
                    )

                    st.code(

                        str(
                            resultado.get(
                                "erro",
                                resultado
                            )
                        )

                    )


        except Exception as erro:

            st.error(
                "❌ Erro no gerador de vídeo."
            )

            st.code(
                str(erro)
            )


        st.stop()


    # ========================================================
    # 🧠 MEMORIZAR
    # ========================================================

    if low.startswith(
        "memorize:"
    ):

        texto_memoria = pergunta[
            len("memorize:")
        ].strip()


        if texto_memoria:

            salvar_memoria(
                texto_memoria
            )


        st.success(
            "🧠 Memória salva."
        )


        st.stop()


    # ========================================================
    # 📚 CONTEXTO
    # ========================================================

    contexto = "\n".join(

        f"{m['role']}: {m['content']}"

        for m in st.session_state.mensagens[-20:]

        if m.get("tipo")
        not in (
            "imagem",
            "video"
        )

    )


    # ========================================================
    # 🧠 INSTRUÇÃO
    # ========================================================

    instrucao = (

        f"{SYSTEM_PROMPT}\n\n"

        "Responda sempre em português "
        "do Brasil.\n\n"

        f"Histórico:\n{contexto}\n\n"

        f"Pergunta:\n{pergunta}"

    )


    # ========================================================
    # 🤖 GEMINI
    # ========================================================

    try:

        with st.chat_message(
            "assistant"
        ):

            with st.spinner(
                "🤖 Alex IA está pensando..."
            ):

                resposta = (
                    cliente.models.generate_content(

                        model=GEMINI_MODEL,

                        contents=instrucao

                    )
                )


                texto = (

                    resposta.text

                    if resposta.text

                    else

                    "Não consegui gerar "
                    "uma resposta."

                )


            st.write(
                texto
            )


            if st.session_state.usar_voz:

                mostrar_audio(
                    texto
                )


        st.session_state.mensagens.append({

            "role":
                "assistant",

            "content":
                texto,

        })


    except Exception as erro:

        st.error(

            "❌ Erro ao conversar "
            f"com o Gemini: {erro}"

         )
