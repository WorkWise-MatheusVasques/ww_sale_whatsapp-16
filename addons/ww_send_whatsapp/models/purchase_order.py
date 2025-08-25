from odoo import models, _

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def action_open_whatsapp_wizard(self):
        self.ensure_one()
        return {
            "name": _("Enviar por WhatsApp"),
            "type": "ir.actions.act_window",
            "res_model": "ww.whatsapp.compose",
            "view_mode": "form",
            "target": "new",
            "context": {
                # registro atual
                "active_model": "purchase.order",
                "active_id": self.id,
                "active_ids": [self.id],
                # defaults do wizard
                "default_res_model": "purchase.order",
                "default_res_id": self.id,
                "default_partner_id": self.partner_id.id,
                "default_phone": self.partner_id.mobile or self.partner_id.phone or "",
                "default_message": _("Olá, segue o pedido de compra %(name)s em anexo.") % {"name": self.name},
            },
        }