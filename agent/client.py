from openai import OpenAI


def get_ollama_client(config: dict) -> tuple[OpenAI, str]:
    """Returns the Ollama client and model name."""
    client = OpenAI(
        base_url=config["agent"]["ollama_url"],
        api_key="ollama" # Ollama does not need a real key
    )
    model = config["agent"]["model"]
    return client, model