#!/usr/bin/env sh
set -e

# Aplica as migrações pendentes antes de iniciar a API.
# Idempotente: "alembic upgrade head" é no-op quando o banco já está no head.
# Pode ser desativado em produção com RUN_MIGRATIONS=false (ex.: quando as
# migrações são aplicadas por um job/step separado, fora do boot da API).
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "[entrypoint] Aplicando migrações alembic (upgrade head)..."
  alembic upgrade head
  echo "[entrypoint] Migrações aplicadas."
fi

exec "$@"
