"""Camada de acesso ao modelo de IA. Troque de provedor só mudando o .env."""
import json
import re

import httpx

from app.config import get_settings


class LLMError(Exception):
    """Falha ao obter uma resposta utilizável da IA."""


async def _call_anthropic(system: str, user: str) -> str:
    s = get_settings()
    if not s.anthropic_api_key:
        raise LLMError("ANTHROPIC_API_KEY não configurada.")
    async with httpx.AsyncClient(timeout=s.llm_timeout_seconds) as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": s.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": s.anthropic_model,
                "max_tokens": 600,
                "temperature": 0,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
    if r.status_code != 200:
        raise LLMError(f"Anthropic retornou {r.status_code}: {r.text[:200]}")
    blocks = r.json().get("content", [])
    return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")


async def _call_openai(system: str, user: str) -> str:
    s = get_settings()
    if not s.openai_api_key:
        raise LLMError("OPENAI_API_KEY não configurada.")
    async with httpx.AsyncClient(timeout=s.llm_timeout_seconds) as client:
        r = await client.post(
            f"{s.openai_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {s.openai_api_key}"},
            json={
                "model": s.openai_model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
    if r.status_code != 200:
        raise LLMError(f"Provedor OpenAI-compatível retornou {r.status_code}: {r.text[:200]}")
    return r.json()["choices"][0]["message"]["content"]


def _call_mock(user: str) -> str:
    """Classificador por palavras-chave: só para testes e demo sem chave de API."""
    m = re.search(r"<mensagem>(.*?)</mensagem>", user, re.S)
    texto = (m.group(1) if m else user).lower()

    def tem(*palavras):
        return any(p in texto for p in palavras)

    if tem("péssimo", "pessimo", "absurdo", "reclama", "demora", "não funciona", "nao funciona",
           "cobrado duas", "cobrança indevida", "cobranca indevida", "insatisfeit"):
        categoria, sentimento = "reclamacao", "negativo"
    elif tem("obrigad", "parabéns", "parabens", "excelente", "adorei"):
        categoria, sentimento = "elogio", "positivo"
    elif tem("segunda via", "2ª via", "cancelar", "cancelamento", "solicito", "preciso de",
             "gostaria de", "orçamento", "orcamento", "troca"):
        categoria, sentimento = "solicitacao", "neutro"
    elif tem("?", "como ", "quando ", "qual ", "quais ", "onde "):
        categoria, sentimento = "duvida", "neutro"
    else:
        categoria, sentimento = "outros", "neutro"

    if tem("boleto", "fatura", "cobran", "cobrado", "pagamento", "reembolso", "estorno"):
        setor = "Financeiro"
    elif tem("erro", "bug", "sistema", "senha", "login", "acesso", "app", "aplicativo"):
        setor = "Suporte Técnico"
    elif tem("preço", "preco", "orçamento", "orcamento", "plano", "contratar"):
        setor = "Comercial"
    elif categoria == "reclamacao":
        setor = "Qualidade"
    elif categoria == "outros":
        setor = "Outros"
    else:
        setor = "Atendimento"

    if tem("urgente", "imediat", "hoje", "processo", "procon", "advogado"):
        prioridade = "urgente"
    elif categoria == "reclamacao":
        prioridade = "alta"
    elif categoria == "solicitacao":
        prioridade = "media"
    else:
        prioridade = "baixa"

    resumo = (m.group(1) if m else user).strip().replace("\n", " ")[:120]
    return json.dumps(
        {
            "categoria": categoria,
            "prioridade": prioridade,
            "sentimento": sentimento,
            "setor_responsavel": setor,
            "resumo": resumo,
            "confianca": 0.6,
            "resposta_sugerida": "Olá! Recebemos sua mensagem e já a encaminhamos ao setor responsável.",
        },
        ensure_ascii=False,
    )


async def generate(system: str, user: str) -> str:
    provider = get_settings().llm_provider.lower()
    try:
        if provider == "anthropic":
            return await _call_anthropic(system, user)
        if provider == "openai":
            return await _call_openai(system, user)
        if provider == "mock":
            return _call_mock(user)
    except httpx.HTTPError as exc:
        raise LLMError(f"Erro de rede ao chamar a IA: {exc}") from exc
    raise LLMError(f"LLM_PROVIDER inválido: {provider!r}")


def extract_json(texto: str) -> dict:
    """Extrai o objeto JSON da resposta, mesmo se vier dentro de ```json ... ```."""
    limpo = re.sub(r"```(?:json)?", "", texto).strip()
    ini, fim = limpo.find("{"), limpo.rfind("}")
    if ini == -1 or fim == -1 or fim < ini:
        raise ValueError("Nenhum objeto JSON encontrado na resposta da IA.")
    return json.loads(limpo[ini : fim + 1])
