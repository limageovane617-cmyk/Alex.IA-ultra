from openai import OpenAI

# Inicialize o cliente com sua chave
client = OpenAI(api_key="SUA_CHAVE_AQUI")

def gerar_imagem(prompt_descricao):
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt_descricao,
            n=1,
            size="1024x1024"
        )

        image_url = response.data[0].url
        print(f"Imagem gerada com sucesso! Acesse aqui: {image_url}")
        return image_url
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

# Exemplo de uso
prompt = "Um robô futurista elegante estudando tecnologia em um ambiente minimalista"
gerar_imagem(prompt)
