def gerar_imagem(prompt):

    api_key = obter_api_key()

    if not api_key:
        raise RuntimeError(
            "FLUXPOOL_API_KEY não foi encontrada "
            "nos Secrets do Streamlit."
        )

    try:
        from openai import OpenAI
    except Exception as erro:
        raise RuntimeError(
            "A biblioteca openai não está instalada. "
            f"Detalhes: {erro}"
        )

    try:

        cliente = OpenAI(
            base_url=BASE_URL,
            api_key=api_key,
            default_headers={
                "Authorization": f"Bearer {api_key}"
            },
        )

        resposta = cliente.images.generate(
            model=MODELO,
            prompt=prompt.strip(),
            size="1024x1024",
            n=1,
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro na geração pela Fluxpool: {erro}"
        )

    if not resposta:
        raise RuntimeError(
            "A Fluxpool não retornou uma resposta."
        )

    if not resposta.data:
        raise RuntimeError(
            "A Fluxpool não retornou nenhuma imagem."
        )

    imagem_url = resposta.data[0].url

    if not imagem_url:
        raise RuntimeError(
            "A Fluxpool não retornou a URL da imagem."
        )

    try:

        import requests

        imagem = requests.get(
            imagem_url,
            timeout=120,
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro ao baixar a imagem: {erro}"
        )

    if imagem.status_code != 200:
        raise RuntimeError(
            "Não foi possível baixar a imagem. "
            f"HTTP {imagem.status_code}"
        )

    caminho = (
        obter_pasta()
        / "teste_fluxpool.png"
    )

    try:

        caminho.write_bytes(
            imagem.content
        )

    except Exception as erro:

        raise RuntimeError(
            f"Erro ao salvar a imagem: {erro}"
        )

    return str(caminho)
