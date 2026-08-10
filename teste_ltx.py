import requests
import json
import time

# ============================================================
# 🎬 TESTE DA API LTX-2.3
# Alex IA Ultra
# ============================================================

BASE_URL = "https://lightricks-ltx-2-3.hf.space"

PROMPT = """
Uma bola vermelha rolando lentamente sobre uma mesa de madeira,
iluminação cinematográfica, movimento suave de câmera.
"""

print("🎬 Iniciando teste do LTX-2.3...")
print("⏳ Enviando solicitação...")

# ------------------------------------------------------------
# 1. Enviar pedido para o LTX-2.3
# ------------------------------------------------------------

url = f"{BASE_URL}/gradio_api/call/generate_video"

dados = {
    "data": [
        None,       # input_image
        PROMPT,     # prompt
        1.0,        # duration
        True,       # enhance_prompt
        0,          # seed
        True,       # randomize_seed
        512,        # height
        512         # width
    ]
}

try:
    resposta = requests.post(
        url,
        json=dados,
        timeout=60
    )

    print("📡 Status:", resposta.status_code)
    print("📨 Resposta inicial:")
    print(resposta.text)

    if resposta.status_code != 200:
        print("❌ O LTX-2.3 recusou a solicitação.")
        raise SystemExit

    resultado = resposta.json()

    event_id = resultado.get("event_id")

    if not event_id:
        print("❌ Não encontramos o event_id.")
        print(resultado)
        raise SystemExit

    print()
    print("✅ Solicitação aceita!")
    print("🆔 Event ID:", event_id)

except Exception as erro:
    print()
    print("❌ Erro ao enviar a solicitação:")
    print(erro)
    raise SystemExit


# ------------------------------------------------------------
# 2. Acompanhar a geração
# ------------------------------------------------------------

url_evento = f"{BASE_URL}/gradio_api/call/generate_video/{event_id}"

print()
print("🎥 O LTX-2.3 está gerando o vídeo...")
print("⏳ Aguarde...")

try:
    with requests.get(
        url_evento,
        stream=True,
        timeout=300
    ) as resposta_evento:

        print("📡 Status do acompanhamento:", resposta_evento.status_code)

        if resposta_evento.status_code != 200:
            print("❌ Erro ao acompanhar a geração.")
            print(resposta_evento.text)
            raise SystemExit

        for linha in resposta_evento.iter_lines():

            if not linha:
                continue

            texto = linha.decode("utf-8")

            print("📨", texto)

            # O Gradio envia eventos no formato:
            # event: complete
            # data: {...}

            if texto.startswith("data:"):

                dados_resultado = texto[5:].strip()

                try:
                    resultado_final = json.loads(dados_resultado)

                    print()
                    print("🎉 RESULTADO RECEBIDO!")
                    print(resultado_final)

                    # ------------------------------------------------
                    # Procurar o arquivo retornado pelo LTX
                    # ------------------------------------------------

                    if isinstance(resultado_final, list):

                        for item in resultado_final:

                            if isinstance(item, dict):

                                caminho = item.get("path")
                                url_video = item.get("url")

                                if caminho:
                                    print()
                                    print("🎬 Caminho do vídeo:")
                                    print(caminho)

                                if url_video:
                                    print()
                                    print("🔗 URL do vídeo:")
                                    print(url_video)

                    break

                except json.JSONDecodeError:
                    pass

except Exception as erro:
    print()
    print("❌ Erro durante a geração:")
    print(erro)


print()
print("============================================================")
print("🏁 TESTE FINALIZADO")
print("============================================================")
