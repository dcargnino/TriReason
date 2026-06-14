# Shared LLM client for all agents.

from openai import AsyncOpenAI

from trireason.config import settings

_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    """Return a singleton AsyncOpenAI client."""
    global _client
    if _client is None:
        kwargs = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        _client = AsyncOpenAI(**kwargs)
    return _client


async def chat_json(system: str, user: str, *, model: str | None = None) -> str:
    """Send a chat completion request and return the assistant message content.

    The caller is responsible for parsing the JSON from the returned string.
    """
    client = get_openai_client()
    response = await client.chat.completions.create(
        model=model or settings.openai_model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.7,
    )
    content = response.choices[0].message.content
    if content is None:
        raise RuntimeError("LLM returned empty response")
    return content
