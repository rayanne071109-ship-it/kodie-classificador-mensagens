#!/usr/bin/env bash
# Envia as mensagens de examples/mensagens.json para o webhook do n8n.
# Uso: ./scripts/enviar_exemplos.sh [URL_DO_WEBHOOK]
# Requer: curl e jq
set -euo pipefail

URL="${1:-http://localhost:5678/webhook/classificar-mensagem}"
ARQ="$(dirname "$0")/../examples/mensagens.json"

jq -c '.[]' "$ARQ" | while read -r msg; do
  echo ">>> Enviando: $msg"
  curl -s -X POST "$URL" -H "Content-Type: application/json" -d "$msg" | jq .
  echo
done
