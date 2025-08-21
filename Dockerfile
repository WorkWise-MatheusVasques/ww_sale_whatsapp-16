# Dockerfile - Versão Final Corrigida

# Use a imagem oficial do Odoo 16 como base
FROM odoo:16.0

# Mude para o usuário root para poder instalar pacotes
USER root

# MUDANÇA: Versão da MarkupSafe corrigida para 2.1.1
RUN pip install werkzeug==2.2.2 Jinja2==3.0.3 MarkupSafe==2.1.1

# Volte para o usuário padrão do Odoo por segurança
USER odoo