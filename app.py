# ============================================================
# 🤖 ALEX IA ULTRA — aplicativo principal
# ============================================================
import base64
import os
import re
import sys
import importlib
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Alex IA Ultra", page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")

if "gerenciador_imagem" in sys.modules:
    importlib.reload(sys.modules["gerenciador_imagem"])
else:
    import gerenciador_imagem
from gerenciador_imagem import mostrar_imagem
from config_ultra import SYSTEM_PROMPT, GEMINI_MODEL, AI_NAME, CREATOR_NAME
from servicos import criar_cliente_gemini, verificar_servicos
from memoria import salvar_memoria, carregar_memorias, apagar_memoria, apagar_todas_memorias
from personagens import salvar_personagem, carregar_personagem, listar_personagens, apagar_personagem
from voz import mostrar_audio
from video import gerar_video, mostrar_configuracao_video, verificar_magic_hour
from arquivos import ler_arquivo
from codigo import preparar_pedido_codigo, listar_linguagens

DEFAULTS = {"mensagens": [], "personagem_atual": None, "arquivo_contexto": "", "arquivo_nome": "", "ferramenta_ativa": None, "usar_voz": False, "ultima_imagem_caminho": None}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

servicos = verificar_servicos()
if not servicos.get("gemini"):
    st.error("🔐 A chave GEMINI_API_KEY não está configurada nos Secrets do Streamlit.")
    st.stop()
cliente = criar_cliente_gemini()
if cliente is None:
    st.error("❌ Não foi possível criar a conexão com o Gemini.")
    st.stop()


def imagem_fundo_css():
    caminho = Path(__file__).with_name("fundo_chat.jpg")
    if not caminho.exists():
        return ""
    try:
        dados = base64.b64encode(caminho.read_bytes()).decode("utf-8")
        return f"background-image:url(data:image/jpeg;base64,{dados});"
    except Exception:
        return ""

st.markdown(f"""<style>
.stApp {{{imagem_fundo_css()} background-size:cover;background-position:center;background-attachment:fixed;}}
.stApp::before {{content:"";position:fixed;inset:0;background:rgba(2,8,16,.68);z-index:-1;pointer-events:none;}}
.main .block-container {{max-width:980px;padding-top:1.2rem;padding-bottom:8rem;}}
.ultra-header {{text-align:center;margin:0 auto 1.2rem;padding:.65rem 1rem;border-radius:22px;background:rgba(4,15,28,.58);border:1px solid rgba(120,200,255,.16);backdrop-filter:blur(14px);}}
.ultra-name {{font-size:clamp(25px,5vw,39px);font-weight:800;}}
.ultra-subtitle {{color:rgba(235,245,255,.72);font-size:13px;}}
.tool-panel {{margin:0 auto .65rem;padding:.75rem;border-radius:22px;background:rgba(8,17,29,.92);border:1px solid rgba(130,210,255,.16);}}
</style>""", unsafe_allow_html=True)

st.markdown(f'<div class="ultra-header"><div class="ultra-name">🤖 {AI_NAME}</div><div class="ultra-subtitle">Criada por {CREATOR_NAME} • inteligência artificial pessoal</div></div>', unsafe_allow_html=True)

for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem.get("role", "assistant")):
        tipo = mensagem.get("tipo", "texto")
        if tipo == "imagem" and mensagem.get("arquivo") and os.path.exists(mensagem["arquivo"]):
            st.image(mensagem["arquivo"], use_container_width=True)
        elif tipo == "video" and mensagem.get("arquivo") and os.path.exists(mensagem["arquivo"]):
            st.video(mensagem["arquivo"])
        st.write(mensagem.get("content", ""))

with st.popover("＋"):
    st.markdown("### 🧰 Ferramentas da Ultra")
    for nome, rotulo in [("imagem","🖼️ Imagem"),("video","🎬 Vídeo"),("voz","🔊 Voz"),("codigo","💻 Código"),("arquivo","📎 Arquivo"),("personagem","🎭 Personagem"),("memoria","🧠 Memória")]:
        if st.button(rotulo, use_container_width=True):
            st.session_state.ferramenta_ativa = nome
            st.rerun()
    if st.button("🗑️ Limpar chat", use_container_width=True):
        st.session_state.mensagens = []
        st.rerun()

