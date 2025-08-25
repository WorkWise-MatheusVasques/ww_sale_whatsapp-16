#!/bin/bash
# entrypoint.sh (Versão Simplificada e Corrigida)

set -e

# Configura as variáveis do banco de dados
export HOST=${HOST:-db}
export PORT=${PORT:-5432}
export USER=${USER:-odoo}
export PASSWORD=${PASSWORD:-odoo}

# Instala os pacotes Python
echo "Instalando dependências Python de /etc/odoo/requirements.txt..."
pip install --upgrade pip
pip install -r /etc/odoo/requirements.txt

# Monta os argumentos para o Odoo
DB_ARGS=("--db_host" "$HOST" "--db_port" "$PORT" "--db_user" "$USER" "--db_password" "$PASSWORD")

# Executa o comando principal passado pelo docker-compose (neste caso, "odoo")
exec "$@" "${DB_ARGS[@]}"