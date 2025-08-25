# Dockerfile (Versão Final Corrigida)

# Use a imagem oficial do Odoo 16 como base
FROM odoo:16.0

# Mude para o usuário root para poder instalar pacotes
USER root

# Instala as versões corretas dos pacotes para evitar erros no Odoo 16
RUN pip install werkzeug==2.2.2 Jinja2==3.0.3 MarkupSafe==2.1.1

# Copia o script de entrada para a imagem e dá permissão de execução
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Define o script como o ponto de entrada
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Define o comando padrão a ser executado pelo entrypoint
CMD ["odoo"]

# Volte para o usuário padrão do Odoo por segurança
USER odoo