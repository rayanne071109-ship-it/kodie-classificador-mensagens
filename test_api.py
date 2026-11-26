import json

import pytest
from fastapi.testclient import TestClient

from app import ai_client
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_classifica_reclamacao_financeira():
    r = client.post(
        "/classify",
        json={"mensagem": "Fui cobrado duas vezes no cartão, quero estorno hoje!", "cliente": "Ana"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["categoria"] == "reclamacao"
    assert body["setor_responsavel"] == "Financeiro"
    assert body["prioridade"] == "urgente"
    assert body["cliente"] == "Ana"


def test_classifica_duvida():
    r = client.post("/classify", json={"mensagem": "Qual o horário de funcionamento?"})
    assert r.status_code == 200
    assert r.json()["categoria"] == "duvida"


def test_mensagem_vazia_retorna_422():
    assert client.post("/classify", json={"mensagem": ""}).status_code == 422


def test_extract_json_com_markdown():
    assert ai_client.extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_ia_com_resposta_invalida_retorna_502(monkeypatch):
    async def lixo(system, user):
        return "não sei responder"

    monkeypatch.setattr(ai_client, "generate", lixo)
    assert client.post("/classify", json={"mensagem": "Olá, tudo bem?"}).status_code == 502


def test_retry_corrige_resposta_invalida(monkeypatch):
    chamadas = {"n": 0}
    valido = json.dumps(
        {
            "categoria": "Dúvida",  # acento/maiúscula são normalizados
            "prioridade": "baixa",
            "sentimento": "neutro",
            "setor_responsavel": "atendimento",
            "resumo": "Pergunta geral.",
            "confianca": 0.9,
            "resposta_sugerida": "Olá!",
        }
    )

    async def falha_e_depois_ok(system, user):
        chamadas["n"] += 1
        return "texto solto" if chamadas["n"] == 1 else valido

    monkeypatch.setattr(ai_client, "generate", falha_e_depois_ok)
    r = client.post("/classify", json={"mensagem": "Como funciona o plano?"})
    assert r.status_code == 200
    assert r.json()["categoria"] == "duvida"
    assert r.json()["setor_responsavel"] == "Atendimento"
    assert chamadas["n"] == 2
