import logging

from fastapi import FastAPI, HTTPException

from app.ai_client import LLMError
from app.classifier import classify_message
from app.config import get_settings
from app.schemas import ClassificacaoOut, MensagemIn

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Classificador de Mensagens com IA",
    description="Recebe uma mensagem de cliente, classifica com IA e devolve JSON estruturado.",
    version="1.0.0",
)


@app.get("/health")
async def health():
    return {"status": "ok", "provider": get_settings().llm_provider}


@app.post("/classify", response_model=ClassificacaoOut)
async def classify(payload: MensagemIn):
    try:
        resultado = await classify_message(payload.mensagem)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ClassificacaoOut(
        **resultado.model_dump(), cliente=payload.cliente, canal=payload.canal
    )
