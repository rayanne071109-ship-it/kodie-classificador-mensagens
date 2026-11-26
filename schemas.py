import unicodedata
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

Categoria = Literal["duvida", "reclamacao", "solicitacao", "elogio", "outros"]
Prioridade = Literal["baixa", "media", "alta", "urgente"]
Sentimento = Literal["positivo", "neutro", "negativo"]
Setor = Literal[
    "Atendimento", "Financeiro", "Suporte Técnico", "Comercial", "Qualidade", "Outros"
]

SETORES = ["Atendimento", "Financeiro", "Suporte Técnico", "Comercial", "Qualidade", "Outros"]


def _normalizar(texto: str) -> str:
    """minúsculas e sem acento: 'Dúvida' -> 'duvida'."""
    sem_acento = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return sem_acento.strip().lower()


class MensagemIn(BaseModel):
    """Corpo da requisição enviada pelo n8n (ou por qualquer cliente)."""

    mensagem: str = Field(..., min_length=3, max_length=4000, description="Texto do cliente")
    cliente: Optional[str] = Field(None, max_length=120)
    canal: Optional[str] = Field(None, max_length=50, description="email, whatsapp, site...")


class ClassificacaoIA(BaseModel):
    """Contrato que a resposta da IA precisa respeitar (validado com Pydantic)."""

    categoria: Categoria
    prioridade: Prioridade
    sentimento: Sentimento
    setor_responsavel: Setor
    resumo: str = Field(..., min_length=1, max_length=300)
    confianca: float = Field(..., ge=0, le=1)
    resposta_sugerida: str = Field(..., min_length=1, max_length=800)

    @field_validator("categoria", "prioridade", "sentimento", mode="before")
    @classmethod
    def _normaliza_enums(cls, v):
        return _normalizar(v)

    @field_validator("setor_responsavel", mode="before")
    @classmethod
    def _normaliza_setor(cls, v):
        for setor in SETORES:
            if _normalizar(setor) == _normalizar(v):
                return setor
        return v


class ClassificacaoOut(ClassificacaoIA):
    cliente: Optional[str] = None
    canal: Optional[str] = None
