# -*- coding: utf-8 -*-
import os
import requests
from requests import exceptions as req_exc

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Toggle visual (opcional)
    waha_enabled = fields.Boolean(string="WhatsApp (WAHA Plus)")

    # Parâmetros salvos em ir.config_parameter
    waha_base_url = fields.Char(
        string="Base URL",
        config_parameter="waha.base_url",
        help="Ex.: http://10.1.100.10:4000",
    )
    waha_api_key = fields.Char(
        string="API Key",
        config_parameter="waha.api_key",
        help="Chave de acesso do WAHA Plus",
    )
    waha_session = fields.Char(
        string="Sessão",
        default="default",
        config_parameter="waha.session",
        help="ID da sessão no WAHA (ex.: workwise)",
    )
    waha_timeout = fields.Integer(
        string="Timeout (s)",
        default=60,
        config_parameter="waha.timeout",
        help="Tempo máximo de espera para as chamadas ao WAHA",
    )
    waha_file_transport = fields.Selection(
        selection=[("data", "Base64 (file.data)"), ("url", "URL (file.url)")],
        string="Transporte de Arquivo",
        default="data",
        config_parameter="waha.file_transport",
        help="Informativo; o envio atual usa Base64 (file.data).",
    )

    def action_test_waha(self):
        """Botão 'Testar conexão' na tela de Definições."""
        self.ensure_one()
        ICP = self.env["ir.config_parameter"].sudo()

        base = self.waha_base_url or ICP.get_param("waha.base_url") or os.getenv("WAHA_URL", "")
        api_key = self.waha_api_key or ICP.get_param("waha.api_key") or os.getenv("WAHA_API_KEY", "")
        session = self.waha_session or ICP.get_param("waha.session") or os.getenv("WAHA_SESSION_ID", "default")
        timeout = int(self.waha_timeout or ICP.get_param("waha.timeout") or os.getenv("WAHA_TIMEOUT", "60") or 60)

        if not base:
            raise UserError(_("Informe a Base URL do WAHA."))

        url = f"{base.rstrip('/')}/api/sessions"
        headers = {"X-Api-Key": api_key} if api_key else {}
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            r.raise_for_status()
            data = r.json()
        except (req_exc.ConnectionError, req_exc.Timeout) as e:
            # Notificação de erro
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("WAHA"),
                    "message": _("Não foi possível conectar em %s (timeout=%ss).") % (base, timeout),
                    "type": "danger",
                    "sticky": False,
                },
            }
        except req_exc.RequestException as e:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("WAHA"),
                    "message": _("Falha HTTP ao chamar WAHA: %s") % (str(e),),
                    "type": "danger",
                    "sticky": False,
                },
            }

        # Sucesso
        sample = ", ".join(s.get("id", "?") for s in (data if isinstance(data, list) else [])) or "-"
        msg = _("Conexão OK.\nSessão configurada: %s\nSessões existentes (amostra): %s") % (session, sample)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("WAHA"),
                "message": msg,
                "type": "success",
                "sticky": False,
            },
        }
