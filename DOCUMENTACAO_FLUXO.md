# Documentação visual do fluxo n8n

Fluxo exportado em [`../n8n/workflow.json`](../n8n/workflow.json).
As imagens ficam na pasta `docs/prints/` (use exatamente estes nomes ou ajuste os links abaixo).

## 1. Fluxo completo
Todos os nodes conectados: Webhook → Edit Fields → HTTP Request → Switch → Encaminhar (5 filas) → Respond to Webhook.

![Fluxo completo](prints/01-fluxo-completo.png)

## 2. Execução bem-sucedida
Execução concluída com sucesso (todos os nodes em verde) a partir de uma mensagem de teste.

![Execução bem-sucedida](prints/02-execucao-sucesso.png)

## 3. Configuração dos nodes

### 3.1 Webhook
Recebe `POST` em `/webhook/classificar-mensagem`; a resposta é devolvida pelo node *Respond to Webhook*.

![Webhook](prints/03-node-webhook.png)

### 3.2 Edit Fields
Padroniza `mensagem`, `cliente`, `canal` e define `api_url` (endereço da API).

![Edit Fields](prints/04-node-edit-fields.png)

### 3.3 HTTP Request - API FastAPI
`POST {api_url}/classify` com o corpo JSON (mensagem, cliente, canal). Tenta 2 vezes em caso de falha.

![HTTP Request](prints/05-node-http-request.png)

### 3.4 Switch - Categoria
Direciona o item conforme `categoria` retornada pela IA (dúvida, reclamação, solicitação, elogio; o restante vai para "Outros").

![Switch](prints/06-node-switch.png)

### 3.5 Encaminhar (Edit Fields por categoria)
Define `fila_destino`, `status` e `alerta_urgente` (verdadeiro quando prioridade é alta ou urgente).

![Encaminhar](prints/07-node-encaminhar.png)

### 3.6 Respond to Webhook
Devolve o resultado final em JSON ao solicitante.

![Respond to Webhook](prints/08-node-respond.png)

## 4. Resultados por etapa

| Etapa | O que mostra | Print |
|---|---|---|
| Webhook (saída) | Corpo recebido | ![](prints/09-saida-webhook.png) |
| HTTP Request (saída) | JSON classificado pela IA | ![](prints/10-saida-http-request.png) |
| Switch (saída) | Ramo escolhido pela categoria | ![](prints/11-saida-switch.png) |
| Encaminhar (saída) | `fila_destino`, `status`, `alerta_urgente` | ![](prints/12-saida-encaminhar.png) |
| Resposta final (curl/Postman) | JSON devolvido ao cliente | ![](prints/13-resposta-final.png) |