ferramenta = st.session_state.ferramenta_ativa
if ferramenta:
    st.markdown('<div class="tool-panel">', unsafe_allow_html=True)
    if st.button("✕ Fechar ferramenta"):
        st.session_state.ferramenta_ativa = None
        st.rerun()

    if ferramenta == "imagem":
        p = st.text_area("Prompt da imagem", key="tool_prompt_imagem", height=100)
        if st.button("🖼️ Gerar imagem", type="primary"):
            if not p.strip(): st.warning("Digite o que você quer na imagem.")
            else:
                with st.spinner("🖼️ Criando imagem..."): sucesso = mostrar_imagem(p.strip())
                if sucesso:
                    st.session_state.mensagens.append({"role":"assistant","content":"🖼️ Imagem criada.","tipo":"imagem","arquivo":st.session_state.get("ultima_imagem_caminho")})
                    st.session_state.ferramenta_ativa=None
                    st.rerun()

    elif ferramenta == "video":
        camera, proporcao, duracao = mostrar_configuracao_video()
        imagem = st.file_uploader("📤 Imagem de referência (opcional)", type=["png","jpg","jpeg","webp"], key="video_imagem_upload")
        if imagem: st.image(imagem, use_container_width=True)
        descricao = st.text_area("📝 Descrição do vídeo", key="tool_prompt_video", height=130)
        if st.button("🎬 Gerar vídeo", type="primary"):
            if not descricao.strip():
                st.warning("Digite a descrição do vídeo.")
            else:
                imagem_bytes = imagem.getvalue() if imagem else None
                try:
                    with st.spinner("🎬 Gerando seu vídeo..."):
                        resultado = gerar_video(prompt=descricao, imagem_bytes=imagem_bytes, nome_imagem=imagem.name if imagem else "imagem.png", duracao=duracao, width=1536, height=1024, camera=camera, proporcao=proporcao)
                    caminho = resultado.get("video")
                    if caminho:
                        st.success(f"🎉 Vídeo gerado! Motor: {resultado.get('motor')}")
                        st.video(caminho)
                        st.session_state.mensagens.append({"role":"assistant","content":"🎬 Vídeo criado com sucesso.","tipo":"video","arquivo":caminho})
                        st.session_state.ferramenta_ativa=None
                        st.rerun()
                except Exception as erro:
                    st.error("❌ Não foi possível gerar o vídeo.")
                    st.code(str(erro))

    elif ferramenta == "voz":
        st.session_state.usar_voz = st.checkbox("🔊 Ler respostas da Alex em voz", value=st.session_state.usar_voz)
        st.info("A voz será usada nas próximas respostas.")
    elif ferramenta == "codigo":
        st.selectbox("Linguagem", listar_linguagens(), key="tool_linguagem_codigo")
    elif ferramenta == "arquivo":
        arquivo = st.file_uploader("Enviar arquivo", type=["pdf","txt","docx"], key="tool_arquivo_upload")
        if arquivo and st.button("📥 Ler arquivo"):
            texto, erro = ler_arquivo(arquivo)
            if erro: st.error(erro)
            else:
                st.session_state.arquivo_contexto=texto[:50000]; st.session_state.arquivo_nome=arquivo.name; st.success("✅ Arquivo carregado.")
    elif ferramenta == "personagem":
        nomes=listar_personagens(); escolhido=st.selectbox("Personagem salvo",["Nenhum"]+nomes,key="personagem_escolhido")
        dados=carregar_personagem(escolhido) if escolhido!="Nenhum" else None
        nome=st.text_input("Nome",value=dados.get("nome","") if dados else "")
        idade=st.text_input("Idade",value=dados.get("idade","") if dados else "")
        aparencia=st.text_area("Aparência",value=dados.get("aparencia","") if dados else "")
        roupa=st.text_input("Roupa",value=dados.get("roupa","") if dados else "")
        personalidade=st.text_area("Personalidade",value=dados.get("personalidade","") if dados else "")
        if st.button("💾 Salvar personagem") and nome.strip():
            salvar_personagem(nome,idade,aparencia,roupa,personalidade); st.session_state.personagem_atual={"nome":nome,"idade":idade,"aparencia":aparencia,"roupa":roupa,"personalidade":personalidade}; st.rerun()
    elif ferramenta == "memoria":
        nova=st.text_area("Salvar nova memória",key="memoria_nova")
        if st.button("💾 Salvar memória") and nova.strip(): salvar_memoria(nova.strip()); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

pergunta = st.chat_input("Digite sua mensagem para a Alex...")
if pergunta:
    pergunta=pergunta.strip()
    if not pergunta: st.stop()
    st.session_state.mensagens.append({"role":"user","content":pergunta})
    low=pergunta.lower()

    if low.startswith("video:"):
        descricao=pergunta[6:].strip()
        camera, proporcao, duracao=mostrar_configuracao_video()
        try:
            with st.chat_message("assistant"), st.spinner("🎬 Gerando seu vídeo..."):
                resultado=gerar_video(descricao=descricao,camera=camera,proporcao=proporcao,duracao=duracao)
                caminho=resultado.get("video")
                if caminho: st.video(caminho); st.success(f"🎬 Vídeo gerado com {resultado.get('motor')}")
            if caminho: st.session_state.mensagens.append({"role":"assistant","content":"🎬 Vídeo gerado com sucesso.","tipo":"video","arquivo":caminho})
        except Exception as erro:
            st.session_state.mensagens.append({"role":"assistant","content":f"❌ Não foi possível gerar o vídeo.\n\n{erro}"}); st.error(str(erro))
        st.rerun()

    if low.startswith("memorize:"):
        salvar_memoria(pergunta[len("memorize:"):].strip()); st.rerun()

    contexto = "\n".join(f"{m['role']}: {m['content']}" for m in st.session_state.mensagens[-20:] if m.get("tipo") not in ("imagem","video"))
    instrucao=f"{SYSTEM_PROMPT}\n\nResponda sempre em português do Brasil.\n\nHistórico:\n{contexto}\n\nPergunta:\n{pergunta}"
    try:
        with st.chat_message("assistant"):
            with st.spinner("🤖 Alex IA está pensando..."):
                resposta=cliente.models.generate_content(model=GEMINI_MODEL,contents=instrucao)
                texto=resposta.text if resposta.text else "Não consegui gerar uma resposta."
            st.write(texto)
            if st.session_state.usar_voz: mostrar_audio(texto)
        st.session_state.mensagens.append({"role":"assistant","content":texto})
    except Exception as erro:
        st.error(f"❌ Erro ao conversar com o Gemini: {erro}")
