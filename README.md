# 📨 Classificador de Mensagens com IA + n8n

Desafio Técnico **KODIE — IA e Automação** · Caso escolhido: **4.1 — Classificação de Mensagens**

API em **FastAPI** que usa um modelo de **IA** para classificar mensagens de clientes e devolve **JSON estruturado**; um fluxo no **n8n** recebe a mensagem, chama a API e encaminha para a fila/setor correto.

```
Cliente ──► Webhook (n8n) ──► Edit Fields ──► HTTP Request ──► API FastAPI ──► Modelo de IA
                                                                     │
                                  Respond to Webhook ◄── Encaminhar ◄── Switch (categoria)
```

---

## 1. Apresentação da Ideia

Em muitas empresas pequenas, o atendimento começa com alguém lendo cada mensagem, descobrindo o assunto e repassando manualmente ao setor certo. É um trabalho repetitivo, sujeito a erro e que atrasa a resposta ao cliente. A ideia foi automatizar exatamente essa triagem: a IA **interpreta** a mensagem e a automação **age** a partir da interpretação.

## 2. Problema Escolhido

**Caso 4.1 — Classificação de Mensagens.** Uma empresa recebe dúvidas, solicitações e reclamações sem processo organizado para identificar o assunto. A solução classifica cada mensagem automaticamente e a encaminha ao responsável.

## 3. Solução Proposta

Para cada mensagem, a IA extrai:

| Campo | Valores |
|---|---|
| `categoria` | `duvida`, `reclamacao`, `solicitacao`, `elogio`, `outros` |
| `prioridade` | `baixa`, `media`, `alta`, `urgente` |
| `sentimento` | `positivo`, `neutro`, `negativo` |
| `setor_responsavel` | Atendimento, Financeiro, Suporte Técnico, Comercial, Qualidade, Outros |
| `resumo` | resumo objetivo da mensagem |
| `confianca` | 0 a 1 |
| `resposta_sugerida` | rascunho de resposta ao cliente |

**Papel da IA:** interpretar texto livre, decidir categoria/prioridade/setor e redigir o resumo e a resposta sugerida.
**Papel da automação (n8n):** receber a mensagem, acionar a API e rotear o resultado (Switch por categoria), sinalizando casos de prioridade alta/urgente.

