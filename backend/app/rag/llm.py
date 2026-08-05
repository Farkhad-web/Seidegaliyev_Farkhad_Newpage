"""Anthropic Claude client — one call to condense a follow-up question, one
streaming call for the grounded answer. Condensing uses Haiku (cheap, low
stakes); the actual answer uses Sonnet, where quality matters."""
from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic

from app.config import get_settings
from app.rag.prompts import CONDENSE_SYSTEM_PROMPT

_client: AsyncAnthropic | None = None


def get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=get_settings().anthropic_api_key)
    return _client


async def condense_question(history_text: str, question: str) -> str:
    if not history_text.strip():
        return question
    settings = get_settings()
    response = await get_client().messages.create(
        model=settings.condense_model,
        max_tokens=200,
        temperature=0,
        system=CONDENSE_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Chat history:\n{history_text}\n\nFollow-up question: {question}",
            }
        ],
    )
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    return text or question


async def stream_answer(
    system_prompt: str,
    history: list[tuple[str, str]],
    question: str,
) -> AsyncIterator[dict]:
    """Yields {"type": "delta", "text": ...} chunks, then a final
    {"type": "usage", "input_tokens": ..., "output_tokens": ...}."""
    settings = get_settings()
    messages = [{"role": role, "content": content} for role, content in history]
    messages.append({"role": "user", "content": question})

    async with get_client().messages.stream(
        model=settings.anthropic_model,
        max_tokens=settings.llm_max_tokens,
        temperature=settings.llm_temperature,
        system=system_prompt,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield {"type": "delta", "text": text}
        final = await stream.get_final_message()
        yield {
            "type": "usage",
            "input_tokens": final.usage.input_tokens,
            "output_tokens": final.usage.output_tokens,
        }
