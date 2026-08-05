Alex IA Ultra V3 - Arquivos
→ Leitura de PDF/TXT ando.


importar streamlit como st
do Openai Import OpenAI.
importar PyPDF2

st. set_page_config(
page_title="🤖 Alex IA Ultra",
page_icon="🤖",
layout="wide"
)

st. título("🤖 Alex IA Ultra")
st. legenda("Sua inteligência artificial)

api_key = st. text_input(
"Digite sua chave do OpenRouter:",
tipo="password"
)

se api_key:

 experimente:
Cliente = OpenAI(
pi_key=api_key,
base_url="https://openrouter.ai/api/v1"
)

 se "mensagens" não em st. session_state:
 st. session_state. @NOTRANSLATE =
 {
"role": "system",
"conteúdo": "Você é um Alex IA Ultra, uma inteligência artificial avançada criada por Geovani. Responda sempre em português de forma inteligente. "
}
@FBENTITY

 se "arquivo_texto" não em st. session_state:
 st. session_state. Arquivo_texto = ""

# Área de Arquivos
 st. barra lateral. título("📄 Arquivos")

Arquivo = st. barra lateral. file_uploader(
"Envie um Arquivo",
tipo=["txt", "pdf"]
)

Arquivo:

Arquivo. tipo == "Texto/plano":
 st. session_state. Arquivo_texto = Arquivo. ler(). descodificar("utf-8)

 Elif Arquivo. tipo == "Candidatura/PDF":

Leitor = PyPDF2. PdfReader (arquivo)

 texto = ""

Pela pagina em leitor. páginas:
 texto += pagina. extract_text() ou ""

 st. session_state. Arquivo_texto = texto

 st. barra lateral. sucesso("Arquivo carreado com sucesso! ")

 se st. barra lateral. botão("🗑️ Limpar conversa"):
 st. session_state. @NOTRANSLATE =
 {
"role": "system",
"conteúdo": "Você é um Alex IA Ultra, uma inteligência artificial avançada criada por Geovani. "
}
@FBENTITY
 st. session_state. Arquivo_texto = ""
 st. repetição()

# Mostrar
@FBENTITY em St. session_state. automaticamente

["role"] ! = "sistema":

 com st. chat_mensage(mensagem["role"]):
 st. escrever(mensagem["conteúdo])

pergunta = st. chat_input(
"Converse com a Alex IA Ultra... "
)

 se perguntar:

contexto = ""

 se st. session_state. Arquivo_texto:

contexto = f"""

Use este Arquivo como base para socorros:

{st. session_state. Arquivo_texto}

""

 st. session_state. xícara. apend(
 {
"role": "utilizador",
"conteúdo": pergunta + contexto
}
)

 com st. chat_mensage("utilizador"):
 st. escrever(pergunta)

resposta = cliente. chat. finalizações criar(
model="openrouter/livre",
 mensagens=st. session_state. automaticamente
)

 texto_reposta = resposta escolhas[0]. mensagem. conteúdos

 st. session_state. xícara. apend(
 {
"controlo": "assistente",
"conteúdo": texto_resposta
}
)

 com st. chat_mensage("assistente"):
 st. escrever(texto_resposta)

Excepto Exceção como e:
 st. erro(f"Erro: {e})