**Como garantimos o formato da resposta da IA:**
- prompt estruturado com regras, critérios, esquema JSON e exemplos (*few-shot*);
- `temperature = 0` para respostas consistentes;
- validação com **Pydantic** (valores fora do permitido são rejeitados; acentos/maiúsculas são normalizados);
- extração tolerante de JSON (aceita resposta dentro de ```` ```json ````);
- **uma nova tentativa automática** se o JSON vier inválido; se persistir, a API responde `502`;
- a mensagem do cliente vai dentro de `<mensagem>…</mensagem>` e o prompt instrui a IA a tratá-la como dado (mitigação básica de *prompt injection*).

## 4. Tecnologias Utilizadas

- **Python 3.12** + **FastAPI** + Uvicorn
- **Pydantic** (validação) e **httpx** (chamadas à IA)
- **IA:** Anthropic (Claude) por padrão; também aceita qualquer API compatível com OpenAI (OpenAI, Groq, Gemini, OpenRouter, Ollama…) via `.env`
- **n8n** (automação)
- **Docker / Docker Compose** (opcional)
- **pytest** (testes)

## 5. Funcionamento do Sistema

1. **Entrada:** um cliente (ou qualquer sistema) envia `POST` para o webhook do n8n com `mensagem`, `cliente` e `canal`.
2. **n8n — Edit Fields:** padroniza os campos e define a URL da API (`api_url`).
3. **n8n — HTTP Request:** chama `POST /classify` da API FastAPI (com 2 tentativas em caso de falha).
4. **API — `/classify`:** valida a entrada, monta o prompt, chama o modelo de IA, valida o JSON de retorno e responde.
5. **n8n — Switch:** roteia pela `categoria` (Dúvida, Reclamação, Solicitação, Elogio ou Outros).
6. **n8n — Encaminhar:** adiciona `fila_destino`, `status = encaminhado` e `alerta_urgente` (verdadeiro se prioridade alta/urgente).
7. **n8n — Respond to Webhook:** devolve o resultado final em JSON.

### Endpoints da API

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Verifica se a API está no ar |
| POST | `/classify` | Classifica uma mensagem |
| GET | `/docs` | Swagger (documentação interativa) |

**Requisição**
```json
{ "mensagem": "Fui cobrado duas vezes no cartão e quero o estorno hoje!", "cliente": "Ana Souza", "canal": "email" }
```

**Resposta (exemplo)**
```json
{
  "categoria": "reclamacao",
  "prioridade": "urgente",
  "sentimento": "negativo",
  "setor_responsavel": "Financeiro",
  "resumo": "Cliente cobrado em duplicidade no cartão e exige estorno hoje.",
  "confianca": 0.96,
  "resposta_sugerida": "Sentimos muito pelo transtorno. Já encaminhamos ao financeiro para análise e estorno com prioridade.",
  "cliente": "Ana Souza",
  "canal": "email"
}
```

### Estrutura do repositório

```
├── app/
│   ├── main.py          # rotas FastAPI
│   ├── classifier.py    # orquestra IA + validação + retry
│   ├── ai_client.py     # chamadas à IA (anthropic / openai / mock)
│   ├── prompts.py       # prompt estruturado
│   ├── schemas.py       # contratos Pydantic
│   └── config.py        # variáveis de ambiente
├── n8n/workflow.json    # fluxo exportado do n8n
├── docs/                # documentação visual (prints) do fluxo
├── examples/            # mensagens de exemplo
├── scripts/             # script para testar o fluxo
├── tests/               # testes automatizados
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

## 6. Como Executar

### Pré-requisitos
- Docker + Docker Compose **ou** Python 3.11+ e n8n (`npx n8n`)
- Uma chave de API de IA (ou use `LLM_PROVIDER=mock` para testar sem chave)

### Opção A — Docker Compose (recomendada)

```bash
git clone <URL-DO-SEU-REPOSITORIO>
cd <pasta-do-repositorio>

cp .env.example .env        # edite e coloque sua chave de API
docker compose up --build -d
```

- API: http://localhost:8000/docs
- n8n: http://localhost:5678 (crie a conta de administrador no primeiro acesso)

**Importar o fluxo no n8n**
1. No n8n: **Workflows → ⋯ / Import from file** e selecione `n8n/workflow.json`
   (dentro do container o arquivo também está em `/workflows/workflow.json`).
2. Abra o fluxo e **ative/publique** (toggle *Active* / botão *Publish*).
3. Teste:

```bash
curl -X POST http://localhost:5678/webhook/classificar-mensagem \
  -H "Content-Type: application/json" \
  -d '{"mensagem":"Fui cobrado duas vezes no cartão e quero o estorno hoje!","cliente":"Ana","canal":"email"}'
```

> Para testar **sem ativar** o fluxo, clique em *Execute workflow* no n8n e use a URL de teste: `/webhook-test/classificar-mensagem`.

Para enviar várias mensagens de exemplo de uma vez (requer `jq`):
```bash
./scripts/enviar_exemplos.sh
```

### Opção B — Sem Docker

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # preencha a chave
uvicorn app.main:app --reload --port 8000

# em outro terminal
npx n8n
```
No n8n, após importar o fluxo, edite o node **Edit Fields** e troque `api_url` de `http://api:8000` para `http://localhost:8000`.

### Variáveis de ambiente

| Variável | Descrição | Padrão |
|---|---|---|
| `LLM_PROVIDER` | `anthropic`, `openai` ou `mock` | `anthropic` |
| `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` | Chave e modelo da Anthropic | — / `claude-haiku-5-5` |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` | Provedor compatível com OpenAI | — / OpenAI / `gpt-4o-mini` |
| `LLM_TIMEOUT_SECONDS` | Timeout da chamada à IA | `30` |
| `LLM_MAX_RETRIES` | Novas tentativas se o JSON vier inválido | `1` |

> 🔒 Nunca suba o `.env` para o GitHub (já está no `.gitignore`). Só o `.env.example` é versionado.

### Testes

```bash
pip install -r requirements-dev.txt
pytest -q
```
Os testes usam o provedor `mock` e **não gastam créditos de IA**.

## 📸 Documentação visual do fluxo

Os prints do fluxo (visão geral, execução com sucesso, configuração de cada node e resultados por etapa) estão em **[docs/DOCUMENTACAO_FLUXO.md](docs/DOCUMENTACAO_FLUXO.md)**, com imagens em `docs/prints/`.

## Possíveis evoluções

- Enviar a mensagem classificada para Slack/e-mail/Google Sheets do setor responsável
- Registrar o histórico de classificações em banco de dados
- Fila para processar grandes volumes e autenticação por chave na API
