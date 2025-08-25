# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class WwServiceDefinition(models.Model):
    _name = "ww.service.definition"
    _description = "Definição de Serviço WAHA"
    _order = "is_default desc, id desc"

    name = fields.Char("Nome", required=True)
    active = fields.Boolean(default=True)
    base_url = fields.Char("Base URL", required=True, help="Ex.: http://10.1.100.10:4000")
    api_key = fields.Char("API Key")
    session = fields.Char("Sessão", default="default", required=True)
    timeout = fields.Integer("Timeout (s)", default=60)
    is_default = fields.Boolean("Padrão")

    file_transport = fields.Selection(
        [("data", "Base64 (file.data)"), ("url", "URL (file.url)")],
        string="Transporte de Arquivo",
        default="data",
        help="Informativo; o módulo atual usa Base64."
    )

    _sql_constraints = [
        ("name_uniq", "unique(name)", "Já existe um serviço com esse nome."),
    ]

    @api.constrains("is_default", "active")
    def _check_single_default(self):
        for rec in self:
            if rec.is_default and rec.active:
                others = self.search([
                    ("id", "!=", rec.id),
                    ("is_default", "=", True),
                    ("active", "=", True),
                ], limit=1)
                if others:
                    raise ValidationError(_("Já existe outro serviço padrão ativo: %s") % others.name)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.is_default and rec.active:
                self.search([("id", "!=", rec.id), ("is_default", "=", True)]).write({"is_default": False})
        return records

    def write(self, vals):
        res = super().write(vals)
        if vals.get("is_default") or vals.get("active"):
            for rec in self:
                if rec.is_default and rec.active:
                    self.search([("id", "!=", rec.id), ("is_default", "=", True)]).write({"is_default": False})
        return res

    def to_cfg_dict(self):
        """Formata nos campos esperados pelo wizard."""
        return {
            "base": (self.base_url or "").rstrip("/"),
            "api_key": self.api_key or "",
            "session": self.session or "default",
            "timeout": int(self.timeout or 60),
            "file_transport": self.file_transport or "data",
        }
