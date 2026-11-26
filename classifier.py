import logging

from pydantic import ValidationError

from app import ai_client
from app.config import get_settings
from app.prompts import RETRY_REMINDER, SYSTEM_PROMPT, USER_TEMPLATE
from app.schemas import ClassificacaoIA

log = logging.getLogger("classifier")


async def classify_message(mensagem: str) -> ClassificacaoIA:
    """Chama a IA, valida o JSON com Pydantic e tenta de novo se vier inválido."""
    user_prompt = USER_TEMPLATE.format(mensagem=mensagem)
    tentativas = 1 + max(0, get_settings().llm_max_retries)
    ultimo_erro = "desconhecido"

    for n in range(1, tentativas + 1):
        prompt = user_prompt if n == 1 else user_prompt + RETRY_REMINDER
        raw = await ai_client.generate(SYSTEM_PROMPT, prompt)
        try:
            return ClassificacaoIA.model_validate(ai_client.extract_json(raw))
        except (ValueError, ValidationError) as exc:
            ultimo_erro = str(exc)
            log.warning("Resposta inválida da IA (tentativa %s/%s): %s", n, tentativas, exc)

    raise ai_client.LLMError(f"A IA não retornou um JSON válido: {ultimo_erro[:200]}")
