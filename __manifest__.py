{
    "name": "Sale: Enviar por WhatsApp (WAHA Plus)",
    # MUDANÇA: Versão atualizada para 16.0
    "version": "16.0.1.0.0",
    "summary": "Botão no Pedido de Venda para enviar PDF via WAHA Plus",
    "author": "Você",
    "license": "LGPL-3",
    "depends": [
        "base",
        "base_setup",
        "sale_management",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_views.xml",
        "views/whatsapp_wizard_views.xml",
        "views/res_config_settings_view.xml",
        # O arquivo de dados pode ser mantido ou removido dependendo da sua estratégia
        # "data/params.xml", # Se você gerencia a config via UI, pode comentar/remover
    ],
    "installable": True,
    "application": False,
}