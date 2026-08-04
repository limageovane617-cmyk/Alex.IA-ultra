importar streamlit como st
do Openai Import OpenAI.

st. set_page_config(
page_title="🤖 Alex IA Ultra",
page_icon="🤖",
layout="wide"
)

st. título("🤖 Alex IA Ultra")
st. escrever("Sua inteligência avançada artificial")

experimente:
pi_key = st. Segredos["OPENROUTER_API_KEY"]

Cliente = OpenAI(
pi_key=api_key,
base_url="https://openrouter.ai/api/v1"
)

 se "mensagens" não em st. session_state:
 st. session_state. @NOTRANSLATE =
 {
"role": "system",
"conteúdo": "Você é um Alex IA Ultra, uma inteligência artificial avançada criada por Geovani. Responda sempre em portugueses de forma intransitável. "
}
@FBENTITY

@FBENTITY em St. session_state. automaticamente
["role"] ! = "sistema":
 com st. chat_mensage(mensagem["role"]):
 st. escrever(mensagem["conteúdo])

pergunta = st. chat_input("Converse com Alex IA Ultra... ")

 se perguntar:

 st. session_state. xícara. apend(
 {
"role": "utilizador",
"conteúdo": pergunta
}
)

 com st. chat_mensage("utilizador"):
 st. escrever(pergunta)

resposta = cliente. chat. finalizações criar(
model="openrouter/livre",
 mensagens=st. session_state. automaticamente
)

 texto = resposta. escolhas[0]. mensagem. conteúdos

 st. session_state. xícara. apend(
 {
"controlo": "assistente",
"conteúdo": texto
}
)

 com st. chat_mensage("assistente"):
 st. escrever(texto)

Exceção como e:
 st. erro(f"Erro: {e})
